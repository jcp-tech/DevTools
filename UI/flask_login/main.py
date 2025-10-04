# main.py
import os
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.status import HTTP_302_FOUND
from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv

load_dotenv()

SESSION_SECRET = os.getenv("SESSION_SECRET", "CHANGE_ME_LONG_RANDOM")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# Where to send users after login/logout (your Streamlit app)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:8501")

app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="lax",
    https_only=False,     # True in production
    max_age=60 * 60 * 24, # 1 day
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8501", "http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

oauth = OAuth()
oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    client_kwargs={"scope": "openid email profile"},
)

def is_logged_in(request: Request) -> bool:
    return request.session.get("user") is not None

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.get("/me")
async def me(request: Request):
    if is_logged_in(request):
        return {"authenticated": True, "user": request.session["user"]}
    return {"authenticated": False}

@app.get("/login")
async def login(request: Request, next: Optional[str] = None):
    # Save where to redirect after login
    request.session["post_login_redirect"] = next or FRONTEND_URL

    # Dynamically build redirect URI (e.g. http://127.0.0.1:8000/auth/callback)
    redirect_uri = str(request.base_url)[:-1] + "/auth/callback" # os.getenv("GOOGLE_REDIRECT_URI", "http://127.0.0.1:8000/auth/callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth/callback")
async def auth_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    userinfo = token.get("userinfo") or await oauth.google.parse_id_token(request, token)

    request.session["user"] = {
        "sub": userinfo.get("sub"),
        "email": userinfo.get("email"),
        "name": userinfo.get("name"),
        "picture": userinfo.get("picture"),
    }

    next_url = request.session.pop("post_login_redirect", FRONTEND_URL)
    return RedirectResponse(next_url, status_code=HTTP_302_FOUND)

@app.get("/logout")
async def logout(request: Request, next: Optional[str] = None):
    request.session.clear()
    return RedirectResponse(next or FRONTEND_URL, status_code=HTTP_302_FOUND)
