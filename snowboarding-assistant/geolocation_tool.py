from langchain.tools import Tool
import streamlit as st
from geopy.distance import geodesic
from tool_config import get_tool_version, get_tool_description
from prompts import get_prompt
import pandas as pd
import os
import logging

# Configure the logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_ski_resorts_data():
    """Load ski resorts data from CSV file."""
    csv_path = os.path.join(os.path.dirname(__file__), "ski_resorts.csv")

    try:
        df = pd.read_csv(csv_path)
        # Convert to dictionary with resort name as key and (lat, lon) as value
        ski_resorts = {}
        for _, row in df.iterrows():
            ski_resorts[row['resort_name']] = (row['latitude'], row['longitude'])
        logger.info(f"Loaded {len(ski_resorts)} ski resorts from CSV")
        return ski_resorts
    except Exception as e:
        logger.error(f"Error loading ski resorts CSV: {e}")
        # Fallback to a minimal set of resorts if CSV fails
        return {
            'Vail': (39.6433, -106.3781),
            'Breckenridge': (39.4817, -106.0384),
            'Aspen Snowmass': (39.2084, -106.9490)
        }

def get_user_to_resort_distance(query: str = "") -> str:
    """Get user's location and return relevant information for snowboarding recommendations."""
    print(f"🔧 Using tool: resort_distance_calculator")  
    
    if 'user_location' not in st.session_state or not st.session_state.user_location:
        return None
    
    if st.session_state.get('user_location'):
        location_data = st.session_state.user_location
        lat, lon = location_data['coordinates']
        address = location_data['address'] 
    
    location_data = st.session_state.user_location
    try:
        lat, lon = location_data['coordinates']
        address = location_data['address']
        
        # Load ski resorts data from CSV file
        ski_resorts = load_ski_resorts_data()
        
        # Calculate distances to all resorts
        resort_distances = []
        for resort, coords in ski_resorts.items():
            distance = geodesic(location_data['coordinates'], coords).miles
            resort_distances.append((resort, distance))
        
        # Sort by distance and get the 5 closest
        resort_distances.sort(key=lambda x: x[1])
        closest_resorts = resort_distances[:5]
        
        # Format distances for the 5 closest resorts
        result = {
            "address": address,
            "closest_resorts": {resort: distance for resort, distance in closest_resorts}
        }
        return result        
    except Exception as e:
        logger.error("Error processing location data, returning None")
        return None
"""
def get_resort_proximity_info(query: str = "") -> str:
    print(f"🔧 Using tool: resort_distance_calculator")  
    
    if st.session_state.get('user_location'):
        location_data = st.session_state.user_location
        lat, lon = location_data['coordinates']
        address = location_data['address']

        location_info = resort_distance_calculator.run("")

        # Format location context using template from prompts.json
        location_context_template = get_prompt("location_context", LOCATION_PROMPT_VERSION)
        location_context = location_context_template.format(
            address=address,
            lat=lat,
            lon=lon,
            location_info=location_info
        )
        system_context += "\n" + location_context
        logger.info(f"Location data provided: {address}")
    else:
        # Add no-location message from prompts.json
        no_location_msg = get_prompt("no_location_shared", NO_LOCATION_PROMPT_VERSION)
        system_context += "\n" + no_location_msg  

    return location_context
"""

# Define the tool
resort_distance_calculator = Tool(
    name="resort_distance_calculator",
    description=get_tool_description("resort_distance_calculator", get_tool_version("resort_distance_calculator")),
    func=get_user_to_resort_distance
)