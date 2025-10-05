import json
import os
import uuid
from datetime import datetime
from typing import Optional

import httpx
from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.status import HTTP_302_FOUND

load_dotenv()

SESSION_SECRET = os.getenv("SESSION_SECRET", "CHANGE_ME_LONG_RANDOM")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")
FRONTEND_URL = os.getenv("FRONTEND_URL", "/")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
APP_NAME = os.getenv("APP_NAME", "DevTools")

FIREBASE_SIGNIN_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"

app = FastAPI(title="DevTools Chat UI", version="1.0.0")

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="lax",
    https_only=False,
    max_age=60 * 60 * 24,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8501", "http://localhost:8501", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

oauth = OAuth()
oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    client_kwargs={"scope": "openid email profile"},
)


def get_http_client():
    return httpx.AsyncClient(timeout=30.0)


def is_logged_in(request: Request) -> bool:
    return request.session.get("user") is not None


def build_redirect_uri(request: Request, path: str) -> str:
    base = str(request.base_url)
    if base.endswith("/"):
        base = base[:-1]
    return f"{base}{path}"


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/me")
async def me(request: Request):
    if is_logged_in(request):
        return {"authenticated": True, "user": request.session["user"]}
    return {"authenticated": False}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "APP_NAME": APP_NAME,
            "API_BASE_URL": API_BASE_URL,
        },
    )


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, next: Optional[str] = None, error: Optional[str] = None):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "next": next or FRONTEND_URL, "error": error},
    )


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


@app.post("/login/email", response_class=HTMLResponse)
async def login_email(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    next: str = Form(default=None),
):
    if not FIREBASE_API_KEY:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Server missing FIREBASE_API_KEY.",
                "next": next or FRONTEND_URL,
            },
            status_code=500,
        )

    payload = {"email": email, "password": password, "returnSecureToken": True}
    params = {"key": FIREBASE_API_KEY}

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(FIREBASE_SIGNIN_URL, params=params, json=payload)

    data = resp.json()
    if resp.status_code != 200:
        msg = data.get("error", {}).get("message", "Authentication failed")
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": f"Email login failed: {msg}",
                "next": next or FRONTEND_URL,
            },
            status_code=401,
        )

    request.session["user"] = {
        "provider": "firebase",
        "uid": data.get("localId"),
        "email": data.get("email") or email,
        "id_token": data.get("idToken"),
    }
    request.session["refresh_token"] = data.get("refreshToken")

    return RedirectResponse(next or FRONTEND_URL, status_code=HTTP_302_FOUND)


@app.get("/logout")
async def logout(request: Request, next: Optional[str] = None):
    request.session.clear()
    return RedirectResponse(next or FRONTEND_URL, status_code=HTTP_302_FOUND)


@app.post("/api/session")
async def create_session(payload: dict):
    user_id = payload.get("user_id") or f"user-{uuid.uuid4()}"
    session_id = payload.get("session_id") or f"session-{int(datetime.utcnow().timestamp())}"
    url = f"{API_BASE_URL}/apps/{APP_NAME}/users/{user_id}/sessions/{session_id}"
    async with get_http_client() as client:
        r = await client.post(url, headers={"Content-Type": "application/json"}, content="{}")
    if r.status_code == 200:
        return {"ok": True, "user_id": user_id, "session_id": session_id}
    return JSONResponse(status_code=r.status_code, content={"ok": False, "error": r.text})


@app.post("/api/run")
async def run_message(payload: dict):
    payload["app_name"] = APP_NAME
    async with get_http_client() as client:
        r = await client.post(
            f"{API_BASE_URL}/run",
            headers={"Content-Type": "application/json"},
            content=json.dumps(payload),
        )
    try:
        data = r.json()
    except Exception:
        data = {"error": r.text}
    return JSONResponse(status_code=r.status_code, content=data)
