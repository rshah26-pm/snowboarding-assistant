import streamlit as st
import streamlit.components.v1 as components
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from main import get_snowboard_assistant_response
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if 'prompt_count' not in st.session_state:
    st.session_state.prompt_count = 0
    st.session_state.first_prompt_time = time.time()

def can_issue_prompt():
    add_debug_info("Checking if prompt can be issued")
    current_time = time.time()
    time_elapsed = current_time - st.session_state.first_prompt_time
    
    if time_elapsed > 60:  # Reset the count after a minute
        st.session_state.prompt_count = 0
        st.session_state.first_prompt_time = current_time
    
    if st.session_state.prompt_count < 5:
        add_debug_info(f"Prompt count: {st.session_state.prompt_count}")
        st.session_state.prompt_count += 1
        return True
    else:
        add_debug_info("Rate limit reached, wait a few seconds...")
        return False

# Get initial query parameters
initial_location_param = st.query_params.get('location_data')
initial_consent_param = st.query_params.get('consent', 'false').lower() == 'true'

# Initialize session state variables - ONLY if they don't exist
if 'user_location' not in st.session_state:
    st.session_state.user_location = None
    logger.info("Initialized user_location as None")
if 'location_consent' not in st.session_state:
    # Use consent from query param if available
    st.session_state.location_consent = initial_consent_param
    logger.info(f"Initialized location_consent as {initial_consent_param}")
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'location_requested' not in st.session_state:
    st.session_state.location_requested = False
    logger.info("Initialized location_requested as False")
if 'debug_info' not in st.session_state:
    st.session_state.debug_info = []

# Function to add debug info - only logs to console, not to UI
def add_debug_info(message):
    logger.info(message)
    # Still add to session state for potential future use, but don't display
    st.session_state.debug_info.append(f"{time.strftime('%H:%M:%S')} - {message}")

st.set_page_config(page_title="Snowboarding Assistant", page_icon="🏂")

# Function to initialize geolocation
def init_geolocation():
    add_debug_info("Initializing geolocation")
    st.session_state.location_requested = True
    
    components.html(
        """
        <script>
        console.log("Geolocation component loaded");
        
        function getLocation() {
            console.log("getLocation function called");
            if (navigator.geolocation) {
                console.log("Navigator.geolocation is available");
                navigator.geolocation.getCurrentPosition(
                    function(position) {
                        console.log("Got position:", position.coords.latitude, position.coords.longitude);
                        const locationParam = `${position.coords.latitude},${position.coords.longitude}`;
                        console.log("Setting location_data query param to:", locationParam);
                        
                        // Keep the consent parameter and set the location data
                        const searchParams = new URLSearchParams(window.location.search);
                        searchParams.set('consent', 'true');
                        searchParams.set('location_data', locationParam);
                        
                        // Create new URL with updated parameters
                        const newUrl = window.location.pathname + '?' + searchParams.toString();
                        
                        // Navigate to the new URL instead of reloading
                        window.parent.history.pushState({}, '', newUrl);
                        
                        // Send message to Streamlit
                        window.parent.postMessage({
                            type: "streamlit:setQueryParam",
                            queryParams: { 
                                location_data: locationParam,
                                consent: 'true'
                            }
                        }, "*");
                        
                        console.log("Location data sent to Streamlit, reloading...");
                        
                        // Use a more controlled approach to trigger a rerun
                        setTimeout(function() {
                            // Use soft reload
                            window.parent.postMessage({type: "streamlit:forceRerun"}, "*");
                        }, 500);
                    },
                    function(error) {
                        console.error("Error getting location:", error);
                        alert("Error getting location: " + error.message);
                    },
                    { 
                        enableHighAccuracy: true,
                        timeout: 10000,
                        maximumAge: 0
                    }
                );
            } else {
                console.error("Geolocation is not supported by this browser");
                alert("Geolocation is not supported by this browser.");
            }
        }
        
        // Execute immediately when loaded
        console.log("Executing getLocation immediately");
        getLocation();
        </script>
        """,
        height=0
    )
    add_debug_info("Geolocation component rendered")

# Main content area
st.title("🏂 Snowboarding Assistant")
st.write("Ask me anything about planning your snowboarding season, trips, or gear!")


