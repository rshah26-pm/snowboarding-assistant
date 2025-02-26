import streamlit as st
import streamlit.components.v1 as components
from main import get_snowboard_assistant_response
from geopy.geocoders import Nominatim
import os

# Initialize session state
if 'user_location' not in st.session_state:
    st.session_state.user_location = None
if "messages" not in st.session_state:
    st.session_state.messages = []

st.set_page_config(page_title="Snowboarding Assistant", page_icon="🏂")

st.title("🏂 Snowboarding Assistant")
st.write("Ask me anything about planning your snowboarding season, trips, or gear!")

def init_geolocation():
    components.html(
        """
        <script>
        function getLocation() {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    function(position) {
                        const locationParam = `${position.coords.latitude},${position.coords.longitude}`;
                        window.location.search = `?location=${locationParam}`;
                    },
                    function(error) {
                        console.error("Error getting location:", error);
                        alert("Error getting location: " + error.message);
                    }
                );
            } else {
                alert("Geolocation is not supported by this browser.");
            }
        }
        </script>
        <button onclick="getLocation()" id="geoButton">Get Location</button>
        """,
        height=50,
    )

def get_browser_location():
    """Get user location using a dropdown selector"""
    with st.sidebar:
        # Major cities/regions as starting points
        locations = {
            "San Francisco Bay Area": (37.7749, -122.4194),
            "Los Angeles": (34.0522, -118.2437),
            "Sacramento": (38.5816, -121.4944),
            "Las Vegas": (36.1699, -115.1398),
            "Phoenix": (33.4484, -112.0740),
            "Seattle": (47.6062, -122.3321),
            "Portland": (45.5155, -122.6789),
            "Salt Lake City": (40.7608, -111.8910),
            "Denver": (39.7392, -104.9903),
        }
        
        st.write("📍 Location Settings")
        selected_location = st.selectbox(
            "Select your starting point",
            options=list(locations.keys()),
            key="location_selector"
        )
        
        if selected_location:
            try:
                # Get coordinates for selected location
                lat, lon = locations[selected_location]
                
                # Convert coordinates to location name
                geolocator = Nominatim(user_agent="snowboarding_assistant")
                location_data = geolocator.reverse((lat, lon))
                
                # Store in session state
                st.session_state.user_location = {
                    'coordinates': (lat, lon),
                    'address': f"{selected_location}, {location_data.address.split(',')[-1].strip()}",
                    'city': selected_location
                }
                
                st.success(f"Using {selected_location}")
                
            except Exception as e:
                st.error(f"Error processing location: {e}")
                st.session_state.user_location = None

# Add location functionality before the chat interface
get_browser_location()

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What would you like to know?"):
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = get_snowboard_assistant_response(prompt)
            st.markdown(response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})