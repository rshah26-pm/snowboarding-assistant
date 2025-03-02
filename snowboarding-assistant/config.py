import os
from dotenv import load_dotenv
import streamlit as st

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