# Sidebar for location consent and display
with st.sidebar:
    st.header("Settings")
    
    # Slick consent checkbox
    location_consent = st.checkbox(
        "📍 Share my location for personalized resort recommendations",
        value=st.session_state.location_consent,
        help="Your location will be used to calculate distances to ski resorts",
        key="location_consent_checkbox"
    )
    
    # Handle consent change
    if location_consent != st.session_state.location_consent:
        add_debug_info(f"Location consent changed from {st.session_state.location_consent} to {location_consent}")
        st.session_state.location_consent = location_consent
        
        # Also update the query parameter
        st.query_params['consent'] = str(location_consent).lower()
        
        if location_consent:
            # Initialize geolocation when consent is given
            add_debug_info("Consent given, initializing geolocation")
            init_geolocation()
            st.info("Requesting your location... Please allow location access in your browser.")
        else:
            # Clear location data when consent is revoked
            add_debug_info("Consent revoked, clearing location data")
            st.session_state.user_location = None
            st.session_state.location_requested = False
            # Clear the location_data query parameter
            if 'location_data' in st.query_params:
                st.query_params.pop('location_data')
    
    # Display current location if available
    if st.session_state.user_location:
        add_debug_info(f"Displaying location: {st.session_state.user_location['address']}")
        st.success(f"📍 Using location: {st.session_state.user_location['address']}")

# Handle the location data from query parameters
location_param = st.query_params.get('location_data')
if location_param:
    add_debug_info(f"Found location_data in query params: {location_param}")
    if st.session_state.location_consent:
        try:
            add_debug_info("Processing location data")
            lat, lon = map(float, location_param.split(','))
            add_debug_info(f"Parsed coordinates: {lat}, {lon}")
            
            # Convert coordinates to location name
            add_debug_info("Converting coordinates to location name")
            geolocator = Nominatim(user_agent="snowboarding_assistant")
            location_data = geolocator.reverse((lat, lon))
            add_debug_info(f"Got location data: {location_data.address}")
            
            # Store in session state
            st.session_state.user_location = {
                'coordinates': (lat, lon),
                'address': location_data.address
            }
            add_debug_info(f"Stored location in session state: {st.session_state.user_location}")
            
            # Reset the location requested flag
            st.session_state.location_requested = False
            
        except Exception as e:
            error_msg = f"Error processing location data: {str(e)}"
            add_debug_info(error_msg)
            st.sidebar.error(error_msg)
    else:
        add_debug_info("Found location_data but consent is not given")

# If location was requested but not yet received, show the geolocation component
if st.session_state.location_requested and st.session_state.location_consent and not st.session_state.user_location:
    add_debug_info("Location requested but not received, reinitializing geolocation")
    init_geolocation()

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

def process_user_input(prompt):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    while not can_issue_prompt():
        with st.spinner("Rate limit reached, wait a few seconds..."):
            add_debug_info("Rate limit reached, wait a few seconds...")
            time.sleep(10)
    with st.spinner("Thinking..."):
        add_debug_info(f"Processing user prompt: {prompt}")
        response = get_snowboard_assistant_response(prompt)

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Force a rerun to update the UI with the new messages
    st.rerun()




def handle_suggestion_click(suggestion):
    add_debug_info(f"Suggestion clicked: {suggestion}")
    # Process the suggestion as if it was entered in the chat input
    process_user_input(suggestion)

def initialize_suggestion_bubbles():
    add_debug_info("Creating suggestion bubbles")
    
    # Create a container for the suggestion bubbles
    suggestion_container = st.container()
    
    with suggestion_container:        
        # Create three columns for the suggestion bubbles
        col1, col2, col3 = st.columns(3)
        
        # Define the suggestion prompts
        suggestions = [
            "What's the closest resort to me?",
            "Should I go snowboarding tomorrow?",
            "Is it colder in Tahoe than it is here right now?"
        ]
        
        # Create a button for each suggestion in its own column
        if col1.button(suggestions[0], key="suggestion_1"):
            handle_suggestion_click(suggestions[0])
            
        if col2.button(suggestions[1], key="suggestion_2"):
            handle_suggestion_click(suggestions[1])
            
        if col3.button(suggestions[2], key="suggestion_3"):
            handle_suggestion_click(suggestions[2])


def handle_chat_input():
    if prompt := st.chat_input("Ask about snowboarding..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Process user input to get assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                add_debug_info(f"Processing user prompt: {prompt}")
                process_user_input(prompt)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})


# Display the suggestion bubbles
initialize_suggestion_bubbles()

# Call the function to handle chat input
handle_chat_input()
