---
name: colab-ssh-setup
description: \"Use when setting up Colab SSH for VSCode via colab CLI.\"
---

# Colab SSH Setup

Provision a Google Colab runtime and expose it as a standard SSH host alias (`~/.ssh/config`) using the `colab` CLI's native WebSocket-to-stdio proxy bridge. This allows VSCode Remote-SSH or other coding agents to connect to a Colab VM without requiring external tunnels like ngrok or serveo.

## Installation & Requirements

- **CLI:** `colab` command, provided by either `mighty-colab` (stable, has `ssh`) or `google-colab-cli` (GitHub main has `ssh`, PyPI 0.6.0 does NOT). **Do NOT use `uv tool install google-colab-cli` from PyPI 0.6.0** — it lacks the `ssh` subcommand and fails with `No such command 'ssh'` (see https://github.com/googlecolab/google-colab-cli/issues/102).
  - **Recommended (fast, verified today on this machine — `mighty-colab 0.2.2`):**
    ```bash
    export PYTHONPATH=""
    uv tool install mighty-colab
    which colab; readlink -f $(which colab)  # → ~/.local/share/uv/tools/mighty-colab/bin/mighty-colab
    colab version  # 0.2.2
    colab --help | grep -q ssh && echo "ssh OK" || echo "ssh MISSING"
    ```
  - **Alternative — GitHub source (the `git clone` suggestion from https://github.com/googlecolab/google-colab-cli/issues/102#issuecomment-5384947488, community member CoffeeBEEE, not maintainer):**
    ```bash
    # Option A — one-liner (heavy: resolves 52 packages + pyarrow 34MiB, ~2-5 min):
    export PYTHONPATH=""
    uv tool install --force git+https://github.com/googlecolab/google-colab-cli.git
    # Option B — explicit git clone (same result, leaves a local repo):
    git clone https://github.com/googlecolab/google-colab-cli.git /tmp/google-colab-cli
    uv tool install --force --from /tmp/google-colab-cli google-colab-cli  # or: uv pip install -e /tmp/google-colab-cli
    # Verify either way:
    which colab; readlink -f $(which colab)  # → .../google-colab-cli/bin/colab
    colab version
    colab ssh --help | head -n 20  # must show --proxy-mode
    ```
    Pin for reproducibility: `uv tool install --force git+https://github.com/googlecolab/google-colab-cli.git@<commit-sha>`
  - **When PyPI publishes `>0.6.0` with `ssh`, `uv tool install google-colab-cli` will work again** — keep the `colab --help | grep ssh` check. Until then, use one of the two above.
- **Auth:** Google Application Default Credentials (ADC). Commands must use `--auth=adc`.
- **Client SSH:** OpenSSH client installed on the local machine.
- **Identity:** An `ed25519` or `ecdsa` key is required. **RSA keys are rejected** by the Colab SSH server.

### Verification (the `which colab` whole idea — run BEFORE any `colab --help | grep ssh` check)
`which colab` + `readlink -f` + `uv tool list` tells you *which binary* you are testing — `google-colab-cli` vs `mighty-colab` create different uv tool dirs and symlink targets.
```bash
which colab; which -a colab; ls -l $(which colab); readlink -f $(which colab)
uv tool list | grep -E "mighty-colab|google-colab-cli"
export PYTHONPATH=""; colab version; colab --help | grep ssh && echo "HAS ssh" || echo "MISSING ssh — reinstall via git or mighty-colab"
COLAB_BIN=$(readlink -f $(which colab)); echo "COLAB_BIN=$COLAB_BIN"  # use this verbatim in ProxyCommand
```
If `which -a` shows two entries, you are shadowing. `COLAB_BIN` must be re-derived after every `uv tool install --force …`.

### Hermes Terminal Fix (macOS)
The `colab` binary is installed via `uv tool` but crashes with `ModuleNotFoundError` because the Hermes terminal leaks its system `PYTHONPATH`. **Always prefix colab commands with `export PYTHONPATH=\"\"`** when running from the Hermes terminal, and use `/usr/bin/env PYTHONPATH=` in `~/.ssh/config` ProxyCommand.

## Workflow

### 1. Session Identification
Before provisioning, the agent must ask the user for the desired session name. 
- **Default suggestion:** `agent-colab`.
- **Constraint:** Avoid spaces and shell-special characters.

Once the name is confirmed, proceed to verify the CLI before provisioning.

### 1a. Pre-flight: does `colab ssh` exist? (with `which colab` chain)
Run this **before** creating any session — it catches the PyPI 0.6.0 broken state:
```bash
which colab; which -a colab; ls -l $(which colab); readlink -f $(which colab)
uv tool list | grep -E "mighty-colab|google-colab-cli"
export PYTHONPATH=""
colab version
if ! colab ssh --help >/dev/null 2>&1; then
  echo "colab ssh missing — you have PyPI 0.6.0 or no install. Reinstalling..."
  # Fast path (mighty-colab has ssh and is already verified):
  uv tool install --force mighty-colab
  # Or GitHub source (heavier, ~2-5 min, per https://github.com/googlecolab/google-colab-cli/issues/102#issuecomment-5384947488):
  # uv tool install --force git+https://github.com/googlecolab/google-colab-cli.git
  which colab; readlink -f $(which colab); colab ssh --help | head -n 20
fi
COLAB_BIN=$(readlink -f $(which colab)); echo "COLAB_BIN=$COLAB_BIN"
```
If this still shows `No such command 'ssh'`, ensure `which colab` points to `~/.local/share/uv/tools/.../bin/colab` and that `uv tool update-shell` has been run; try `uv tool install --force --reinstall git+https://github.com/googlecolab/google-colab-cli.git` and re-check `readlink -f`.

### 2. Provision the Runtime
Create the named session. SSH support is baked in at creation; do not attempt to install `openssh-server` manually on the VM.

```bash
export PYTHONPATH=\"\"
colab --auth=adc new -s <session_name>
```
*Optional:* Use `--gpu T4` or `--tpu v5e1` to provision accelerators.

### 3. Verify Connectivity
Confirm the `/colab/ssh` endpoint is active before updating config. First re-derive the binary (do not reuse a stale path):

```bash
export PYTHONPATH=\"\"
COLAB_BIN=$(readlink -f $(which colab)); echo "COLAB_BIN=$COLAB_BIN"
colab ssh --help | head -n 5  # sanity: must show --proxy-mode
```

**Direct interactive shell test:**
```bash
export PYTHONPATH=\"\"
echo \"exit\" | colab --auth=adc ssh -s <session_name>
```
If this returns a `kex_exchange_identification: Connection closed` or an HTTP error:
- **404:** SSH not exposed $\rightarrow$ `colab stop` and recreate with `colab new`.
- **502:** Runtime sshd unreachable $\rightarrow$ `colab restart-kernel`.
- **429:** Another SSH session is already connected $\rightarrow$ close existing clients.
- **No such command 'ssh':** You have PyPI 0.6.0 — reinstall: `uv tool install --force mighty-colab` or `uv tool install --force git+https://github.com/googlecolab/google-colab-cli.git` then re-run `which colab; readlink -f $(which colab)` and `colab ssh --help`.

**ProxyCommand bridge test (one-shot command):**
```bash
export PYTHONPATH=\"\"
COLAB_BIN=$(readlink -f \"$(which colab)\")
ssh -o \"ProxyCommand=$COLAB_BIN ssh --proxy-mode -s <session_name>\" \\
     -o StrictHostKeyChecking=no -o UserKnownHotsFile=/dev/null \\
     -o RequestTTY=no root@colab-runtime 'pwd'
```
Verify with `ssh -G` if alias exists: `ssh -G <alias> | grep -i proxycommand` should match `echo $COLAB_BIN`.

### 4. Configure SSH Aliases
Add two hosts to `~/.ssh/config` to support both coding agents (no TTY) and interactive shells (TTY). Use the **absolute path** from `COLAB_BIN` — re-derive it after every install, do not hardcode `mighty-colab` or `google-colab-cli`:

```bash
COLAB_BIN=$(readlink -f $(which colab)); echo $COLAB_BIN
# then use that value in ~/.ssh/config:
```

```sshconfig
# === Colab SSH bridge (managed by Hermes) ===
Host colab-agent
  HostName colab-runtime
  User root
  ProxyCommand /usr/bin/env PYTHONPATH= <COLAB_BIN> ssh --proxy-mode -s <session_name>
  StrictHostKeyChecking no
  UserKnownHostsFile /dev/null
  RequestTTY no

Host colab-shell
  HostName colab-runtime
  User root
  ProxyCommand /usr/bin/env PYTHONPATH= <COLAB_BIN> ssh --proxy-mode -s <session_name>
  StrictHostKeyChecking no
  UserKnownHostsFile /dev/null
  RequestTTY yes
```
Example (today): `COLAB_BIN=/Users/rajivmehtapy/.local/share/uv/tools/mighty-colab/bin/mighty-colab`; after git install: `.../google-colab-cli/bin/colab`. Replace `<COLAB_BIN>` with the actual `readlink -f` output.

> **Critical:** the `ProxyCommand` MUST start with `/usr/bin/env PYTHONPATH=`. The Hermes terminal leaks its venv `PYTHONPATH` into child processes; the ProxyCommand inherits it and `mighty-colab` crashes with `ModuleNotFoundError: pydantic_core._pydantic_core`. The env prefix makes the alias work from VSCode and any shell.

### 5. Connect VSCode
1. Install **Remote - SSH** extension.
2. **Cmd+Shift+P** $\rightarrow$ `Remote-SSH: Connect to Host...` $\rightarrow$ select `colab-agent`.
3. Select **Linux** as the target platform.
4. Open folder `/content`.

## Pitfalls & Safety

- **PyPI 0.6.0 missing `ssh` (issue #102):** `No such command 'ssh'` means you installed `google-colab-cli` 0.6.0 from PyPI. Fix: `export PYTHONPATH="" && uv tool install --force mighty-colab` (fast) or `uv tool install --force git+https://github.com/googlecolab/google-colab-cli.git` (heavier, per https://github.com/googlecolab/google-colab-cli/issues/102#issuecomment-5384947488 — community workaround, not maintainer-confirmed). Then re-run `which colab; readlink -f $(which colab); colab ssh --help`. Until PyPI publishes `>0.6.0`, stay on `mighty-colab` or git main.
- **Binary shadowing / `which colab`:** `mighty-colab` vs `google-colab-cli` create different `~/.local/share/uv/tools/...` dirs but both provide `colab`. Always run `which -a colab; readlink -f $(which colab); uv tool list` before debugging — `which colab` chain tells you the real binary. If `which -a` shows two, `PATH` order wins; prefer one and remove the other with `uv tool uninstall <name>` if needed.
- **SIGHUP/Teardown:** Use the `--rm` flag with `colab ssh --proxy-mode` if you want the runtime to stop automatically upon disconnect.
- **Single Session Limit:** Colab restricts you to **one active SSH session per runtime**. If you have VSCode connected, a separate terminal `ssh colab-shell` will fail with HTTP 429.
- **Billing:** Runtimes bill compute units until stopped. Always run `colab --auth=adc stop -s <session_name>` when finished.
- ** Logical Host:** `root@colab-runtime` is a placeholder; the `ProxyCommand` handles the actual WebSocket routing.

## Completion Report Template
When finishing a setup, return:
- **Colab session:** `<name>`
- **Accelerator:** `<CPU/GPU/TPU>`
- **SSH alias:** `colab-agent`
- **ProxyCommand:** `<abs-path> ssh --proxy-mode -s <name>`
- **Remote workspace:** `/content`
- **Connection command:** `ssh colab-agent`
