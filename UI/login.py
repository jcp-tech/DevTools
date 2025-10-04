
import os
import json
import time
import base64
import requests
import streamlit as st
from dotenv import load_dotenv
try:
    import firebase_admin
    from firebase_admin import credentials, auth as fb_admin_auth
    FIREBASE_ADMIN_AVAILABLE = True
except Exception:
    FIREBASE_ADMIN_AVAILABLE = False
load_dotenv()

# ----------------------
# Config via environment
# ----------------------
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY", "")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
OAUTH_CLIENT_SECRET_FILE = os.getenv("OAUTH_CLIENT_SECRET_FILE", "")  # optional path to client_secret.json
SERVICE_ACCOUNT_JSON = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "")  # optional json string or path

# st.sidebar.subheader("Env Check (dev only)")
# st.sidebar.write("FIREBASE_API_KEY set:", bool(FIREBASE_API_KEY))
# st.sidebar.write("OAUTH_CLIENT_SECRET_FILE set:", bool(OAUTH_CLIENT_SECRET_FILE))
# st.sidebar.write("GOOGLE_CLIENT_ID set:", bool(GOOGLE_CLIENT_ID))
# st.sidebar.write("GOOGLE_CLIENT_SECRET set:", bool(GOOGLE_CLIENT_SECRET))
# st.sidebar.write("FIREBASE_SERVICE_ACCOUNT_JSON set:", bool(SERVICE_ACCOUNT_JSON))


# ----------------------
# Constants
# ----------------------
FIREBASE_REST_BASE = "https://identitytoolkit.googleapis.com/v1"
SIGN_UP_URL = f"{FIREBASE_REST_BASE}/accounts:signUp?key={FIREBASE_API_KEY}"
SIGN_IN_PW_URL = f"{FIREBASE_REST_BASE}/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
SIGN_IN_IDP_URL = f"{FIREBASE_REST_BASE}/accounts:signInWithIdp?key={FIREBASE_API_KEY}"
GET_USER_DATA_URL = f"{FIREBASE_REST_BASE}/accounts:lookup?key={FIREBASE_API_KEY}"


def _init_firebase_admin():
    """
    Initialize Firebase Admin SDK if SERVICE_ACCOUNT_JSON is provided.
    Accepts a JSON string or a path to a JSON file.
    """
    if not FIREBASE_ADMIN_AVAILABLE:
        return

    if firebase_admin._apps:
        return  # already initialized

    if SERVICE_ACCOUNT_JSON:
        try:
            if SERVICE_ACCOUNT_JSON.strip().startswith("{"):
                # JSON blob
                cred = credentials.Certificate(json.loads(SERVICE_ACCOUNT_JSON))
            else:
                # Treat as path
                cred = credentials.Certificate(SERVICE_ACCOUNT_JSON)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            st.warning(f"Could not initialize Firebase Admin: {e}")


def verify_firebase_id_token(id_token: str):
    """
    Optionally verify Firebase ID token using Admin SDK if available.
    Returns decoded claims dict or None if verification not possible.
    """
    if not id_token:
        return None
    if FIREBASE_ADMIN_AVAILABLE and firebase_admin._apps:
        try:
            return fb_admin_auth.verify_id_token(id_token)
        except Exception as e:
            st.warning(f"Token verification failed: {e}")
            return None
    return None


def get_user_info_from_id_token(id_token: str):
    """
    Fallback to REST lookup if Admin SDK is not configured.
    """
    try:
        r = requests.post(GET_USER_DATA_URL, json={"idToken": id_token}, timeout=15)
        r.raise_for_status()
        data = r.json()
        users = data.get("users", [])
        return users[0] if users else None
    except Exception as e:
        st.error(f"Failed to fetch user profile: {e}")
        return None


def signup_email_password(email: str, password: str):
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    r = requests.post(SIGN_UP_URL, json=payload, timeout=15)
    r.raise_for_status()
    return r.json()


def login_email_password(email: str, password: str):
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    r = requests.post(SIGN_IN_PW_URL, json=payload, timeout=15)
    r.raise_for_status()
    return r.json()


def firebase_signin_with_google(id_token: str):
    """
    Exchange a Google ID token for a Firebase ID token using the signInWithIdp endpoint.
    """
    post_body = f"id_token={id_token}&providerId=google.com"
    payload = {
        "postBody": post_body,
        "requestUri": "http://localhost",  # must be a valid URL, not used here
        "returnIdpCredential": True,
        "returnSecureToken": True
    }
    r = requests.post(SIGN_IN_IDP_URL, json=payload, timeout=20)
    r.raise_for_status()
    return r.json()


def google_oauth_local_flow():
    import os
    os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request

    scopes = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ]

    flow = None
    if OAUTH_CLIENT_SECRET_FILE:
        flow = InstalledAppFlow.from_client_secrets_file(OAUTH_CLIENT_SECRET_FILE, scopes=scopes)
    elif GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
        client_config = {
            "installed": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost"]
            }
        }
        flow = InstalledAppFlow.from_client_config(client_config, scopes=scopes)
    else:
        st.error("Provide OAUTH_CLIENT_SECRET_FILE or GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET.")
        return None

    try:
        creds = flow.run_local_server(port=0, open_browser=True, prompt="consent")
    except Exception as e:
        st.error(f"OAuth local server failed: {e}")
        return None

    # Ensure we actually get an ID token
    if not getattr(creds, "id_token", None):
        try:
            creds.refresh(Request())
        except Exception as e:
            st.error(f"Could not refresh credentials to obtain ID token: {e}")
            return None

    return getattr(creds, "id_token", None)

