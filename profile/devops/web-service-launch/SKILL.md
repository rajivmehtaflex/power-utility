---
name: web-service-launch
description: Launch a web service (e.g., Chainlit, FastAPI) on a specific port, handling port conflicts, dependencies, and verification.
license: MIT
metadata:
  author: Hermes Agent
  devops_tags: web-service, launch, port, dependency, troubleshooting
  platforms: linux, macos, windows
  version: 1.0.0
---

# Web Service Launch

This skill covers launching a web service on a specific port, commonly used for development UI tools like Chainlit, Streamlit, Flask, FastAPI, etc. It includes steps to check for existing processes, manage dependencies, set environment variables, start the service, and verify it's running.

## When to Use

- You need to start a local web service for development or testing.
- You encounter "address already in use" errors when starting a service.
- You need to verify that a service is responding on a port.
- You want to troubleshoot service startup failures by checking logs.

## Step-by-Step Guide

### 1. Check for Existing Processes

Before starting a service, check if another process is already using the target port.

```bash
# Replace 8001 with your target port
lsof -ti:8001
```

If the command returns a PID, a process is already listening on that port.

### 2. Kill Existing Process (if any)

If a process is using the port, kill it to free the port.

```bash
# Replace 21524 with the PID from lsof
kill -9 21524
```

Alternatively, kill all processes matching a pattern (use with caution):

```bash
pkill -f "chainlit run app.py"  # Example for Chainlit
```

### 3. Set Required Environment Variables

Many services require environment variables for configuration (e.g., port, database paths, API keys).

```bash
# Example for Chainlit: set the port
export CHAINLIT_PORT=8001

# Or set it inline when starting the service:
CHAINLIT_PORT=8001 uv run chainlit run app.py
```

### 4. Install Missing Dependencies

If the service fails to start due to missing dependencies, install them using the project's package manager.

For Python projects using `uv`:
```bash
uv pip install <package>
```

For example, to install `greenlet` (often required by SQLAlchemy):
```bash
uv pip install greenlet
```

Always check the service's logs for import errors to identify missing packages.

### 5. Start the Service

Start the service in the background or foreground, depending on your needs.

**Foreground (for immediate feedback):**
```bash
uv run chainlit run app.py --port 8001
```

**Background (to continue working):**
```bash
# Using the terminal tool with background=true and notify_on_complete=true
terminal(command="uv run chainlit run app.py --port 8001", background=true, notify_on_complete=true)
```

**Note:** If starting via a script or terminal, ensure you are in the correct project directory.

### 6. Verify the Service is Running

Check that the service is listening on the port and responding to HTTP requests.

```bash
# Check port listening
lsof -i :8001

# Check HTTP response (adjust endpoint as needed)
curl -s http://localhost:8001 | head -5
```

### 7. Verify ASGI and WebSocket Behavior Locally

For FastAPI/ASGI services with a browser terminal or other WebSocket route, test the application in-process before starting a public server or cloud deployment. Use `TestClient` for `/health` and `/`, then open the WebSocket, consume the initial server output, send a deterministic command marker, and assert that the marker is returned. If the handler changes into a mounted directory, substitute a temporary directory during the test. Create the verifier under an OS-safe temporary path with a `hermes-verify-` prefix and delete it in `finally`; never add it to the project.

Run the verifier with the project virtualenv and an explicit project-root `PYTHONPATH`. If the agent runtime can leak another Python environment, use a sanitized environment so C-extension imports come from the project venv.

See `references/asgi-websocket-verification.md` for the reusable recipe and the boundary between local behavior evidence and actual cloud deployment evidence. For Modal-hosted public browser terminals, also follow `references/modal-cloud-web-terminal-verification.md` for GPU preflight, sanitized Modal commands, visible browser verification, public-endpoint warnings, and teardown evidence.

### 8. Check Logs for Errors

If the service fails to start or behaves unexpectedly, consult its log files.

Common log locations:
- `./logs/` (project-relative)
- `~/.hermes/logs/` (for Hermes-related services)
- Service-specific logs (e.g., `service/g-fcp-da-chainlit/logs/chainlit.log`)

Look for errors such as:
- `Address already in use`
- `ModuleNotFoundError`
- `Permission denied`
- `API error occurred: Status 403`

## Common Pitfalls and How to Avoid Them

### Pitfall: Forgetting to Free the Port
**Symptom:** `error while attempting to bind on address ('127.0.0.1', 8001): [errno 48] address already in use`  
**Fix:** Always check for and kill existing processes before starting the service.

### Pitfall: Missing Dependencies
**Symptom:** Import errors (e.g., `No module named 'greenlet'`) or runtime errors (e.g., `ValueError: the greenlet library is required`)  
**Fix:** Check the service's startup logs for import errors and install the missing package using the appropriate package manager.

### Pitfall: Incorrect Environment Variables
**Symptom:** Service starts but behaves incorrectly (e.g., using wrong port, failing to connect to database)  
**Fix:** Double-check required environment variables in the service's documentation or `.env.example` file. Set them explicitly when starting the service.

### Pitfall: Not Checking Logs
**Symptom:** Service appears to start but fails silently or shows vague errors  
**Fix:** Always check the service's log files for detailed error messages. Look for timestamps around the startup time.

### Pitfall: Starting in the Wrong Directory
**Symptom:** Service fails to find configuration files, data, or modules  
**Fix:** Ensure you are in the project's root directory or the service's working directory before starting. Use `cd` to the correct path.

## Example: Launching Chainlit for FCP Data Processor

This example demonstrates launching the Chainlit UI for the FCP Data Processor project on port 8001.

```bash
# 1. Kill any existing Chainlit processes
pkill -f "chainlit run app.py"

# 2. Set the port (optional, can be set inline)
export CHAINLIT_PORT=8001

# 3. Install missing dependencies (if any)
cd /Users/rajivmehtapy/Documents/fcp-data-processor/service/g-fcp-da-chainlit
uv pip install greenlet

# 4. Start Chainlit in the background
terminal(command="uv run chainlit run app.py --port 8001", background=true, notify_on_complete=true)

# 5. Verify it's running
lsof -i :8001
curl -s http://localhost:8001 | grep -i "Assistant"

# 6. Check logs for errors
tail -f /Users/rajivmehtapy/Documents/fcp-data-processor/service/g-fcp-da-chainlit/logs/chainlit.log
```

## References

- [Chainlit Documentation](https://docs.chainlit.io/)
- [UV Package Manager](https://docs.astral.sh/uv/)
- [Lsof Command](https://man7.org/linux/man-pages/man8/lsof.8.html)

## Related Skills

- `cli-tool-installation`: For installing CLI tools and dependencies.
- `system-update`: For updating system packages and CLI tools.
- `hermes-agent`: For configuring and extending Hermes Agent itself (includes spawning additional Hermes instances).
