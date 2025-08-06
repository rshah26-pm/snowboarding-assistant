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

# ===== MODEL CONFIGURATION =====
# Model names for different tasks
INTENT_CLASSIFIER_MODEL = os.environ.get("INTENT_CLASSIFIER_MODEL", "llama-3.1-8b-instant")
RESPONSE_GENERATION_MODEL = os.environ.get("RESPONSE_GENERATION_MODEL", "llama-3.1-8b-instant")

# Temperature settings for different tasks
TEMPERATURE_CONFIGS = {
    "intent_classifier": float(os.environ.get("INTENT_CLASSIFIER_TEMPERATURE", "0.1")),
    "response_generation": float(os.environ.get("RESPONSE_GENERATION_TEMPERATURE", "0.7"))
}

# ===== RATE LIMITING & USAGE LIMITS =====
MAX_MESSAGE_COUNT = int(os.environ.get("MAX_MESSAGE_COUNT", "12"))
RATE_LIMIT_PER_MINUTE = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "20"))
TAVILY_MONTHLY_LIMIT = int(os.environ.get("TAVILY_MONTHLY_LIMIT", "600"))

# ===== CONVERSATION & HISTORY LIMITS =====
MAX_HISTORY_MESSAGES = int(os.environ.get("MAX_HISTORY_MESSAGES", "8"))
MAX_SOURCES_TO_SHOW = int(os.environ.get("MAX_SOURCES_TO_SHOW", "5"))
MAX_SEARCH_RESULTS = int(os.environ.get("MAX_SEARCH_RESULTS", "3"))

# ===== LOCATION & SEARCH CONFIGURATION =====
LOCATION_KEYWORDS = [
    "near me", "nearby", "closest", "nearest", 
    "my location", "my area", "distance", "how far"
]

# ===== FEATURE FLAGS =====
ENABLE_WEB_SEARCH = os.environ.get("ENABLE_WEB_SEARCH", "true").lower() == "true"
ENABLE_LOCATION_SERVICES = os.environ.get("ENABLE_LOCATION_SERVICES", "true").lower() == "true"
ENABLE_SOURCE_LINKS = os.environ.get("ENABLE_SOURCE_LINKS", "true").lower() == "true"
COMPRESS_IMAGES = os.environ.get("COMPRESS_IMAGES", "false").lower() == "true"
DEBUG_MODE = os.environ.get("DEBUG_MODE", "false").lower() == "true"

# ===== PROMPT VERSION CONTROL =====
# Default prompt versions (can be overridden per request)
DEFAULT_PROMPT_VERSIONS = {
    "response_generation": os.environ.get("RESPONSE_PROMPT_VERSION", "v1"),
    "intent_classifier": os.environ.get("INTENT_PROMPT_VERSION", "v1"),
    "location_context": os.environ.get("LOCATION_PROMPT_VERSION", "v1"),
    "web_search_results": os.environ.get("WEB_SEARCH_PROMPT_VERSION", "v1"),
    "web_search_unavailable": os.environ.get("WEB_SEARCH_UNAVAILABLE_PROMPT_VERSION", "v1"),
    "no_location_shared": os.environ.get("NO_LOCATION_PROMPT_VERSION", "v1"),
    "location_sharing_suggestion": os.environ.get("LOCATION_SHARING_PROMPT_VERSION", "v1")
}

# ===== EVALUATION CONFIGURATION =====
# Settings specifically for running evaluations
EVAL_CONFIG = {
    "enable_logging": True,
    "log_prompt_versions": True,
    "log_model_usage": True,
    "log_search_usage": True,
    "track_response_times": True
}

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
    is_limit_exceeded = st.session_state.tavily_usage_count >= TAVILY_MONTHLY_LIMIT
    
    return (st.session_state.tavily_usage_count, is_limit_exceeded)

def get_config_summary():
    """Get a summary of current configuration for debugging/evaluation"""
    return {
        "models": {
            "intent_classifier": INTENT_CLASSIFIER_MODEL,
            "response_generation": RESPONSE_GENERATION_MODEL
        },
        "temperatures": TEMPERATURE_CONFIGS,
        "limits": {
            "max_messages": MAX_MESSAGE_COUNT,
            "rate_limit_per_minute": RATE_LIMIT_PER_MINUTE,
            "tavily_monthly_limit": TAVILY_MONTHLY_LIMIT,
            "max_history_messages": MAX_HISTORY_MESSAGES,
            "max_sources": MAX_SOURCES_TO_SHOW
        },
        "features": {
            "web_search": ENABLE_WEB_SEARCH,
            "location_services": ENABLE_LOCATION_SERVICES,
            "source_links": ENABLE_SOURCE_LINKS,
            "debug_mode": DEBUG_MODE
        },
        "prompt_versions": DEFAULT_PROMPT_VERSIONS
    }