import os
from groq import Groq
import streamlit as st
from tools import location_tool, tavily_search_tool
from dotenv import load_dotenv
from config import GROQ_API_KEY  # Import API keys
import logging

# Set up logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_snowboard_assistant_response(user_prompt):
    """
    Get a response from the AI snowboarding assistant using Groq.
    
    Args:
        user_prompt (str): The user's question or request
        
    Returns:
        str: The AI assistant's response
    """
    try:
        # Load environment variables from .env file
        load_dotenv()

        # Function to get API keys
        def get_api_key(key_name):
            # First try to get from Streamlit secrets
            if key_name in st.secrets:
                logger.info(f"Using {key_name} from Streamlit secrets")
                return st.secrets[key_name]
            # Then try to get from environment variables
            elif key_name in os.environ:
                logger.info(f"Using {key_name} from environment variables")
                return os.environ[key_name]
            else:
                logger.warning(f"{key_name} not found in secrets or environment variables")
                return None

        # Initialize Groq client
        groq_client = Groq(api_key=GROQ_API_KEY)
        
        # Create the base system context
        system_context = """You are a helpful snowboarding assistant that helps users plan their season and trips.
        You have access to two tools:
        1. A web search tool for current information about snowboarding resorts, conditions, and gear
        2. A location tool that provides distances to major ski resorts
        
        When making resort recommendations or helping with trip planning:
        - If the user has shared their location, use the get_location_info tool to find nearby resorts
        - Consider travel distance when making recommendations
        - Use the web_search tool for current conditions and resort information
        
        Always prioritize resorts that are closer to the user's location when they ask about nearby options.
        """

        # Add location context if available
        if st.session_state.get('user_location'):
            # Get location info directly from session state
            location_data = st.session_state.user_location
            lat, lon = location_data['coordinates']
            address = location_data['address']
            
            # Run the location tool to get distances
            location_info = location_tool.run("")
            
            # Add location context to system prompt
            system_context += f"\nUser's current location: {address} (Coordinates: {lat}, {lon})\n"
            system_context += f"\nLocation details:\n{location_info}\n"
            system_context += "\nUse this location information when making recommendations about nearby resorts."
            
            print(f"Location data provided to AI: {address}")
        else:
            system_context += "\nThe user has not shared their location. If they ask about nearby resorts, suggest they enable location sharing for personalized recommendations."
            print("No location data available for AI")

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
                    "content": """First determine if this query requires current information from web search.  This could be because of the need for factual current information like weather, conditions, prices, etc
                    If NO, respond with just 'NO'.
                    If YES, respond with 'YES:' followed by a search query optimized to find the specific real-time information needed.
                    Keep the search query concise and specific, and use a simple sentence with no special characters or formatting. Keep it less than 200 characters.
                    Focus the search query on factual current information like weather, conditions, prices, etc.
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
        if needs_search:
            search_results = tavily_search_tool.run(search_query)

        # Create the final response
        messages = [
            {
                "role": "system",
                "content": system_context
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]

        # Add search results if available
        if search_results:
            messages.append({
                "role": "system",
                "content": f"Web search results:\n{search_results}\nUse this information in your response when relevant."
            })
        
        chat_completion = groq_client.chat.completions.create(
            messages=messages,
            model="llama3-8b-8192",
            temperature=0.7
        )
        
        return chat_completion.choices[0].message.content
    except Exception as e:
        error_message = f"Error getting response: {str(e)}"
        print(f"Error: {error_message}")
        return f"Sorry, I encountered an error: {error_message}. Please try again later."