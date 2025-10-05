"""
V.I.S.I.O.N Application | Need to Change accoring to this Project with LOGIN, TRACKING, ...
"""
import streamlit as st
import requests
import json
import os
import uuid
import time

# Set page config
st.set_page_config(
    page_title="DevTools",
    page_icon="❤️‍🔥",
    layout="centered"
)

## Apply custom CSS
# from pathlib import Path
# css_path = Path(__file__).parent / "vision-theme.css"
# st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# Constants
API_BASE_URL = "http://localhost:8000"
APP_NAME = "DevTools"

# Initialize session state variables
if "user_id" not in st.session_state:
    st.session_state.user_id = f"user-{uuid.uuid4()}"
    
if "session_id" not in st.session_state:
    st.session_state.session_id = None
    
if "messages" not in st.session_state:
    st.session_state.messages = []

# if "attached_file" not in st.session_state:
#     st.session_state.attached_file = []

def create_session():
    """
    Create a new session with the agent.
    
    This function:
    1. Generates a unique session ID based on timestamp
    2. Sends a POST request to the ADK API to create a session
    3. Updates the session state variables if successful
    
    Returns:
        bool: True if session was created successfully, False otherwise
    
    API Endpoint:
        POST /apps/{app_name}/users/{user_id}/sessions/{session_id}
    """
    session_id = f"session-{int(time.time())}"
    response = requests.post(
        f"{API_BASE_URL}/apps/{APP_NAME}/users/{st.session_state.user_id}/sessions/{session_id}",
        headers={"Content-Type": "application/json"},
        data=json.dumps({})
    )
    
    if response.status_code == 200:
        st.session_state.session_id = session_id
        st.session_state.messages = []
        # st.session_state.attached_file = []
        return True
    else:
        st.error(f"Failed to create session: {response.text}")
        return False

def send_message(message):
    """
    Send a message to the agent and process the response.
    
    This function:
    1. Adds the user message to the chat history
    2. Sends the message to the ADK API
    3. Processes the response to extract text and information
    4. Updates the chat history with the assistant's response
    
    Args:
        message (str): The user's message to send to the agent
        
    Returns:
        bool: True if message was sent and processed successfully, False otherwise
    
    API Endpoint:
        POST /run
        
    Response Processing:
        - Parses the ADK event structure to extract text responses
        - Looks for text_to_speech function responses to find file paths
        - Adds both text and information to the chat history
    """
    if not st.session_state.session_id:
        st.error("No active session. Please create a session first.")
        return False
    
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": message})
    
    # Send message to API
    response = requests.post(
        f"{API_BASE_URL}/run",
        headers={"Content-Type": "application/json"},
        data=json.dumps({
            "app_name": APP_NAME,
            "user_id": st.session_state.user_id,
            "session_id": st.session_state.session_id,
            "new_message": {
                "role": "user",
                "parts": [{"text": message}]
            }
        })
    )
    
    if response.status_code != 200:
        st.error(f"Error: {response.text}")
        return False
    
    # Process the response
    events = response.json()
    
    # Extract assistant's text response
    assistant_message = None
    # attached_file_path = None
    
    for event in events:
        # Look for the final text response from the model
        if event.get("content", {}).get("role") == "model" and "text" in event.get("content", {}).get("parts", [{}])[0]:
            assistant_message = event["content"]["parts"][0]["text"]
        
        # # Look for text_to_speech function response to extract file path
        # if "functionResponse" in event.get("content", {}).get("parts", [{}])[0]:
        #     func_response = event["content"]["parts"][0]["functionResponse"]
        #     if func_response.get("name") == "text_to_speech":
        #         response_text = func_response.get("response", {}).get("result", {}).get("content", [{}])[0].get("text", "")
        #         if "File saved as:" in response_text:
        #             parts = response_text.split("File saved as:")[1].strip().split()
        #             if parts:
        #                 attached_file_path = parts[0].strip(".")
    
    # Add assistant response to chat
    if assistant_message:
        st.session_state.messages.append({"role": "assistant", "content": assistant_message}) # , "attached_file": attached_file_path
    
    return True

# UI Components
st.title("V.I.S.I.O.N")

# Sidebar for session management
with st.sidebar:
    st.header("Session Management")
    
    if st.session_state.session_id:
        st.success(f"Active session: {st.session_state.session_id}")
        if st.button("➕ New Session"):
            create_session()
    else:
        st.warning("No active session")
        if st.button("➕ Create Session"):
            create_session()
    
    st.divider()
    st.caption("This app interacts with the Agent via the ADK API Server.")
    st.caption("Make sure the ADK API Server is running on port 8000.")

# Chat interface
st.subheader("Begin by Uploading a Youtube Video Link.")

# Display messages
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    else:
        with st.chat_message("assistant"):
            st.write(msg["content"])
            
            # # Handle File if available
            # if "attached_file" in msg and msg["attached_file"]:
            #     attached_file = msg["attached_file"]
            #     if os.path.exists(attached_file):
            #         st.file(attached_file)
            #     else:
            #         st.warning(f"File not accessible: {attached_file}")

# Input for new messages
if st.session_state.session_id:  # Only show input if session exists
    user_input = st.chat_input("Type your message...")
    if user_input:
        send_message(user_input)
        st.rerun()  # Rerun to update the UI with new messages
else:
    st.info("⬅️ Create a session to start chatting")