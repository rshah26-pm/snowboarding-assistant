from langchain.tools import Tool
from tavily import TavilyClient
import os

tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

def web_search(query: str) -> str:
    """
    Search the web for snowboarding-related information.
    
    Args:
        query (str): The search query
        
    Returns:
        str: Search results summary
    """
    search_results = tavily.search(
        query=query,
        search_depth="basic",
        max_results=3
    )

    print(f"Search results: {search_results}\n\n")
    
    # Format results into a readable summary
    summary = []
    for result in search_results['results']:  # search_results is a list of dictionaries
        print(f"Result: {result}")
        if isinstance(result, dict):  # verify it's a dictionary
            title = result.get('title', 'No title')
            content = result.get('content', 'No content')
            url = result.get('url', 'No URL')
            print(f"Title: {title}")
            print(f"URL: {url}")
            summary.append(f"- {title}\nURL: {url}\nSummary: {content}\n")
    print(f"Summary: {summary}")
   
    return "\n".join(summary) if summary else "No results found."

# Define the tool
tavily_search_tool = Tool(
    name="web_search",
    description="Useful for searching current information about snowboarding resorts, conditions, gear reviews, and related topics.",
    func=web_search
) 