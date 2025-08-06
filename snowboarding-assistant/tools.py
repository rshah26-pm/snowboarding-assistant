from langchain.tools import Tool
import logging  # Import the logging module
import requests
import re
from web_search_tool import tavily_search_tool
from geolocation_tool import resort_distance_calculator

# Configure the logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)  # Create a logger instance

# Make sure both tools are available for use
tools = [
    tavily_search_tool,
    resort_distance_calculator
] 