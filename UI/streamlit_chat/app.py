"""Combined Streamlit app with authentication-protected chat."""
import json
import os
import time
import uuid
from typing import Any, Dict, Optional

import requests
import streamlit as st
from requests import RequestException
from streamlit_js_eval import streamlit_js_eval

# Page configuration must be the first Streamlit command
st.set_page_config(page_title="DevTools", page_icon="❤️‍🔥", layout="centered")

API_BASE_URL = os.getenv("FASTAPI_BASE", "http://localhost:8000")
APP_NAME = os.getenv("APP_NAME", "DevTools")


def initialize_state() -> None:
    """Ensure all required session state keys exist with sensible defaults."""
    if "user_id" not in st.session_state:
        st.session_state.user_id = f"user-{uuid.uuid4()}"

    if "session_id" not in st.session_state:
        st.session_state.session_id = None

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "audio_files" not in st.session_state:
        st.session_state.audio_files = []


def clear_chat_state() -> None:
    """Reset chat-related session state when the user logs out."""
    st.session_state.session_id = None
    st.session_state.messages = []
    st.session_state.audio_files = []


def check_authentication() -> Dict[str, Any]:
    """Query the FastAPI backend for authentication status via browser JS."""
    js = f"""
    (async () => {{
      try {{
        const res = await fetch("{API_BASE_URL}/me", {{
          method: "GET",
          credentials: "include"
        }});
        const data = await res.json();
        return JSON.stringify(data);
      }} catch (e) {{
        return JSON.stringify({{ error: String(e) }});
      }}
    }})()
    """

    result = streamlit_js_eval(js_expressions=js, key="auth-check")

    if result is None:
        st.info("Checking login status…")
        st.stop()

    try:
        payload = json.loads(result)
    except json.JSONDecodeError:
        payload = {"error": "Invalid JSON returned from /me"}

    return payload


def create_session() -> bool:
    """Create a new chat session for the authenticated user."""
    session_id = f"session-{int(time.time())}"
    try:
        response = requests.post(
            f"{API_BASE_URL}/apps/{APP_NAME}/users/{st.session_state.user_id}/sessions/{session_id}",
            headers={"Content-Type": "application/json"},
            data=json.dumps({}),
            timeout=30,
        )
    except RequestException as exc:
        st.error(f"Failed to create session: {exc}")
        return False

    if response.status_code == 200:
        st.session_state.session_id = session_id
        st.session_state.messages = []
        st.session_state.audio_files = []
        return True

    st.error(f"Failed to create session: {response.text}")
    return False


def send_message(message: str) -> bool:
    """Send a message to the agent and process the response events."""
    if not st.session_state.session_id:
        st.error("No active session. Please create a session first.")
        return False

    st.session_state.messages.append({"role": "user", "content": message})

    try:
        response = requests.post(
            f"{API_BASE_URL}/run",
            headers={"Content-Type": "application/json"},
            data=json.dumps(
                {
                    "app_name": APP_NAME,
                    "user_id": st.session_state.user_id,
                    "session_id": st.session_state.session_id,
                    "new_message": {"role": "user", "parts": [{"text": message}]},
                }
            ),
            timeout=60,
        )
    except RequestException as exc:
        st.error(f"Error communicating with the API: {exc}")
        return False

    if response.status_code != 200:
        st.error(f"Error: {response.text}")
        return False

    events = response.json()
    assistant_message: Optional[str] = None
    audio_file_path: Optional[str] = None

    for event in events:
        content = event.get("content", {})
        parts = content.get("parts", [{}])

        if content.get("role") == "model" and "text" in parts[0]:
            assistant_message = parts[0]["text"]

        if "functionResponse" in parts[0]:
            func_response = parts[0]["functionResponse"]
            if func_response.get("name") == "text_to_speech":
                response_text = (
                    func_response.get("response", {})
                    .get("result", {})
                    .get("content", [{}])[0]
                    .get("text", "")
                )
                if "File saved as:" in response_text:
                    extracted = response_text.split("File saved as:")[1].strip().split()
                    if extracted:
                        audio_file_path = extracted[0].strip(".")

    if assistant_message:
        st.session_state.messages.append(
            {"role": "assistant", "content": assistant_message, "audio_path": audio_file_path}
        )

    return True


def main() -> None:
    initialize_state()

    auth_payload = check_authentication()
    error = auth_payload.get("error")
    authenticated = bool(auth_payload.get("authenticated")) and error is None
    user_info = auth_payload.get("user", {}) if authenticated else {}
    user_name = user_info.get("name") or user_info.get("email") or ""

    top_left, top_right = st.columns([5, 1])
    with top_left:
        st.title("V.I.S.I.O.N")
        if authenticated and user_name:
            st.caption(f"Welcome, {user_name}")

    with top_right:
        st.markdown(
            "<div style='display:flex; justify-content:flex-end;'>",
            unsafe_allow_html=True,
        )
        if authenticated:
            st.link_button("Log out", f"{API_BASE_URL}/logout", type="secondary")
        else:
            st.link_button("Log in", f"{API_BASE_URL}/login", type="primary")
        st.markdown("</div>", unsafe_allow_html=True)

    if error:
        clear_chat_state()
        st.error(f"Auth check failed: {error}")
        return

    if not authenticated:
        clear_chat_state()
        st.warning("You must log in to access the chat interface.")
        return

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
        st.caption("Ensure the ADK API Server is running on port 8000.")

    st.subheader("Begin by uploading a YouTube video link.")

    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.chat_message("user").write(msg["content"])
        else:
            with st.chat_message("assistant"):
                st.write(msg["content"])
                if msg.get("audio_path"):
                    audio_path = msg["audio_path"]
                    if os.path.exists(audio_path):
                        st.audio(audio_path)
                    else:
                        st.warning(f"Audio file not accessible: {audio_path}")

    if st.session_state.session_id:
        user_input = st.chat_input("Type your message…")
        if user_input:
            send_message(user_input)
            st.rerun()
    else:
        st.info("⬅️ Create a session to start chatting")


if __name__ == "__main__":
    main()
