# api/routes/chat.py — Chat endpoint
# api/routes/sessions.py — Session management
# api/routes/health.py — Health check
# api/auth/token_auth.py — Bearer token auth
# api/core/config.py — Config loader
#
# These are compact — combined here for reference.
# In your project, split into separate files per the structure in main.py comments.

# === api/routes/chat.py ===
"""Chat endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from api.core.hermes_bridge import call_hermes
from api.auth.token_auth import verify_token

router = APIRouter()


class ChatRequest(BaseModel):
    prompt: str
    session_id: Optional[str] = None
    skills: Optional[list[str]] = None
    max_turns: Optional[int] = None
    timeout: Optional[int] = None


class ChatResponse(BaseModel):
    response: str
    session_id: Optional[str]
    success: bool
    error: Optional[str] = None


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, _: bool = Depends(verify_token)):
    """Send a prompt to Hermes Agent."""
    result = await call_hermes(
        prompt=req.prompt,
        session_id=req.session_id,
        skills=req.skills,
        max_turns=req.max_turns,
        timeout=req.timeout,
    )
    return ChatResponse(**result)


# === api/routes/sessions.py ===
"""Session management endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.core.hermes_bridge import list_sessions, create_named_session
from api.auth.token_auth import verify_token

router = APIRouter()


class CreateSessionRequest(BaseModel):
    name: str


@router.get("/sessions")
async def get_sessions(_: bool = Depends(verify_token)):
    return {"sessions": await list_sessions()}


@router.post("/sessions/new")
async def new_session(req: CreateSessionRequest, _: bool = Depends(verify_token)):
    session_id = await create_named_session(req.name)
    return {"session_id": session_id, "name": req.name}


# === api/routes/health.py ===
"""Health check endpoints."""

import subprocess
import urllib.request
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    checks = {}
    try:
        result = subprocess.run(["hermes", "version"],
                                capture_output=True, text=True, timeout=5)
        checks["hermes"] = "ok" if result.returncode == 0 else "error"
    except Exception:
        checks["hermes"] = "unreachable"

    try:
        req = urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=3)
        checks["model_server"] = "ok" if req.status == 200 else "error"
    except Exception:
        checks["model_server"] = "unreachable"

    all_ok = all(v == "ok" for v in checks.values())
    return {"status": "healthy" if all_ok else "degraded", "components": checks}


# === api/auth/token_auth.py ===
"""Bearer token authentication."""

from fastapi import HTTPException, Header
from api.core.config import load_config

config = load_config()


async def verify_token(authorization: str = Header(...)):
    if not config["auth"]["enabled"]:
        return True
    expected = f"Bearer {config['auth']['token']}"
    if authorization != expected:
        raise HTTPException(status_code=401,
                           detail="Invalid or missing authentication token")
    return True


# === api/core/config.py ===
"""Load server configuration."""

import yaml
import os


def load_config() -> dict:
    path = os.environ.get("HERMES_API_CONFIG",
                          "/opt/hermes-server/config/server.yaml")
    with open(path) as f:
        return yaml.safe_load(f)
