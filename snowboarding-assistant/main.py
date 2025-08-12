import os
from groq import Groq
import streamlit as st
from geolocation_tool import resort_distance_calculator
from web_search_tool import tavily_search_tool
from dotenv import load_dotenv
from config import (
    GROQ_API_KEY,
    check_tavily_usage,
    ACTION_CLASSIFIER_MODEL,
    RESPONSE_GENERATION_MODEL
)
import logging
import json
from prompts import get_prompt
import time
import requests
from action_classifier import classify_actions

# Set up logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_groq_request(messages, model, temperature=0.7):
    """
    Validate the Groq API request before sending
    """
    # Check if messages are properly formatted
    if not messages or not isinstance(messages, list):
        raise ValueError("Messages must be a non-empty list")
    
    for message in messages:
        if not isinstance(message, dict):
            raise ValueError("Each message must be a dictionary")
        if 'role' not in message or 'content' not in message:
            raise ValueError("Each message must have 'role' and 'content' keys")
        if message['role'] not in ['system', 'user', 'assistant']:
            raise ValueError("Message role must be 'system', 'user', or 'assistant'")
        if not isinstance(message['content'], str):
            raise ValueError("Message content must be a string")
    
    # Check model name
    if not model or not isinstance(model, str):
        raise ValueError("Model must be a non-empty string")
    
    # Check temperature
    if not isinstance(temperature, (int, float)) or temperature < 0 or temperature > 2:
        raise ValueError("Temperature must be a number between 0 and 2")
    
    # Check total content length (Groq has limits)
    total_content = sum(len(msg.get('content', '')) for msg in messages)
    if total_content > 32000:  # Conservative limit
        logger.warning(f"Total content length ({total_content}) is large, may cause issues")
    
    return True

