# Local ASGI and WebSocket Verification

Use this before exposing a new FastAPI/ASGI service through a cloud endpoint or public tunnel.

## Focused checks

1. Create a temporary verifier with `tempfile.NamedTemporaryFile(prefix="hermes-verify-", suffix=".py")`; never leave the verifier in the project.
2. Run it with the project virtualenv, the project root explicitly in `PYTHONPATH`, and a sanitized environment if the agent runtime may leak another Python environment.
3. Import the application and assert configuration values that affect deployment: CPU/RAM/GPU settings, timeout, volume paths, and app name.
4. Use `fastapi.testclient.TestClient` to request `/health` and `/`.
5. Use `client.websocket_connect("/ws")` to receive the initial PTY output, send a deterministic command such as `printf '\\n__HERMES_WS_OK__\\n'`, and assert the marker returns.
6. If the ASGI app changes directory into a mounted volume, temporarily replace that mount path with a `TemporaryDirectory` during the local test. Restore or discard the process afterward.
7. Always remove the temporary verifier in a `finally` block.

## Evidence boundary

These checks prove local imports, route wiring, and PTY/WebSocket behavior. They do not prove Modal image builds, GPU allocation, volume availability, public URL issuance, or cloud authentication. Report those as separate deployment checks and do not run them merely to satisfy local verification.

A deprecation warning from the local test client should be reported separately from the pass/fail result; do not turn a non-fatal warning into a fabricated test failure.
