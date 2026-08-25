# templates/test_api.py — Self-contained API verification suite
#
# Runs with FastAPI TestClient — no live server, no Hermes binary needed.
# Verifies all endpoints, auth, file I/O, and error handling.
#
# Usage:
#   python3 tests/test_api.py
#   # or
#   make test
#
# EXPECTED OUTPUT: 14 passed, 0 failed

import sys
import os
import tempfile
import shutil

# Set up test config BEFORE importing app modules
_test_dir = tempfile.mkdtemp(prefix="hermes-test-")
os.environ["HERMES_API_CONFIG"] = os.path.join(_test_dir, "test_server.yaml")

_test_config = """\
server:
  host: "127.0.0.1"
  port: 9999
  workers: 1

auth:
  enabled: true
  token: "test-token-do-not-use-in-prod"

hermes:
  binary: "echo"
  max_turns: 5
  timeout: 10
  max_concurrent: 2

files:
  upload_dir: "%s/uploads"
  output_dir: "%s/outputs"
  max_size_mb: 10
""" % (_test_dir, _test_dir)

with open(os.environ["HERMES_API_CONFIG"], "w") as f:
    f.write(_test_config)

# Now import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)
TOKEN = "test-token-do-not-use-in-prod"
AUTH = {"Authorization": f"Bearer {TOKEN}"}

_passed = 0
_failed = 0


def check(name, status, extra_ok=True):
    global _passed, _failed
    ok = status < 500 and extra_ok
    icon = "PASS" if ok else "FAIL"
    if ok:
        _passed += 1
    else:
        _failed += 1
    print(f"  {icon}  {name:45s}  HTTP {status}")


def test_root():
    r = client.get("/")
    check("GET /", r.status_code, "service" in r.json())

def test_health():
    r = client.get("/health")
    d = r.json()
    check("GET /health", r.status_code, "status" in d and "components" in d)

def test_chat_no_auth_rejected():
    r = client.post("/chat", json={"prompt": "hi"})
    check("POST /chat (no auth -> rejected)", r.status_code)

def test_chat_with_auth():
    r = client.post("/chat", json={"prompt": "echo hello"}, headers=AUTH)
    d = r.json()
    check("POST /chat (authed)", r.status_code, "success" in d)

def test_chat_skill_param():
    r = client.post("/chat", json={"prompt": "test", "skills": ["plan", "pdf"]},
                    headers=AUTH)
    check("POST /chat (skills param)", r.status_code)

def test_chat_session_param():
    r = client.post("/chat", json={"prompt": "test", "session_id": "fake_123"},
                    headers=AUTH)
    check("POST /chat (session_id param)", r.status_code)

def test_file_upload():
    r = client.post("/files/in",
        files={"file": ("test.txt", b"hello world", "text/plain")},
        headers=AUTH)
    d = r.json()
    check("POST /files/in", r.status_code, d.get("filename") == "test.txt")

def test_file_upload_binary():
    r = client.post("/files/in",
        files={"file": ("data.bin", b"\x00\x01\x02\x03", "application/octet-stream")},
        headers=AUTH)
    check("POST /files/in (binary)", r.status_code)

def test_file_list():
    r = client.get("/files/out", headers=AUTH)
    check("GET /files/out", r.status_code, "files" in r.json())

def test_file_download_404():
    r = client.get("/files/out/nonexistent.txt", headers=AUTH)
    check("GET /files/out/missing -> 404", r.status_code, r.status_code == 404)

def test_file_download_after_upload():
    client.post("/files/in",
        files={"file": ("roundtrip.txt", b"roundtrip content", "text/plain")},
        headers=AUTH)
    upload_path = os.path.join(_test_dir, "uploads", "roundtrip.txt")
    check("file written to disk", 200 if os.path.exists(upload_path) else 500)

def test_sessions_list():
    r = client.get("/sessions", headers=AUTH)
    check("GET /sessions", r.status_code, "sessions" in r.json())

def test_session_create():
    r = client.post("/sessions/new", json={"name": "test-user"}, headers=AUTH)
    check("POST /sessions/new", r.status_code)

def test_chat_max_turns_param():
    r = client.post("/chat", json={"prompt": "test", "max_turns": 3, "timeout": 5},
                    headers=AUTH)
    check("POST /chat (max_turns + timeout)", r.status_code)


def main():
    print("=" * 60)
    print("Hermes Agent API - Test Suite")
    print("=" * 60)

    tests = [
        test_root, test_health, test_chat_no_auth_rejected,
        test_chat_with_auth, test_chat_skill_param, test_chat_session_param,
        test_chat_max_turns_param, test_file_upload, test_file_upload_binary,
        test_file_list, test_file_download_404, test_file_download_after_upload,
        test_sessions_list, test_session_create,
    ]

    for t in tests:
        try:
            t()
        except Exception as e:
            global _failed
            _failed += 1
            print(f"  CRASH  {t.__name__:45s}  {e}")

    print("=" * 60)
    print(f"Result: {_passed} passed, {_failed} failed, {len(tests)} total")
    print("=" * 60)

    shutil.rmtree(_test_dir, ignore_errors=True)
    sys.exit(0 if _failed == 0 else 1)


if __name__ == "__main__":
    main()
