from langchain.tools import Tool
from tavily import TavilyClient
import os
import streamlit as st
from geopy.distance import geodesic
from config import TAVILY_API_KEY, check_tavily_usage
import logging  # Import the logging module
import requests
import re
from resort_database import get_closest_resorts

# Configure the logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)  # Create a logger instance

def web_search(query: str, return_links: bool = False) -> str:
    """
    Search the web for snowboarding-related information.
    
    Args:
        query (str): The search query
        return_links (bool): Whether to return links separately
        
    Returns:
        str or dict: Search results summary, or dict with content and links if return_links=True
    """
    print(f"🔧 Using tool: web_search with query: {query}")  # Log tool usage
    
    # Check if we've exceeded the Tavily usage limit
    usage_count, limit_exceeded = check_tavily_usage()
    
    if limit_exceeded:
        message = "I'm sorry, but we've reached our monthly limit for web searches. " \
               "I'll try to answer based on my existing knowledge, but I can't " \
               "search for the latest information at this time."
        
        return {"content": message, "links": []} if return_links else message
    
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
    links = []  # Store links separately
    
    for result in search_results['results']:  # search_results is a list of dictionaries
        if isinstance(result, dict):  # verify it's a dictionary
            title = result.get('title', 'No title')
            url = result.get('url', 'No URL')
            content = result.get('content', 'No content')
            
            # Add to summary
            summary.append(f"- {title}\nURL: {url}\nSummary: {content}\n")
            
            # Add to links list
            if url and url not in links:
                links.append(url)

    formatted_summary = "\n".join(summary) if summary else "No results found."

    logger.info(f"Links returned from Tavily search: {links}")
    
    # Return either just the summary or both summary and links
    if return_links:
        return {
            "content": formatted_summary,
            "links": links
        }
    else:
        return formatted_summary

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
        
        # Get closest resorts from the database
        closest_resorts = get_closest_resorts(lat, lon, query, limit=5)
        
        if not closest_resorts:
            return f"I couldn't find any ski resorts matching your criteria near {address}."
        
        # Format distances for the 5 closest resorts
        formatted_distances = "\n- ".join([
            f"{resort['name']}: {resort['distance']} miles" + 
            (f" ({resort['region']}, {resort['state']})" if 'region' in resort and 'state' in resort else "")
            for resort in closest_resorts
        ])
        
        # Get the two closest for the summary line
        closest_two = closest_resorts[:2]
        
        return f"""Current location: {address}
        
The 5 closest ski resorts to your location:
- {formatted_distances}

The closest resorts to your location are {closest_two[0]['name']} ({closest_two[0]['distance']} miles) and {closest_two[1]['name']} ({closest_two[1]['distance']} miles).
"""

    except Exception as e:
        logger.error(f"Error in get_user_to_resort_distance: {str(e)}")
        return f"Error processing location data: {str(e)}"

resort_distance_calculator = Tool(
    name="resort_distance_calculator",
    description="""Use this tool to calculate distances from the user's location to nearby snowboarding resorts. 
    It provides the user's location and distances to the 5 closest ski resorts.
    Only use this when the user's query involves location-based recommendations, distance considerations, 
    or travel planning. The tool returns distances to the closest ski resorts based on the user's current location.""",
    func=get_user_to_resort_distance
)

# Make sure both tools are available for use
tools = [
    tavily_search_tool,
    resort_distance_calculator  # Updated tool name
] 