def render_profile_box(user_profile: dict):
    st.success("Signed in with Firebase ✅")
    name = user_profile.get("displayName") or user_profile.get("email") or "Unknown User"
    email = user_profile.get("email", "—")
    st.write(f"**Name:** {name}")
    st.write(f"**Email:** {email}")
    if "photoUrl" in user_profile:
        st.image(user_profile["photoUrl"], width=96)

    st.caption("Below is your raw Firebase profile payload:")
    st.code(json.dumps(user_profile, indent=2))


def logout():
    for key in ["firebase_id_token", "firebase_refresh_token", "firebase_user", "idp", "email"]:
        if key in st.session_state:
            del st.session_state[key]


def main():
    st.set_page_config(page_title="Streamlit + Firebase Auth", page_icon="🔐", layout="centered")
    st.title("🔐 Streamlit Login with Firebase Authentication")
    st.write("Google Sign-In and Email/Password using Firebase (REST).")

    _init_firebase_admin()

    # Logged-in view
    if "firebase_id_token" in st.session_state and "firebase_user" in st.session_state:
        render_profile_box(st.session_state["firebase_user"])
        if st.button("Logout"):
            logout()
            st.rerun()
        return

    tab_google, = st.tabs(["Sign in with Google"]) # tab_google, tab_email = st.tabs(["Sign in with Google", "Email / Password"])

    # with tab_email:
    #     mode = st.radio("Choose Mode", ["Login", "Sign Up"], horizontal=True)
    #     email_input = st.text_input("Email")
    #     password_input = st.text_input("Password", type="password")
    #     submit_label = "Create Account" if mode == "Sign Up" else "Login"
    #     if st.button(submit_label, use_container_width=True):
    #         if not email_input or not password_input:
    #             st.warning("Enter both email and password.")
    #         else:
    #             try:
    #                 if mode == "Sign Up":
    #                     resp = signup_email_password(email_input, password_input)
    #                 else:
    #                     resp = login_email_password(email_input, password_input)
    #                 firebase_id_token = resp.get("idToken")
    #                 refresh_token = resp.get("refreshToken")
    #                 if not firebase_id_token:
    #                     st.error("Authentication failed. No idToken in response.")
    #                 else:
    #                     # Lookup profile
    #                     user_info = get_user_info_from_id_token(firebase_id_token) or {"email": email_input}
    #                     st.session_state["firebase_id_token"] = firebase_id_token
    #                     st.session_state["firebase_refresh_token"] = refresh_token
    #                     st.session_state["firebase_user"] = user_info
    #                     st.session_state["idp"] = "password"
    #                     st.session_state["email"] = email_input
    #                     st.success("Authenticated!")
    #                     time.sleep(0.5)
    #                     st.rerun()
    #             except requests.HTTPError as http_err:
    #                 try:
    #                     details = http_err.response.json()
    #                     st.error(f"HTTP error: {details}")
    #                 except Exception:
    #                     st.error(f"HTTP error: {http_err}")
    #             except Exception as e:
    #                 st.error(f"Error: {e}")

    with tab_google:
        st.info("You will be prompted by Google in a separate browser window.")
        if st.button("Continue with Google"):
            with st.spinner("Opening Google OAuth flow..."):
                google_id_token = google_oauth_local_flow()
                if not google_id_token:
                    st.error("No Google ID token returned.")
                else:
                    # Exchange Google ID token for Firebase ID token
                    try:
                        resp = firebase_signin_with_google(google_id_token)
                        firebase_id_token = resp.get("idToken")
                        refresh_token = resp.get("refreshToken")
                        email = resp.get("email")
                        local_id = resp.get("localId")
                        if not firebase_id_token:
                            st.error("Firebase sign-in failed. No idToken in response.")
                        else:
                            # Fetch Firebase user profile
                            decoded = verify_firebase_id_token(firebase_id_token)
                            if decoded is None:
                                # Try REST lookup
                                user_info = get_user_info_from_id_token(firebase_id_token) or {}
                            else:
                                # Map decoded claims to a user-like dict
                                user_info = {
                                    "email": decoded.get("email"),
                                    "user_id": decoded.get("user_id"),
                                    "name": decoded.get("name"),
                                    "picture": decoded.get("picture"),
                                }
                            st.session_state["firebase_id_token"] = firebase_id_token
                            st.session_state["firebase_refresh_token"] = refresh_token
                            st.session_state["firebase_user"] = user_info or {"email": email, "localId": local_id}
                            st.session_state["idp"] = "google"
                            st.session_state["email"] = email or user_info.get("email")
                            st.success("Signed in with Google!")
                            time.sleep(0.5)
                            st.rerun()
                    except Exception as e:
                        st.error(f"Google sign-in failed: {e}")

if __name__ == "__main__":
    main()
