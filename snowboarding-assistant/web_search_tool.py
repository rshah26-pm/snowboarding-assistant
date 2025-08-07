from langchain.tools import Tool
from tavily import TavilyClient
import os
import streamlit as st
from config import TAVILY_API_KEY, check_tavily_usage
from prompts import get_prompt
import logging

# Configure the logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
        message = get_prompt("web_search_unavailable", "v1")
        
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