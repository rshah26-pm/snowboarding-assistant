import os
from dotenv import load_dotenv
import streamlit as st
import requests
from datetime import datetime

# Load environment variables from .env file if it exists
load_dotenv()

# Function to get API keys from either environment variables or Streamlit secrets
def get_api_key(key_name):
    env_value = os.environ.get(key_name)
    if env_value:
        print(f"Found {key_name} in environment variables")
        return env_value
    
    # First try to get from Streamlit secrets
    try:
        if key_name in st.secrets:
            print(f"Found {key_name} in Streamlit secrets")
            return st.secrets[key_name]
    except Exception as e:
        print(f"Error accessing nested secrets: {e}")
   
    print(f"WARNING: {key_name} not found in Streamlit secrets or environment variables")
    return None

# Initialize API keys
TAVILY_API_KEY = get_api_key("TAVILY_API_KEY")
GROQ_API_KEY = get_api_key("GROQ_API_KEY")

# Function to check Tavily API usage
def check_tavily_usage():
    """
    Check the current Tavily API usage for the month.
    Returns:
        tuple: (usage_count, is_limit_exceeded)
    """
    # Initialize session state for Tavily usage if not exists
    if 'tavily_usage_count' not in st.session_state:
        st.session_state.tavily_usage_count = 0
        st.session_state.tavily_last_check = None
    
    # Only check once per hour to avoid excessive API calls
    current_time = datetime.now()
    if (st.session_state.tavily_last_check is None or 
        (current_time - st.session_state.tavily_last_check).total_seconds() > 3600):
        
        try:
            # Make API request to Tavily usage endpoint
            headers = {
                "Authorization": f"Bearer {TAVILY_API_KEY}"
            }
            response = requests.get(
                "https://api.tavily.com/v1/usage",
                headers=headers
            )
            
            if response.status_code == 200:
                usage_data = response.json()
                # Extract the current month's usage
                current_month = current_time.strftime("%Y-%m")
                monthly_usage = 0
                
                # Parse the usage data - structure may vary based on Tavily's API
                if "usage" in usage_data:
                    for period, count in usage_data["usage"].items():
                        if period.startswith(current_month):
                            monthly_usage += count
                
                # Update session state
                st.session_state.tavily_usage_count = monthly_usage
                st.session_state.tavily_last_check = current_time
                
                print(f"Tavily API usage for current month: {monthly_usage}")
            else:
                print(f"Failed to get Tavily usage data: {response.status_code} - {response.text}")
        
        except Exception as e:
            print(f"Error checking Tavily usage: {str(e)}")
    
    # Check if usage exceeds limit
    is_limit_exceeded = st.session_state.tavily_usage_count >= 600
    
    return (st.session_state.tavily_usage_count, is_limit_exceeded) 