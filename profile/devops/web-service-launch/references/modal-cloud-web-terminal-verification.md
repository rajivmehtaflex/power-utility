# Modal cloud web-terminal deployment verification

Use this reference when a FastAPI/ASGI browser terminal is deployed to Modal and the user needs a public URL.

## Preflight

1. Inspect the project configuration before asking for values. Confirm the app name, GPU, CPU, RAM, function timeout, and WebSocket idle timeout.
2. Validate the effective configuration by importing `config.py`; do not rely on shell `grep` output when values have inline comments.
3. Run Modal CLI commands with a sanitized environment when the agent runtime may leak another Python installation:

```bash
env -i HOME="$HOME" \
  PATH="$PWD/.venv/bin:/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin" \
  .venv/bin/modal profile list
```

4. For a GPU deployment, run a bounded availability check before the full deployment when queue time is material. A successful check must show the requested GPU, not merely a successful CLI exit.

## Deployment

Deploy from the project root with a script that validates configuration and uses the sanitized Modal environment. Keep the web-terminal function timeout and the WebSocket receive/idle timeout aligned when the user requests a long-lived connection.

## Verification gate

Do not declare success from deployment output, `curl`, or a health endpoint alone. Verify all three layers:

1. **Modal control plane:** app state is `deployed` and the requested resource configuration is effective.
2. **HTTP/API:** `/health` returns a deterministic success payload including app/resource details.
3. **Browser terminal:** open the public URL in a visible preview and an automation browser, confirm the UI says `Connected`, execute a deterministic marker command such as `printf 'modal-terminal-ok\\n'`, and visually confirm the marker output and returned shell prompt.

A JSON or canvas-based terminal may not expose command output in a DOM snapshot; use a screenshot/vision check when needed.

## Public endpoint and teardown

Explicitly tell the user when the endpoint is unauthenticated. Do not place credentials in the image or volumes. If the terminal should not remain public, add authentication middleware and inject credentials with Modal Secrets. Provide the exact app-stop command after verification so the user can release GPU resources:

```bash
env -i HOME="$HOME" \
  PATH="$PWD/.venv/bin:/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin" \
  .venv/bin/modal app stop <app-name> --yes
```

## Evidence to report

Return the exact public URL, app state, requested GPU/CPU/RAM/timeout, health result, browser-terminal connection status, deterministic command result, and whether authentication is enabled. If deployment reused an existing configuration, say so and identify the files inspected without claiming a configuration change was made.
