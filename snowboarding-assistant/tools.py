from langchain.tools import Tool
from tavily import TavilyClient
import os
import streamlit as st
from geopy.distance import geodesic

tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

def web_search(query: str) -> str:
    """
    Search the web for snowboarding-related information.
    
    Args:
        query (str): The search query
        
    Returns:
        str: Search results summary
    """
    print(f"🔧 Using tool: web_search with query: {query}")  # Log tool usage
    
    search_results = tavily.search(
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

def get_user_location(query: str = "") -> str:
    """Get user's location and return relevant information for snowboarding recommendations."""
    print(f"🔧 Using tool: get_location_info")  # Log tool usage
    
    if 'user_location' not in st.session_state or not st.session_state.user_location:
        return "Location access not granted. Please select your location for personalized resort recommendations."
    
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
        
        distances = []
        for resort, coords in ski_resorts.items():
            distance = geodesic(location_data['coordinates'], coords).miles
            distances.append(f"{resort}: {int(distance)} miles")
        
        formatted_distances = "\n- ".join(distances)
        
        return f"""Current location: {address}
        
Distances to major resorts:
- {formatted_distances}

This information can help identify the most convenient resorts for your trip."""

    except Exception as e:
        return f"Error processing location data: {str(e)}"

# Add this after your get_user_location() function
location_tool = Tool(
    name="get_location_info",
    description="""Use this tool when you need to consider the user's location for resort recommendations, 
    trip planning, or travel logistics. It provides the user's location and distances to major ski resorts. 
    Only use this when the user's query involves location-based recommendations, distance considerations, 
    or travel planning. The tool returns distances to resorts like Heavenly, Northstar, Palisades Tahoe, 
    Kirkwood, Mammoth, Vail, Breckenridge, and Park City.""",
    func=get_user_location
)

# Make sure both tools are available for use
tools = [
    tavily_search_tool,
    location_tool
] 