def retry_groq_request(groq_client, messages, model, temperature=0.7, max_retries=3):
    """
    Retry Groq API request with exponential backoff
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting Groq API request (attempt {attempt + 1}/{max_retries})")
            
            # Validate request before sending
            validate_groq_request(messages, model, temperature)
            
            # Add small delay between retries
            if attempt > 0:
                time.sleep(2 ** attempt)  # Exponential backoff: 2, 4, 8 seconds
            
            response = groq_client.chat.completions.create(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=4000  # Add explicit token limit
            )
            
            logger.info("Groq API request successful")
            return response
            
        except Exception as e:
            logger.error(f"Groq API attempt {attempt + 1} failed: {str(e)}")
            
            # If it's the last attempt, raise the error
            if attempt == max_retries - 1:
                raise e
            
            # Check if it's a rate limit error
            if "rate_limit" in str(e).lower() or "429" in str(e):
                logger.warning("Rate limit detected, waiting longer before retry")
                time.sleep(10)  # Wait 10 seconds for rate limits
            elif "500" in str(e) or "internal_server_error" in str(e).lower():
                logger.warning("Internal server error detected, retrying...")
                time.sleep(5)  # Wait 5 seconds for server errors
            else:
                logger.warning(f"Unknown error type: {type(e).__name__}")
                time.sleep(2)

def geolocation_tool_adaptor(system_context, user_prompt):
        """
        Appends the appropriate location context to the system context
        using the resort_distance_calculator tool and user session state.
        Assumes the calling code has already verified the user is asking for location-based recommendations.
        """
        location_info = resort_distance_calculator.run("")
        if location_info is not None:
            location_context_template = get_prompt("location_context")
            # Format closest_resorts as a pretty string if it's a dict
            closest_resorts = location_info.get('closest_resorts')
            if isinstance(closest_resorts, dict):
                closest_resorts_str = "\n".join(
                    f"- {resort}: {distance:.1f} miles" for resort, distance in closest_resorts.items()
                )
            else:
                closest_resorts_str = str(closest_resorts)
            location_context = location_context_template.format(
                address=location_info.get('address', ''),
                closest_resorts=closest_resorts_str
            )
            system_context += "\n" + location_context
            logger.info(f"Location data provided: {location_context}")
        else:
            # Add no-location message from prompts.json
            no_location_msg = get_prompt("no_location_shared")
            system_context += "\n" + no_location_msg

        return system_context
    
def build_system_context(user_prompt):
    """
    Build the system context from prompts.json based on current state.
    """
    # Start with the base response generation prompt
    system_context = get_prompt("response_generation")    
    return system_context

def get_snowboard_assistant_response(user_prompt, conversation_history=None):
    """
    Get a response from the AI snowboarding assistant.
    
    Args:
        user_prompt (str): The user's question or request
        conversation_history (list, optional): Previous messages in the conversation
        
    Returns:
        str: The AI assistant's response
    """
    try:
        load_dotenv()

        # Initialize search tracking variables
        search_links = []
        search_used = False

        # Function to get API keys
        def get_api_key(key_name):
            if key_name in st.secrets:
                return st.secrets[key_name]
            elif key_name in os.environ:
                return os.environ[key_name]
            else:
                logger.warning(f"{key_name} not found in secrets or environment variables")
                return None

        # Initialize Groq client
        if not GROQ_API_KEY:
            error_msg = "GROQ_API_KEY not found in environment variables or Streamlit secrets"
            logger.error(error_msg)
            return f"Configuration error: {error_msg}. Please check your API key setup."
        
        logger.info(f"Initializing Groq client. action_classifier_model={ACTION_CLASSIFIER_MODEL}")
        groq_client = Groq(api_key=GROQ_API_KEY)

        system_context = build_system_context(user_prompt)

        # LLM based action classifier (to determine if we need to use a tool)
        logger.info(f"Running action classifier for user prompt")
        try:
            classification = classify_actions(
                user_prompt=user_prompt,
                groq_client=groq_client,
                model=ACTION_CLASSIFIER_MODEL,
            )
            tool_use = classification["tool_use"]
            search_query = classification["search_query"] or user_prompt
            logger.info(f"Classifier decided tool_use={tool_use} search_query='{search_query}'")
        except Exception as intent_error:
            logger.error(f"Action classifier failed: {str(intent_error)}")
            tool_use = {"search": False, "geolocation": False}
            search_query = user_prompt
     
        # If needed, perform web search
        search_results = ""
        search_links = []
        if tool_use["search"]:
            logger.info(f"Web search needed for query: '{search_query}'")
            # Check if we've exceeded the Tavily usage limit
            usage_count, limit_exceeded = check_tavily_usage()
            
            if limit_exceeded:
                logger.info("Tavily usage limit exceeded, skipping web search")
                # Use the prompt from prompts.json for the "web search unavailable" message
                search_results = get_prompt("web_search_unavailable")
            else:
                logger.info(f"Performing Tavily search with query: '{search_query}'")
                raw_results = tavily_search_tool.run(search_query, return_links=True)
                
                # Extract links from the results
                if isinstance(raw_results, dict) and 'links' in raw_results:
                    search_links = raw_results['links']
                    search_results = raw_results['content']
                    logger.info(f"Received {len(search_links)} links from Tavily search")
                    logger.info(f"Search links: {json.dumps(search_links)}")
                else:
                    # Fallback for backward compatibility
                    logger.info("Received search results in legacy format, extracting links")
                    search_results = raw_results
                    # Try to extract links from the text
                    for line in search_results.split('\n'):
                        if line.startswith('URL:'):
                            url = line.replace('URL:', '').strip()
                            if url and url not in search_links:
                                search_links.append(url)
                    logger.info(f"Extracted {len(search_links)} links from legacy format")
                    logger.info(f"Extracted links: {json.dumps(search_links)}")

        # --- BUILD MESSAGES ARRAY (FOCUSED ON CONVERSATION FLOW) ---
        messages = [
            {
                "role": "system",
                "content": system_context
            }
        ]
        
        # Add conversation history if provided
        if conversation_history:
            logger.info(f"Adding conversation history with {len(conversation_history)} messages")
            history_to_include = []
            for message in conversation_history[-8:]:  # Include up to 8 recent messages (4 exchanges)
                if message["role"] in ["user", "assistant"]:
                    history_to_include.append({
                        "role": message["role"],
                        "content": message["content"]
                    })
            messages.extend(history_to_include)

        # Add search results if available (as a separate system message)
        if search_results:
            logger.info("Adding search results to the prompt")
            formatted_links = ""
            if search_links:
                formatted_links = "\n\nRelevant sources:\n"
                for i, link in enumerate(search_links[:5]):  # Limit to 5 sources; TODO: make this a config variable
                    formatted_links += f"{i+1}. {link}\n"
            
            search_results_template = get_prompt("web_search_results")
            formatted_search_message = search_results_template.format(
                search_results=search_results,
                formatted_links=formatted_links
            )
            
            messages.append({
                "role": "system",
                "content": formatted_search_message
            })
            
            search_used = True
            logger.info("Search was used to gather additional information for the response.")
        
        # Make sure the current prompt is included as the last user message
        if not (messages[-1]["role"] == "user" and messages[-1]["content"] == user_prompt):
            messages.append({
                "role": "user",
                "content": user_prompt
            })
        
        logger.info("Sending request to Groq API")
        
        # Validate model name
        if not RESPONSE_GENERATION_MODEL:
            error_msg = "RESPONSE_GENERATION_MODEL not configured"
            logger.error(error_msg)
            return f"Configuration error: {error_msg}. Please check your model configuration."
        
        try:
            chat_completion = retry_groq_request(
                groq_client=groq_client,
                messages=messages,
                model=RESPONSE_GENERATION_MODEL,
                temperature=0.7
            )
            
            response = chat_completion.choices[0].message.content
            logger.info("Received response from Groq API")
        except Exception as api_error:
            logger.error(f"Groq API error: {str(api_error)}")
            logger.error(f"Error type: {type(api_error).__name__}")
            # Try to get more details about the error
            if hasattr(api_error, 'response'):
                logger.error(f"Response status: {api_error.response.status_code}")
                logger.error(f"Response text: {api_error.response.text}")
            raise api_error        
        
        # Check if there's a Google URL in the search links
        google_url = None

        # Deterministically append sources if search was used
        if search_links and search_used:
            logger.info("Deterministically appending sources to response")
            
            # Remove any existing sources section if present
            if "Sources:" in response:
                logger.info("Removing existing Sources section from response")
                response = response.split("Sources:")[0].strip()
            
            # Add a clean sources section
            sources_section = "\n\n**Sources:**\n"
            used_links = 0
            
            for i, url in enumerate(search_links[:5]):  # Limit to 5 sources                
                # Extract domain for more descriptive title
                try:
                    if "google.com" in url:
                        google_url = url
                        logger.info(f"Skipping Google URL: {url}")
                        continue
                    domain = url.split('//')[1].split('/')[0] if '//' in url else url
                    sources_section += f"- [{domain}]({url})\n"
                    used_links += 1
                except Exception as e:
                    logger.warning(f"Error formatting URL {url}: {str(e)}")
            
            # Only append if we have valid links
            if used_links > 0:
                response += sources_section
                logger.info(f"Added {used_links} sources to response")
            else:
                logger.info("No valid sources to add")
        else:
            logger.info("No search links available or search not used, skipping sources")
            # Append Google search query message if found
        if google_url:
            response += f"\n\nOh, and I found the following Google search query helpful in thinking through this, check it out: {google_url}"
            logger.info("Added Google search query reference to response")

        return response
    except Exception as e:
        error_message = f"Error getting response: {str(e)}"
        logger.error(f"Error: {error_message}")
        return f"Sorry, I encountered an error: {error_message}. Please try again later."