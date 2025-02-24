import streamlit as st
from main import get_snowboard_assistant_response

st.set_page_config(page_title="Snowboarding Assistant", page_icon="🏂")

st.title("🏂 Snowboarding Assistant")
st.write("Ask me anything about planning your snowboarding season, trips, or gear!")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

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