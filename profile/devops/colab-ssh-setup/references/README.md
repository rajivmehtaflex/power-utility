# Google Colab CLI (mighty-colab) Guide

This guide explains how to install and use the `colab` CLI utility to manage Google Colab runtimes from your local terminal, enabling remote execution and VSCode integration.

## 🚀 Installation

The CLI is provided by the `google-colab-cli` package. The recommended installation method on macOS/Linux is via `uv` to ensure a clean, isolated environment.

```bash
# Install the CLI tool globally using uv
uv tool install mighty-colab
```

### Verifying Installation
Run the following to ensure the `colab` command is available:
```bash
which colab
# Expected output: /Users/<user>/.local/bin/colab
```

## 🔑 Authentication

The CLI requires authentication to communicate with the Colab backend. For headless or agent-driven environments, **Application Default Credentials (ADC)** are recommended.

Run this command to authenticate your local environment with the necessary scopes:
```bash
gcloud auth application-default login \
  --scopes=openid,\
https://www.googleapis.com/auth/cloud-platform,\
https://www.googleapis.com/auth/userinfo.email,\
https://www.googleapis.com/auth/colaboratory
```

*Note: When running `colab` commands, always use the `--auth=adc` flag.*

## 🛠️ Common Use Cases & Sample Prompts

If you are using an AI agent (like Hermes), you can use these prompts to trigger the correct CLI workflows.

### 1. Provisioning a New Runtime
**Case:** You need a fresh VM to start working.

- **CPU Session:**
  > "Create a new Colab CPU session named `my-research-env` using the colab CLI."
- **GPU Session (e.g., T4):**
  > "Provision a Colab T4 GPU session named `gpu-worker` using the colab CLI."

### 2. VSCode / IDE Remote Development
**Case:** You want to use VSCode's full feature set (extensions, debugger) on a Colab VM.

- **Setup Workflow:**
  > "Use the `colab-ssh-setup` skill to connect my local VSCode to a new Colab session named `dev-box`."

### 3. Remote Script Execution
**Case:** You have a local `.py` file you want to run on the Colab VM without opening a browser.

- **Run local file:**
  > "Run the local script `train_model.py` on the `my-research-env` Colab session and download the logs."

### 4. Interactive Access
**Case:** You need a quick shell to check files or install a package.

- **Drop into Console:**
  > "Open an interactive console for the `my-research-env` Colab session."

### 5. Lifecycle Management
**Case:** You are finished and want to stop billing compute units.

- **Stop Session:**
  > "Stop the `my-research-env` Colab session to release the resources."

---

## ⚠️ Critical Pitfalls (macOS / Hermes)

### The PYTHONPATH Leak
On macOS, the `colab` binary (installed via `uv`) often crashes with `ModuleNotFoundError: No module named 'pydantic_core'` because the environment leaks a system `PYTHONPATH` into the tool's isolated venv.

**The Fix:** Always clear the `PYTHONPATH` before running `colab` commands in the terminal:
```bash
export PYTHONPATH=""
colab --auth=adc sessions
```

### SSH Session Limit
Google Colab generally allows only **one active SSH connection** per runtime. If you are connected via VSCode, attempting to open a second interactive shell via `colab ssh` will result in an **HTTP 429 (Too Many Requests)** error. Close your IDE connection first.
