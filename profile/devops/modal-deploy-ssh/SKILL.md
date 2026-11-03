---
name: modal-deploy-ssh
description: Use when the user wants a named Modal CPU or GPU session reachable by SSH or VS Code Remote-SSH, including launch, reconnect, provisioning, status, or stop. The session uses a long-running Modal function, a raw TCP SSH tunnel, and a persistent volume mounted at /workspace.
license: Apache-2.0
compatibility: Requires Python 3.9+, Modal CLI 1.6.3+ (or uvx to supply it), an SSH keypair, and macOS or Linux with network access to modal.com. The remote image is Debian 12 (bookworm).
metadata:
  author: rajivmehtaflex
  version: "0.2.0"
allowed-tools: Bash Read Write Edit
---

# Modal Deploy SSH

Create named Modal sessions reachable through plain SSH and VS Code Remote-SSH. A long-running Modal function starts sshd and holds a raw TCP tunnel open with `modal.forward(port=22, unencrypted=True)`. SSH encrypts the connection end to end; password authentication is disabled.

The lifecycle manager and app definition live in `scripts/` beside this file. Resolve those paths relative to the skill directory.

## Use this skill when

- The user wants a named Modal session they can SSH into.
- A Modal SSH endpoint needs to be launched or reconnected after a stop or timeout.
- The user wants VS Code Remote-SSH wired to the same stable host alias.
- The user wants a persistent Modal volume mounted at `/workspace`.

Use a browser-terminal workflow instead when the user has no SSH key or needs a browser-only terminal.

## Preflight

Before launching, check Modal authentication, the selected public key, and Python 3.9+:

```sh
modal profile list
ls ~/.ssh/id_ed25519.pub
python3 --version
```

The manager requires Modal CLI 1.6.3 or newer for the long-running function and endpoint handoff. It automatically uses `uvx --python 3.14 --from modal modal` when it finds an older CLI and `uvx` is installed. An explicit `--modal` path must also be current; the manager does not upgrade the global CLI.

## Launch

```sh
python3 scripts/modal_ssh_session.py launch --name <session-name>
```

The launch flow:

1. Checks Modal authentication, the SSH public key, and any required existing volume.
2. Runs a short local entrypoint that spawns a long-running SSH function.
3. The function starts sshd, opens the TCP tunnel, mounts the volume at `/workspace`, and waits until its timeout.
4. The launcher writes or refreshes the managed SSH block in `~/.ssh/config`.
5. The manager verifies one real SSH login by default, then reports the endpoint.

The image uses `python:3.12-slim-bookworm`. It installs gcc in the base setup layer because legacy Modal image builders can bootstrap a pinned aiohttp release that needs to compile on Python 3.12. Keep the base on Debian 12 (bookworm); Debian 11 (bullseye) package mirrors return 404s.

Default resources are 8 CPU cores, 32768 MiB memory, no GPU, and a 24-hour timeout. The default volume name is `<session-name>-ws`; it is created if missing.

| Flag | Default | Description |
|---|---|---|
| `--name` | required | Modal app and SSH alias |
| `--cpu` | `8` | CPU cores; fractional values are allowed |
| `--memory` | `32768` | Memory in MiB |
| `--gpu` | none | GPU spec such as `L4` or `H100:2` |
| `--timeout` | `86400` | Function lifetime in seconds; maximum 86400 |
| `--volume` | `<name>-ws` | Persistent volume name |
| `--existing-volume` | off | Require the selected volume to exist; never create it |
| `--pubkey` | `~/.ssh/id_ed25519.pub` | Public key to authorize |
| `--pubkey2` | none | Optional second public key |
| `--verify-attempts` | `1` | SSH checks before stopping on an error |
| `--provision` | off | Run a setup script after SSH verification |
| `--modal` | auto | Explicit current Modal CLI path |

When the user says the volume already exists and must not be created, pass both `--volume <name> --existing-volume`. The manager checks the volume list, and the app uses `Volume.from_name(..., create_if_missing=False)`.

Example with an existing volume:

```sh
python3 scripts/modal_ssh_session.py launch \
  --name g-time-exp --cpu 2 --memory 4096 \
  --volume terminal-data --existing-volume
```

## Startup time

With an already cached image and available CPU capacity, allocation plus SSH verification targets three minutes. Cold image builds can take longer. Provisioning scripts run after allocation and may download large packages or install many tools, so the complete task cannot be guaranteed within three minutes. Do not promise that duration for a cold image or arbitrary installer.

## Connect from VS Code

After a successful launch, use VS Code → Remote-SSH: Connect to Host → the session name. The same alias works from a terminal:

```sh
ssh <session-name>
```

The login shell starts in `/workspace`.

## Provisioning

`--provision` runs the script from `/root` so installers that write to their current directory do not write into the mounted volume. Provisioning output streams live; the script's exit code becomes the launch command's exit code.

```sh
python3 scripts/modal_ssh_session.py launch --name g-data-linkup --provision
```

Only `/workspace` persists across a respawn. Packages installed into the root filesystem are lost when the function ends. A provisioning script may still modify `/workspace` explicitly; inspect it first and honor any instruction to preserve volume data.

## Status and stop

```sh
python3 scripts/modal_ssh_session.py status --name <session-name>
python3 scripts/modal_ssh_session.py stop --name <session-name>
```

Stop resolves app IDs and stops every non-stopped app with that description. It removes the managed SSH block unless `--keep-config` is supplied. Stopping never deletes a volume.

## Failure handling

The default SSH verification makes one attempt. On failure, the manager prints the captured SSH error and exits without provisioning or launching another session. Inspect `ssh -vvv <session-name>` and `modal app list`, report the output, and only retry after identifying a specific cause and making a targeted correction.

If an image build fails, inspect its Modal build logs before changing the image. If provisioning exits nonzero, report the exact error and leave the session state visible; do not silently relaunch.

See [references/TROUBLESHOOTING.md](references/TROUBLESHOOTING.md) for detailed recovery steps.

## Completion report

Report all of these fields:

```text
Session: <name>
CPU/Memory: <cpu> CPU / <memory> MiB
GPU: <none | model>
Endpoint: <host>:<port>
SSH: ssh <name> (verified | failed)
VS Code: Remote-SSH -> <name>
Volume: <volume-name> at /workspace (created | existing)
Provisioning: <skipped | exit 0 | failed>
Stop: python3 scripts/modal_ssh_session.py stop --name <name>
```
