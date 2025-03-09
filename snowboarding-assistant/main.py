import os
from groq import Groq
import streamlit as st
from tools import resort_distance_calculator, tavily_search_tool
from dotenv import load_dotenv
from config import GROQ_API_KEY, check_tavily_usage  # Import API keys and check_tavily_usage function
import logging
import json

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
        # Initialize search tracking variables
        search_links = []
        search_used = False
        
        # Load environment variables from .env file
        load_dotenv()

        # Function to get API keys
        def get_api_key(key_name):
            # First try to get from Streamlit secrets
            if key_name in st.secrets:
                return st.secrets[key_name]
            # Then try to get from environment variables
            elif key_name in os.environ:
                return os.environ[key_name]
            else:
                logger.warning(f"{key_name} not found in secrets or environment variables")
                return None

        # Initialize Groq client
        groq_client = Groq(api_key=GROQ_API_KEY)
        
        # Create the base system context
        system_context = """You are a helpful and enthusiastic snowboarding assistant that helps users plan their season and trips.
        You have access to two tools:
        1. A web search tool for current information about snowboarding resorts, conditions, and gear
        2. A location tool that provides distances to major ski resorts
        
        When making resort recommendations or helping with trip planning:
        - If the user has shared their location, use the get_location_info tool to find nearby resorts
        - Consider travel distance when making recommendations
        - Use the web_search tool for current conditions and resort information
        
        Always prioritize resorts that are closer to the user's location when they ask about nearby options.
        
        IMPORTANT: When users ask about nearby resorts or location-based recommendations but haven't shared their location, 
        explicitly tell them to "check the sidebar and enable location sharing by clicking the checkbox labeled 
        '📍 Share my location'". Make it clear that the sidebar can be 
        accessed by clicking the expand arrow in the top-left corner of the screen.

        Never make the user feel pressured to share their location.
        
        STYLE GUIDE: Use snowboarder lingo and casual language to make your responses fun and engaging. Sprinkle in phrases like:
        - "Shred the gnar" (to snowboard aggressively on challenging terrain)
        - "Fresh pow" (fresh powder snow)
        - "Stoked" (excited)
        - "Sick" or "Rad" (awesome, cool)
        - "Sending it" (going for it, taking risks)
        - "Carving" (making clean turns)
        - "Catching air" (jumping)
        - "Bombing" (going downhill fast)
        - "Jibbing" (tricks on non-snow features)
        - "Park rat" (someone who spends time in terrain parks)
        
        Keep your tone enthusiastic but not over-the-top. Use these terms naturally where they fit, not in every response. Don't use the term "dude" when referring to the user. 
        Be knowledgeable but approachable, like a friend who loves snowboarding and wants to share their passion.
        
        IMPORTANT: Remember the conversation history and maintain context between messages. Refer back to previous questions and answers when relevant.
        """

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
        
        # If it's a location query but we don't have location data, add a note
        if is_location_query and not st.session_state.get('user_location'):
            system_context += "\nThe user is asking about location-based recommendations, but they haven't shared their location. Make sure to suggest they enable location sharing."

        # First, determine if we need web search and get optimized search query
        planning_message = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system", 
                    "content": """You can leverage the web search tool to find current information like weather conditions, ongoing sales/deals/prices for cheap equipment, etc. This is very important in terms of ensuring you are providing the most accurate and up-to-date and valuable information to the user. So use it pro-actively, for example, if you see the word "cheap" in the user's query, you should use the web search tool to find the best deals. If you see the word "weather" in the user's query, you should use the web search tool to find the current weather conditions.
                    If you determine the user's query does not require web search, respond with just 'NO'.
                    If you determine the user's query does equire web search, respond with 'YES:' followed by a search query optimized for a search engine to retrieve the specific information needed. We want to be as specific as possible.
                    Keep the search query concise and specific, and use a simple sentence with no special characters or formatting. Keep it less than 200 characters.
                    """
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            model="llama3-8b-8192",
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
        search_links = []  # New list to store search result links
        
        if needs_search:
            logger.info(f"Web search needed for query: '{search_query}'")
            # Check if we've exceeded the Tavily usage limit
            usage_count, limit_exceeded = check_tavily_usage()
            
            if limit_exceeded:
                logger.info("Tavily usage limit exceeded, skipping web search")
                search_results = "Web search is currently unavailable as we've reached our monthly limit of 600 requests. " \
                                 "I'll answer based on my existing knowledge."
                # Also add this to the system context
                system_context += "\nNOTE: Web search functionality is currently unavailable due to reaching the monthly request limit. " \
                                  "Please provide answers based on your existing knowledge only."
            else:
                logger.info(f"Performing Tavily search with query: '{search_query}'")
                # Get the raw search results
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
            # Log the conversation history for debugging
            logger.info(f"Adding conversation history with {len(conversation_history)} messages")
            
            # Only include the last few messages to stay within token limits
            # Skip system messages and only include user and assistant messages
            history_to_include = []
            for message in conversation_history[-8:]:  # Include up to 8 recent messages (4 exchanges)
                if message["role"] in ["user", "assistant"]:
                    history_to_include.append({
                        "role": message["role"],
                        "content": message["content"]
                    })
            
            # Add the filtered history to messages
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
            # Format the links in a way that's easy for the model to use
            formatted_links = ""
            if search_links:
                formatted_links = "\n\nRelevant sources:\n"
                for i, link in enumerate(search_links[:5]):  # Limit to 5 sources
                    formatted_links += f"{i+1}. {link}\n"
            
            # Modify the system message to instruct the model to use search results
            # but NOT to include sources (we'll handle that ourselves)
            messages.append({
                "role": "system",
                "content": f"""Web search results:
{search_results}
{formatted_links}

Use this information in your response when relevant. DO NOT include links in your response. DO NOT include a Sources section at the end of your response.
"""
            })
            
            # Set flag to indicate search was used
            search_used = True
            logger.info("Search was used to gather additional information for the response.")
        
        # Make sure the current prompt is included as the last user message
        if not (messages[-1]["role"] == "user" and messages[-1]["content"] == user_prompt):
            messages.append({
                "role": "user",
                "content": user_prompt
            })
        
        logger.info("Sending request to Groq API")
        chat_completion = groq_client.chat.completions.create(
            messages=messages,
            model="llama3-8b-8192",
            temperature=0.7
        )
        
        response = chat_completion.choices[0].message.content
        logger.info("Received response from Groq API")        
        
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