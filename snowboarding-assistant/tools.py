from langchain.tools import Tool
from tavily import TavilyClient
import os
import streamlit as st
from geopy.distance import geodesic
from config import TAVILY_API_KEY, check_tavily_usage

def web_search(query: str) -> str:
    """
    Search the web for snowboarding-related information.
    
    Args:
        query (str): The search query
        
    Returns:
        str: Search results summary
    """
    print(f"🔧 Using tool: web_search with query: {query}")  # Log tool usage
    
    # Check if we've exceeded the Tavily usage limit
    usage_count, limit_exceeded = check_tavily_usage()
    
    if limit_exceeded:
        return "I'm sorry, but we've reached our monthly limit for web searches. " \
               "I'll try to answer based on my existing knowledge, but I can't " \
               "search for the latest information at this time."
    
    # Increment the usage count in anticipation of this request
    st.session_state.tavily_usage_count += 1
    
    tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
    search_results = tavily_client.search(
        query=query,
        search_depth="basic",
        max_results=3
    )
    
    # Format results into a readable summary
    summary = []
    for result in search_results['results']:  # search_results is a list of dictionaries
        if isinstance(result, dict):  # verify it's a dictionary
            title = result.get('title', 'No title')
            content = result.get('content', 'No content')
            url = result.get('url', 'No URL')
            summary.append(f"- {title}\nURL: {url}\nSummary: {content}\n")
   
    return "\n".join(summary) if summary else "No results found."

# Define the tool
tavily_search_tool = Tool(
    name="web_search",
    description="Useful for searching current information about snowboarding resorts, conditions, gear reviews, and related topics.",
    func=web_search
)

def get_user_to_resort_distance(query: str = "") -> str:
    """Get user's location and return relevant information for snowboarding recommendations."""
    print(f"🔧 Using tool: resort_distance_calculator")  # Log tool usage
    
    if 'user_location' not in st.session_state or not st.session_state.user_location:
        return "Location access not granted. Please enable location sharing for personalized resort recommendations."
    
    location_data = st.session_state.user_location
    try:
        lat, lon = location_data['coordinates']
        address = location_data['address']
        
        # Calculate distances to major resorts
        ski_resorts = {
            'Heavenly': (38.9353, -119.9400),
            'Northstar': (39.2746, -120.1211),
            'Palisades Tahoe': (39.1967, -120.2356),
            'Kirkwood': (38.6850, -120.0654),
            'Mammoth': (37.6308, -119.0326),
            'Vail': (39.6433, -106.3781),
            'Breckenridge': (39.4817, -106.0384),
            'Park City': (40.6461, -111.4980)
        }
        
        # Find closest resorts
        resort_distances = []
        for resort, coords in ski_resorts.items():
            distance = geodesic(location_data['coordinates'], coords).miles
            resort_distances.append((resort, distance))
        
        # Sort by distance
        resort_distances.sort(key=lambda x: x[1])
        
        # Format distances
        formatted_distances = "\n- ".join([f"{resort}: {int(distance)} miles" for resort, distance in resort_distances])
        
        return f"""Current location: {address}
        
Distances to major resorts:
- {formatted_distances}

The closest resorts to your location are {resort_distances[0][0]} ({int(resort_distances[0][1])} miles) and {resort_distances[1][0]} ({int(resort_distances[1][1])} miles).
"""

    except Exception as e:
        return f"Error processing location data: {str(e)}"

resort_distance_calculator = Tool(
    name="resort_distance_calculator",
    description="""Use this tool to calculate distances from the user's location to nearby snowboarding resorts. 
    It provides the user's location and distances to major ski resorts. 
    Only use this when the user's query involves location-based recommendations, distance considerations, 
    or travel planning. The tool returns distances to resorts like Heavenly, Northstar, Palisades Tahoe, 
    Kirkwood, Mammoth, Vail, Breckenridge, and Park City.""",
    func=get_user_to_resort_distance
)

# Make sure both tools are available for use
tools = [
    tavily_search_tool,
    resort_distance_calculator  # Updated tool name
] 