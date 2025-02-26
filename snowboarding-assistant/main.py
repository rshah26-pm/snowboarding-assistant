import os
from groq import Groq
import streamlit as st
from tools import location_tool, tavily_search_tool  # Import both tools

def get_snowboard_assistant_response(user_prompt):
    """
    Get a response from the AI snowboarding assistant using Groq.
    
    Args:
        user_prompt (str): The user's question or request
        
    Returns:
        str: The AI assistant's response
    """
    # Initialize Groq client
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    
    # Create the base system context
    system_context = """You are a helpful snowboarding assistant that helps users plan their season and trips.
    You have access to two tools:
    1. A web search tool for current information
    2. A location tool that provides distances to major ski resorts
    
    When making resort recommendations or helping with trip planning:
    - Always check the user's location first using the get_location_info tool
    - Consider travel distance when making recommendations
    - Use the web_search tool for current conditions (such as weather, conditions, prices, etc) and resort information
    """

    # Add location context if available
    if st.session_state.get('user_location'):
        location_info = location_tool.run("")  # Get current location info
        system_context += f"\nUser's current location information:\n{location_info}\n"
        system_context += "\nConsider this location information when making recommendations."

    # First, determine if we need web search and get optimized search query
    planning_message = client.chat.completions.create(
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
    
    chat_completion = client.chat.completions.create(
        messages=messages,
        model="llama3-8b-8192",
        temperature=0.7
    )
    
    return chat_completion.choices[0].message.content