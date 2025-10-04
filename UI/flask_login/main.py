# main.py
import os
from typing import Optional

import httpx
from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.status import HTTP_302_FOUND
from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv

load_dotenv()

# ---- Config ----
SESSION_SECRET = os.getenv("SESSION_SECRET", "CHANGE_ME_LONG_RANDOM")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")  # required for email+pass

# Where to send users after login/logout (your Streamlit app)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:8501")

# ---- App ----
app = FastAPI()

# Sessions for request.session
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="lax",      # cross-port friendly on localhost
    https_only=False,     # set True in prod behind HTTPS
    max_age=60 * 60 * 24, # 1 day
)

# Allow Streamlit (localhost:8501) to call this API with cookies
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8501", "http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

# OAuth (Google OIDC)
oauth = OAuth()
oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    client_kwargs={"scope": "openid email profile"},
)

# Utils
def is_logged_in(request: Request) -> bool:
    return request.session.get("user") is not None

def build_redirect_uri(request: Request, path: str) -> str:
    # request.base_url -> e.g. 'http://127.0.0.1:8000/'
    base = str(request.base_url)
    if base.endswith("/"):
        base = base[:-1]
    return f"{base}{path}"

# Routes
@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.get("/me")
async def me(request: Request):
    if is_logged_in(request):
        return {"authenticated": True, "user": request.session["user"]}
    return {"authenticated": False}

# ---- Login Page (FastAPI-served) ----
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, next: Optional[str] = None, error: Optional[str] = None):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "next": next or FRONTEND_URL, "error": error}
    )

# ---- Google Login ----
@app.get("/login/google")
async def login_google(request: Request, next: Optional[str] = None):
    request.session["post_login_redirect"] = next or FRONTEND_URL
    redirect_uri = build_redirect_uri(request, "/auth/callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth/callback")
async def auth_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    userinfo = token.get("userinfo") or await oauth.google.parse_id_token(request, token)

    request.session["user"] = {
        "provider": "google",
        "sub": userinfo.get("sub"),
        "email": userinfo.get("email"),
        "name": userinfo.get("name"),
        "picture": userinfo.get("picture"),
    }
    next_url = request.session.pop("post_login_redirect", FRONTEND_URL)
    return RedirectResponse(next_url, status_code=HTTP_302_FOUND)

# ---- Email + Password (Firebase Auth via REST) ----
FIREBASE_SIGNIN_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"

@app.post("/login/email", response_class=HTMLResponse)
async def login_email(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    next: str = Form(default=None),
):
    if not FIREBASE_API_KEY:
        # render page with error if key missing
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Server missing FIREBASE_API_KEY.", "next": next or FRONTEND_URL},
            status_code=500
        )

    payload = {"email": email, "password": password, "returnSecureToken": True}
    params = {"key": FIREBASE_API_KEY}

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(FIREBASE_SIGNIN_URL, params=params, json=payload)

    data = resp.json()
    if resp.status_code != 200:
        # Typical error shape: {'error': {'message': 'INVALID_PASSWORD', ...}}
        msg = data.get("error", {}).get("message", "Authentication failed")
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": f"Email login failed: {msg}", "next": next or FRONTEND_URL},
            status_code=401
        )

    # Success: minimal session (no token parsing in Streamlit)
    # data includes idToken, refreshToken, localId, email, expiresIn, etc.
    request.session["user"] = {
        "provider": "firebase",
        "uid": data.get("localId"),
        "email": data.get("email") or email,
        # you can store idToken server-side if you plan to call Firebase APIs later
        "id_token": data.get("idToken"),
    }
    # Optionally store refreshToken if you want server-side refresh later
    request.session["refresh_token"] = data.get("refreshToken")

    return RedirectResponse(next or FRONTEND_URL, status_code=HTTP_302_FOUND)

# ---- Logout ----
@app.get("/logout")
async def logout(request: Request, next: Optional[str] = None):
    request.session.clear()
    return RedirectResponse(next or FRONTEND_URL, status_code=HTTP_302_FOUND)