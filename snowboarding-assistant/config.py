import os
from dotenv import load_dotenv
import streamlit as st

# Load environment variables from .env file if it exists
load_dotenv()

# Function to get API keys from either environment variables or Streamlit secrets
def get_api_key(key_name):
    # First try to get from Streamlit secrets
    if key_name in st.secrets:
        return st.secrets[key_name]
    # Then try to get from environment variables
    elif key_name in os.environ:
        return os.environ[key_name]
    else:
        return None

# Initialize API keys
TAVILY_API_KEY = get_api_key("TAVILY_API_KEY")
GROQ_API_KEY = get_api_key("GROQ_API_KEY") 