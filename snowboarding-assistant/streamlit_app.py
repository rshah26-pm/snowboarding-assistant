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

MAX_MESSAGE_COUNT = 12  # Set the maximum number of messages allowed per conversation

if 'prompt_count' not in st.session_state:
    st.session_state.prompt_count = 0
    st.session_state.first_prompt_time = time.time()

if 'message_count' not in st.session_state:
    st.session_state.message_count = 0
if 'free_tier_ended' not in st.session_state:
    st.session_state.free_tier_ended = False

def can_issue_prompt():
    add_debug_info("Checking if prompt can be issued")
    current_time = time.time()
    time_elapsed = current_time - st.session_state.first_prompt_time
    
    if time_elapsed > 60:  # Reset the count after a minute
        st.session_state.prompt_count = 0
        st.session_state.first_prompt_time = current_time
    
    if st.session_state.prompt_count < 20:
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

# Add a prominent note about the sidebar for location sharing
st.markdown(
    "<small style='color: green; font-size: 14px;'>💡 Use sidebar to enable share location/request features.</small>",
    unsafe_allow_html=True
)

# Sidebar for location consent and display 
with st.sidebar:
    st.header("Settings")
    
    # Slick consent checkbox
    location_consent = st.checkbox(
        "📍 Share my location",
        value=st.session_state.location_consent,
        help="Your location will be used for personalized recommendations like distance to resorts and local weather",
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
            st.info("Requesting your location... Please allow location access in your browser and wait a few seconds.")
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
        st.success(f"📍 Using your live location now.")
        #st.success(f"📍 Using location: {st.session_state.user_location['address']}")

    # Add a divider
    st.divider()

    # Show usage information

    st.subheader("Usage Information")
    remaining_messages = max(0, MAX_MESSAGE_COUNT - st.session_state.message_count)
    
    # Create a progress bar
    progress = st.session_state.message_count / MAX_MESSAGE_COUNT
    st.progress(progress)
    
    # Show remaining messages
    if remaining_messages > 0:
        st.info(f"{remaining_messages} messages left in this free session.")
    else:
        st.warning("You've reached the free tier limit.")

    # Add a divider after the usage information
    st.divider()
    
    # Feature requests section
    st.subheader("Feature requests")
    st.markdown(
        "Got ideas on how we can make the Snowboarding Assistant even better? "
        "Send an email to **rshah26.pm@gmail.com** or contribute directly to the "
        "project @ [GitHub](https://github.com/rshah26-pm/snowboarding-assistant)",
        unsafe_allow_html=True
    )

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

# First, display chat messages from history EXCEPT the last message if it's being processed
message_placeholder = st.container()
with message_placeholder:
    for i, message in enumerate(st.session_state.messages):
        # Skip displaying the last message if we're in the middle of processing a response
        if i == len(st.session_state.messages) - 1 and message["role"] == "user" and "processing" in st.session_state and st.session_state.processing:
            continue
            
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def get_contextual_suggestions():
    """Return suggestions based on conversation context"""
    # Default suggestions for new conversations
    return [
        "What's the closest resort to me?",
        "Should I go snowboarding tomorrow?",
        "Recommend beginner-friendly gear"
    ]

def initialize_suggestion_bubbles():
    """Display suggestion bubbles only at the start of a new conversation"""
    # Only show suggestions if there are no messages yet
    if len(st.session_state.messages) == 0:
        add_debug_info("Creating initial suggestion bubbles")
        
        suggestions = get_contextual_suggestions()
        add_debug_info(f"Generated {len(suggestions)} suggestions")
        
        # Create a container for the suggestion bubbles
        suggestion_container = st.container()
        
        with suggestion_container:
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            
            # Create columns for a more responsive layout
            cols = st.columns(len(suggestions))
            
            # Create a button for each suggestion
            for i, suggestion in enumerate(suggestions):
                if cols[i].button(suggestion, key=f"suggestion_{i}", use_container_width=True):
                    add_debug_info(f"Suggestion clicked: {suggestion}")
                    # Store the suggestion in session state
                    st.session_state.clicked_suggestion = suggestion
                    # Force a rerun to immediately update the UI
                    st.rerun()

def process_user_input(prompt):
    """Process user input and get assistant response."""
    if not prompt:
        return
    
    # Check if the user has reached the message limit
    
    if st.session_state.message_count >= MAX_MESSAGE_COUNT:
        if not st.session_state.free_tier_ended:
            st.session_state.free_tier_ended = True
            # Add a message to the chat history
            st.session_state.messages.append({
                "role": "assistant", 
                "content": f"⚠️ **You've reached the free tier limit of {MAX_MESSAGE_COUNT} messages per conversation.** \n\n" +
                           "Thank you for understanding as we work to provide this service to all users fairly."
            })
            # Display the message
            with st.chat_message("assistant"):
                st.markdown(f"⚠️ **You've reached the free tier limit of {MAX_MESSAGE_COUNT} messages per conversation.** \n\n" +
                           "Thank you for understanding as we work to provide this service to all users fairly.")
        return
        
    # Increment the message count (counts both user and assistant messages as one interaction)
    st.session_state.message_count += 1
    
    # Check if this is a new prompt (not already in messages)
    is_new_prompt = True
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user" and st.session_state.messages[-1]["content"] == prompt:
        add_debug_info(f"Prompt already in messages, skipping: {prompt}")
        is_new_prompt = False
    
    if is_new_prompt:
        add_debug_info(f"Adding new prompt to messages: {prompt}")
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Check if location consent is given but location is not yet available
        if st.session_state.location_consent and not st.session_state.user_location:
            add_debug_info("Location consent given but location not yet available")
            
            # Wait for location with a simple spinner
            with st.spinner("Waiting for your location data (this may take a few seconds)..."):
                # Wait for a maximum of 10 seconds
                wait_start = time.time()
                while time.time() - wait_start < 10 and not st.session_state.user_location:
                    # Sleep briefly to avoid CPU spinning
                    time.sleep(0.5)
                    
                    # Check if location data is now available in query params
                    location_param = st.query_params.get('location_data')
                    if location_param:
                        try:
                            add_debug_info(f"Found location_data while waiting: {location_param}")
                            lat, lon = map(float, location_param.split(','))
                            
                            # Convert coordinates to location name
                            geolocator = Nominatim(user_agent="snowboarding_assistant")
                            location_data = geolocator.reverse((lat, lon))
                            
                            # Store in session state
                            st.session_state.user_location = {
                                'coordinates': (lat, lon),
                                'address': location_data.address
                            }
                            add_debug_info(f"Successfully obtained location: {st.session_state.user_location}")
                            break
                            
                        except Exception as e:
                            add_debug_info(f"Error processing location data: {str(e)}")
        
        # Get assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                add_debug_info(f"Getting assistant response for: {prompt}")
                while not can_issue_prompt():
                    with st.spinner("Rate limit reached, wait a few seconds..."):
                        add_debug_info("Rate limit reached, waiting...")
                        time.sleep(10)
                
                # Log location status before getting response
                if st.session_state.user_location:
                    add_debug_info(f"Using location for response: {st.session_state.user_location}")
                else:
                    add_debug_info("No location data available for response")
                
                # Pass conversation history to get_snowboard_assistant_response
                conversation_history = st.session_state.messages.copy()
                response = get_snowboard_assistant_response(prompt, conversation_history)
                add_debug_info("Got assistant response")
                
                # Display the response immediately
                st.markdown(response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

def handle_chat_input():
    if prompt := st.chat_input("Ask about snowboarding..."):
        add_debug_info(f"Text input received: {prompt}")
        # Store the text input in session state
        st.session_state.text_input = prompt
        # Force a rerun to immediately update the UI
        st.rerun()

# Check if there's a clicked suggestion to process at the beginning of the app
if 'clicked_suggestion' in st.session_state:
    suggestion = st.session_state.clicked_suggestion
    add_debug_info(f"Processing stored suggestion: {suggestion}")
    # Remove from session state to prevent processing again
    del st.session_state.clicked_suggestion
    # Process the suggestion
    process_user_input(suggestion)

# Check if there's a text input to process at the beginning of the app
elif 'text_input' in st.session_state:
    text = st.session_state.text_input
    add_debug_info(f"Processing stored text input: {text}")
    # Remove from session state to prevent processing again
    del st.session_state.text_input
    # Process the text input
    process_user_input(text)

# Display the suggestion bubbles (only if no messages yet)
initialize_suggestion_bubbles()

# Call the function to handle chat input
handle_chat_input()
