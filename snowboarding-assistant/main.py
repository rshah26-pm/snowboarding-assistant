import os
from groq import Groq
from tools import tavily_search_tool

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
    
    # Create the system context
    system_context = """You are a helpful snowboarding assistant that helps users plan their season and trips.
    You have access to a web search tool that can provide current information.
    When you need current information about resorts, weather conditions, or gear reviews, use the web_search tool.
    
    You can provide advice about:
    - Resort recommendations and planning
    - Trip planning and logistics 
    - Gear recommendations and purchases
    - Clothing and accessories advice
    - General snowboarding questions
    
    Users may provide:
    - Lists of resorts they want to visit
    - Planned trips they want to take
    - Gear they're considering buying
    - Clothing items they need
    - Accessories they're interested in
    
    Help them make informed decisions about their snowboarding season planning.
    Focus on being practical and specific in your recommendations.
    
    Format your responses in a clear, readable way.
    If you use web search results, integrate them naturally into your response and Provide a list of links from web search that you used as part of your response (only if you used the web search tool).
    """
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
    print(f"Performing web search? {needs_search}")
    search_results = ""
    if needs_search:
        print(f"Performing web search with query: {search_query}")
        search_results = tavily_search_tool.run(search_query)
        print(f"Search results in main.py: {search_results}")
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