import os
import json
import uuid
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
import httpx

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")    # ADK / Agent API
AUTH_BASE_URL = os.getenv("AUTH_BASE_URL", "http://127.0.0.1:8001")  # Existing auth server on :8001
APP_NAME = os.getenv("APP_NAME", "DevTools")

app = FastAPI(title="DevTools Chat UI (FastAPI Frontend)", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8501", "http://localhost:8501", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

def get_http_client():
    return httpx.AsyncClient(timeout=30.0)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # Inject simple constants the template needs
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "APP_NAME": APP_NAME,
            "API_BASE_URL": API_BASE_URL,
            "AUTH_BASE_URL": AUTH_BASE_URL,
        },
    )

@app.get("/login")
async def login():
    return RedirectResponse(f"{AUTH_BASE_URL}/login")

@app.get("/logout")
async def logout():
    return RedirectResponse(f"{AUTH_BASE_URL}/logout")

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
