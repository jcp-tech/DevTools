import streamlit as st
import json
from streamlit_js_eval import streamlit_js_eval

FASTAPI_BASE = "http://127.0.0.1:8000"  # adjust if you used another host/port

st.set_page_config(page_title="Hello World", page_icon="👋", layout="centered")

st.title("Hello World (FastAPI-authenticated)")

# Ask the BROWSER to fetch /me so cookies are sent automatically
js = f"""
(async () => {{
  try {{
    const res = await fetch("{FASTAPI_BASE}/me", {{
      method: "GET",
      credentials: "include"  // send cookies
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
except Exception:
    payload = {"error": "Invalid JSON from /me"}

# Show UI based on FastAPI's answer
if payload.get("error"):
    st.error(f"Auth check failed: {payload['error']}")
elif payload.get("authenticated"):
    user = payload.get("user", {})
    name = user.get("name") or user.get("email") or "user"
    st.success(f"Welcome, {name}! 🎉")
    st.write("This is your protected Hello World page.")
    st.link_button("Log out", f"{FASTAPI_BASE}/logout", type="secondary")
else:
    st.warning("You are not logged in.")
    st.link_button("Continue with Google", f"{FASTAPI_BASE}/login", type="primary")