# FastAPI Bridge Implementation

Complete code for the Hermes Agent API bridge. See SKILL.md for architecture overview.

## Project Structure

```
api/
├── main.py                  # FastAPI app entry point
├── core/
│   ├── config.py            # YAML config loader
│   └── hermes_bridge.py     # Hermes subprocess wrapper
├── routes/
│   ├── chat.py              # POST /chat
│   ├── sessions.py          # GET /sessions, POST /sessions/new
│   ├── files.py             # POST /files/in, GET /files/out
│   └── health.py            # GET /health
└── auth/
    └── token_auth.py        # Bearer token verification
```

## api/main.py

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import chat, sessions, files, health
from api.core.config import load_config

config = load_config()

app = FastAPI(title="Hermes Agent API", version="1.0.0")

app.add_middleware(CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"])

app.include_router(health.router, tags=["health"])
app.include_router(chat.router, tags=["chat"])
app.include_router(sessions.router, tags=["sessions"])
app.include_router(files.router, tags=["files"])
```

## api/core/config.py

```python
import yaml, os

def load_config():
    path = os.environ.get("HERMES_API_CONFIG", "config/server.yaml")
    with open(path) as f:
        return yaml.safe_load(f)
```

## api/core/hermes_bridge.py

```python
import asyncio, subprocess, re
from api.core.config import load_config
config = load_config()

async def call_hermes(prompt, session_id=None, skills=None,
                      max_turns=None, timeout=None):
    max_turns = max_turns or config["hermes"]["max_turns"]
    timeout = timeout or config["hermes"]["timeout"]

    cmd = [config["hermes"]["binary"], "chat", "-q", "-z",
           "--max-turns", str(max_turns)]
    if session_id:
        cmd.extend(["--resume", session_id])
    if skills:
        for skill in skills:
            cmd.extend(["-s", skill])
    cmd.append(prompt)

    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(None,
            lambda: subprocess.run(cmd, capture_output=True,
                                   text=True, timeout=timeout))
    except subprocess.TimeoutExpired:
        return {"response": "", "session_id": session_id,
                "success": False, "error": f"Timed out after {timeout}s"}

    if result.returncode != 0:
        return {"response": "", "session_id": session_id,
                "success": False,
                "error": result.stderr[:1000] if result.stderr else "Unknown"}

    new_session_id = session_id
    if not session_id:
        new_session_id = await _get_latest_session_id()

    return {"response": result.stdout.strip(),
            "session_id": new_session_id, "success": True, "error": None}

async def _get_latest_session_id():
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(None,
            lambda: subprocess.run(["hermes", "sessions", "list"],
                capture_output=True, text=True, timeout=10))
        for line in result.stdout.strip().split("\n"):
            match = re.search(r"(\d{8}_\d{6}_[a-f0-9]+)", line)
            if match:
                return match.group(1)
    except Exception:
        pass
    return None

async def create_named_session(name):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None,
        lambda: subprocess.run(
            ["hermes", "chat", "-q", "-z", "--continue", name, "Session initialized."],
            capture_output=True, text=True, timeout=30))
    return await _get_latest_session_id()

async def list_sessions():
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None,
        lambda: subprocess.run(["hermes", "sessions", "list"],
            capture_output=True, text=True, timeout=10))
    return [{"raw": line.strip()} for line in result.stdout.split("\n") if line.strip()]
```

## api/routes/chat.py

```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from api.core.hermes_bridge import call_hermes
from api.auth.token_auth import verify_token

router = APIRouter()

class ChatRequest(BaseModel):
    prompt: str
    session_id: str | None = None
    skills: list[str] | None = None
    max_turns: int | None = None
    timeout: int | None = None

@router.post("/chat")
async def chat(req: ChatRequest, _: bool = Depends(verify_token)):
    return await call_hermes(
        prompt=req.prompt, session_id=req.session_id,
        skills=req.skills, max_turns=req.max_turns, timeout=req.timeout)
```

## api/routes/sessions.py

```python
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
```

## api/routes/files.py

```python
import os, shutil
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from api.core.config import load_config
from api.auth.token_auth import verify_token

router = APIRouter()
config = load_config()

def _ensure_dir(path):
    try:
        os.makedirs(path, exist_ok=True)
    except PermissionError:
        raise HTTPException(status_code=500,
            detail=f"Cannot create directory: {path}")

@router.post("/files/in")
async def upload_file(file: UploadFile = File(...),
                      _: bool = Depends(verify_token)):
    upload_dir = config["files"]["upload_dir"]
    _ensure_dir(upload_dir)
    file_path = os.path.join(upload_dir, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except PermissionError:
        raise HTTPException(status_code=500,
            detail=f"Cannot write to: {upload_dir}")
    return {"filename": file.filename, "path": file_path,
            "size_bytes": os.path.getsize(file_path)}

@router.get("/files/out/{filename}")
async def download_file(filename: str, _: bool = Depends(verify_token)):
    path = os.path.join(config["files"]["output_dir"], filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, filename=filename)

@router.get("/files/out")
async def list_output_files(_: bool = Depends(verify_token)):
    output_dir = config["files"]["output_dir"]
    if not os.path.exists(output_dir):
        return {"files": []}
    files = []
    for f in os.listdir(output_dir):
        path = os.path.join(output_dir, f)
        if os.path.isfile(path):
            files.append({"filename": f, "size_bytes": os.path.getsize(path)})
    return {"files": files}
```

## api/routes/health.py

```python
import subprocess, urllib.request
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health():
    checks = {}
    try:
        r = subprocess.run(["hermes", "version"],
            capture_output=True, text=True, timeout=5)
        checks["hermes"] = "ok" if r.returncode == 0 else "error"
    except Exception:
        checks["hermes"] = "unreachable"
    try:
        req = urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=3)
        checks["model_server"] = "ok" if req.status == 200 else "error"
    except Exception:
        checks["model_server"] = "unreachable"
    return {"status": "healthy" if all(v == "ok" for v in checks.values()) else "degraded",
            "components": checks}
```

## api/auth/token_auth.py

```python
from fastapi import HTTPException, Header
from api.core.config import load_config
config = load_config()

async def verify_token(authorization: str = Header(...)):
    if not config["auth"]["enabled"]:
        return True
    if authorization != f"Bearer {config['auth']['token']}":
        raise HTTPException(status_code=401, detail="Invalid token")
    return True
```
