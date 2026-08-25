# api/main.py — FastAPI Application Entry Point
# Run: uvicorn api.main:app --host 0.0.0.0 --port 8000
#
# Part of the hermes-agent-api-bridge skill template.
# Copy this file structure into your project and adapt.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import chat, sessions, files, health
from api.core.config import load_config

config = load_config()

app = FastAPI(
    title="Hermes Agent API",
    description="Stateful Hermes Agent accessible over HTTP",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(chat.router, tags=["chat"])
app.include_router(sessions.router, tags=["sessions"])
app.include_router(files.router, tags=["files"])


@app.get("/")
async def root():
    return {
        "service": "Hermes Agent API",
        "version": "1.0.0",
        "endpoints": {
            "chat": "POST /chat",
            "sessions": "GET /sessions, POST /sessions/new",
            "files_in": "POST /files/in",
            "files_out": "GET /files/out, GET /files/out/{filename}",
            "health": "GET /health",
        },
    }


# === Also need these files (see full scaffold in PROJECT_SCAFFOLD.md) ===
#
# api/__init__.py             (empty)
# api/core/__init__.py        (empty)
# api/core/config.py          (load_config from YAML)
# api/core/hermes_bridge.py   (call_hermes, _get_latest_session_id)
# api/routes/__init__.py      (empty)
# api/routes/chat.py          (POST /chat)
# api/routes/sessions.py      (GET /sessions, POST /sessions/new)
# api/routes/files.py         (POST /files/in, GET /files/out)
# api/routes/health.py        (GET /health)
# api/auth/__init__.py        (empty)
# api/auth/token_auth.py      (verify_token dependency)
# config/server.yaml          (server config)
# config/requirements.txt     (fastapi, uvicorn, etc.)
