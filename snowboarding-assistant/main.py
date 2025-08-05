import os
from groq import Groq
import streamlit as st
from tools import resort_distance_calculator, tavily_search_tool
from dotenv import load_dotenv
from config import GROQ_API_KEY, check_tavily_usage  # Import API keys and check_tavily_usage function
import logging
import json
from prompts import get_prompt  # <-- NEW: import the prompt loader

# Set up logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_snowboard_assistant_response(user_prompt, conversation_history=None):
    """
    Get a response from the AI snowboarding assistant using Groq.
    
    Args:
        user_prompt (str): The user's question or request
        conversation_history (list, optional): Previous messages in the conversation
        
    Returns:
        str: The AI assistant's response
    """
    try:
        # --- PROMPT VERSION CONTROL ---
        RESPONSE_PROMPT_VERSION = "v1"  # Change to 'v2' for A/B testing
        INTENT_PROMPT_VERSION = "v1"    # Change to 'v2' for A/B testing

        # Initialize search tracking variables
        search_links = []
        search_used = False
        load_dotenv()

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
        groq_client = Groq(api_key=GROQ_API_KEY)

        # --- SYSTEM PROMPT (RESPONSE GENERATION) ---
        system_context = get_prompt("response_generation", RESPONSE_PROMPT_VERSION)

        # Add location context if available
        if st.session_state.get('user_location'):
            # Get location info directly from session state
            location_data = st.session_state.user_location
            lat, lon = location_data['coordinates']
            address = location_data['address']
            
            # Run the location tool to get distances
            location_info = resort_distance_calculator.run("")
            
            # Add location context to system prompt
            system_context += f"\nUser's current location: {address} (Coordinates: {lat}, {lon})\n"
            system_context += f"\nLocation details:\n{location_info}\n"
            system_context += "\nUse this location information when making recommendations about nearby resorts."
            
            logger.info(f"Location data provided to AI: {address}")
        else:
            system_context += "\nThe user has not shared their location. If they ask about nearby resorts, suggest they enable location sharing for personalized recommendations."

        # Check if the user is asking about location-based recommendations
        location_keywords = ["near me", "nearby", "closest", "nearest", "my location", "my area", "distance", "how far"]
        is_location_query = any(keyword in user_prompt.lower() for keyword in location_keywords)
        if is_location_query and not st.session_state.get('user_location'):
            system_context += "\nThe user is asking about location-based recommendations, but they haven't shared their location. Make sure to suggest they enable location sharing."

        # --- INTENT CLASSIFIER PROMPT ---
        intent_classifier_prompt = get_prompt("intent_classifier", INTENT_PROMPT_VERSION)
        planning_message = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": intent_classifier_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            model="llama-3.1-8b-instant",
            temperature=0.1
        )

        response = planning_message.choices[0].message.content.strip()
        needs_search = response.upper().startswith("YES")
        
        # Extract optimized search query if search is needed
        search_query = user_prompt
        if needs_search and ":" in response:
            search_query = response.split(":", 1)[1].strip()
     
        # If needed, perform web search
        search_results = ""
        search_links = []
        if needs_search:
            logger.info(f"Web search needed for query: '{search_query}'")
            # Check if we've exceeded the Tavily usage limit
            usage_count, limit_exceeded = check_tavily_usage()
            
            if limit_exceeded:
                logger.info("Tavily usage limit exceeded, skipping web search")
                search_results = "Web search is currently unavailable as we've reached our monthly limit of 600 requests. " \
                                 "I'll answer based on my existing knowledge."
                system_context += "\nNOTE: Web search functionality is currently unavailable due to reaching the monthly request limit. " \
                                  "Please provide answers based on your existing knowledge only."
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

        # Create the final response
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
            for message in conversation_history[-8:]:
                if message["role"] in ["user", "assistant"]:
                    history_to_include.append({
                        "role": message["role"],
                        "content": message["content"]
                    })
            messages.extend(history_to_include)
        else:
            # If no history, just add the current prompt
            messages.append({
                "role": "user",
                "content": user_prompt
            })
        
        # Add search results if available but don't ask the model to format sources
        if search_results:
            logger.info("Adding search results to the prompt")
            formatted_links = ""
            if search_links:
                formatted_links = "\n\nRelevant sources:\n"
                for i, link in enumerate(search_links[:5]):  # Limit to 5 sources
                    formatted_links += f"{i+1}. {link}\n"
            
            messages.append({
                "role": "system",
                "content": f"""Web search results:\n{search_results}\n{formatted_links}\n\nUse this information in your response when relevant. DO NOT include links in your response. DO NOT include a Sources section at the end of your response.\n"""
            })
            search_used = True
            logger.info("Search was used to gather additional information for the response.")

        if not (messages[-1]["role"] == "user" and messages[-1]["content"] == user_prompt):
            messages.append({
                "role": "user",
                "content": user_prompt
            })

        logger.info("Sending request to Groq API")
        chat_completion = groq_client.chat.completions.create(
            messages=messages,
            model="llama-3.1-8b-instant",
            temperature=0.7
        )
        response = chat_completion.choices[0].message.content
        logger.info("Received response from Groq API")

        google_url = None
        if search_links and search_used:
            logger.info("Deterministically appending sources to response")
            if "Sources:" in response:
                logger.info("Removing existing Sources section from response")
                response = response.split("Sources:")[0].strip()
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