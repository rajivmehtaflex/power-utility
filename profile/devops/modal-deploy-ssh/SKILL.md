---
name: modal-deploy-ssh
description: Launch, reconnect to, and tear down named Modal cloud sessions with direct SSH access, then wire them into VS Code Remote-SSH automatically. Use when the user asks to create, start, relaunch, or destroy a Modal VM/session (often named g-* like g-data-linkup), to connect VS Code or another editor to a Modal instance, to SSH into a Modal container, or to run a CPU or GPU session on Modal. Also use when a Modal session's SSH connection stopped working after a restart, or when the user wants a persistent cloud dev box with a volume. The skill rewrites ~/.ssh/config on every respawn, so the SSH alias and VS Code connection name never change.
license: Apache-2.0
compatibility: Requires Python 3.9+, an authenticated Modal CLI (modal profile list succeeds), an SSH keypair in ~/.ssh, and macOS or Linux with network access to modal.com. The remote container runs Debian 12 (bookworm).
metadata:
  author: rajivmehtaflex
  version: "0.1.0"
allowed-tools: Bash Read Write Edit
---

# Modal Deploy SSH

Create named Modal cloud sessions that you can reach with plain `ssh`, VS Code
Remote-SSH, or any SSH-based tool. Modal containers have no public IP; this
skill opens a raw TCP relay to an in-container sshd (`unencrypted_ports=[22]`)
and authorizes your key. SSH encrypts the connection end to end and password
auth is disabled, so only key holders get in.

Everything lives in two scripts next to this file. Resolve paths relative to
this skill directory (not the user's working directory):

- `scripts/modal_ssh_session.py` — lifecycle manager (launch / stop / status)
- `scripts/session_app.py` — the Modal app the manager launches

## When to use this skill

Use it when the user wants:

- a named Modal session/VM they can SSH into (names like `g-data-linkup`)
- to connect VS Code to a Modal instance over SSH
- to relaunch or resize a session after it stopped
- a persistent cloud dev box backed by a Modal volume

Do **not** use it when the user needs a browser-only terminal with no SSH key
on the device, or is behind a firewall that blocks arbitrary TCP ports. The
web-terminal + `code tunnel` flow from the `modal-deploy` skill covers those
cases; read `modal-deploy` instead if it is installed.

## Pre-flight

Run these checks before launching. If any fails, stop and report the fix.

```sh
modal profile list          # must list a profile/workspace
ls ~/.ssh/id_ed25519.pub    # or pass --pubkey with another key
python3 --version           # 3.9 or newer
```

If `modal` is not on `PATH`, the manager searches common install locations
(`~/Library/Python/3.*/bin/modal`, `~/.local/bin/modal`, Homebrew). Point it
explicitly with `--modal /path/to/modal` if needed.

## Launch

```sh
python3 scripts/modal_ssh_session.py launch --name <session-name>
```

The manager:

1. verifies Modal auth, the public key, and the CLI;
2. runs `modal run --detach scripts/session_app.py` (the sandbox survives the
   local process exiting);
3. parses `SSH_READY host=... port=...` from the launch output;
4. writes or replaces the managed block in `~/.ssh/config`;
5. verifies with a real `ssh` login and prints the endpoint.

Default resources: 8 CPU, 32 GB RAM, no GPU, 24 h timeout, volume
`<name>-ws` mounted at `/workspace`. Override per session:

| Flag | Default | Notes |
|---|---|---|
| `--cpu` | `8` | float allowed |
| `--memory` | `32768` | MiB |
| `--gpu` | none | `L4`, `A10`, `H100`, `H100:2`, ... |
| `--timeout` | `86400` | seconds; the sandbox stops at expiry |
| `--volume` | `<name>-ws` | created if missing; never auto-deleted |
| `--pubkey` | `~/.ssh/id_ed25519.pub` | key authorized in the container |
| `--pubkey2` | none | optional second key |
| `--provision` | off | run a setup script after launch (see below) |
| `--modal` | auto | explicit modal CLI path |

GPU examples:

```sh
# Cost-optimised CPU box
python3 scripts/modal_ssh_session.py launch --name g-data-linkup

# L4 for a 24 GB workload
python3 scripts/modal_ssh_session.py launch --name g-train --gpu L4

# Two GPUs, longer lifetime, larger disk-backed volume
python3 scripts/modal_ssh_session.py launch --name g-big --gpu H100:2 \
  --cpu 32 --memory 65536 --timeout 172800 --volume g-big-ws
```

Scarce GPUs (H100, H200, B200) can queue for several minutes; a failed
allocation returns a non-zero exit with the Modal log tail. Try `L4`/`A10`
first when the user has no hard requirement.

## Connect from VS Code

After launch, the host alias is already in `~/.ssh/config`:

1. VS Code → Remote-SSH: Connect to Host → pick the session name.
2. No password prompt: the key is authorized and `IdentityFile` is set.
3. The remote workspace root is `/workspace` (persistent volume).

The same alias works for the CLI: `ssh <session-name>`.

## Provisioning (optional)

`--provision` runs a shell script on the VM after SSH verification:

```sh
# With the maintainer's default script (installs VS Code CLI, Ollama, dev tools)
python3 scripts/modal_ssh_session.py launch --name g-data-linkup --provision

# With a custom script
python3 scripts/modal_ssh_session.py launch --name g-data-linkup \
  --provision https://example.com/setup.sh
```

The command executed remotely is `cd /workspace && curl -fsSL <url> | bash`.
Provisioning output streams live and its exit code becomes the command's exit
code. **Installed system packages live in the container's ephemeral rootfs** —
they are gone on the next respawn. Only `/workspace` (the volume) persists.
Re-run `--provision` after every relaunch.

## Respawn and lifecycle

A Modal sandbox gets a new relay host and port every time it starts. The
manager rewrites the block between

```text
# BEGIN modal-deploy-ssh: <name>
...
# END modal-deploy-ssh: <name>
```

so the SSH alias, VS Code connection name, and commands stay the same. A
relaunch with the same `--name` therefore needs no manual config edits:
launch again, reconnect in VS Code.

The sandbox also stops at `--timeout` (default 24 h) or when the Modal app is
stopped. Data in the volume survives; processes and installed packages do not.

## Status and stop

```sh
python3 scripts/modal_ssh_session.py status --name <session-name>
python3 scripts/modal_ssh_session.py stop --name <session-name>
```

`stop` resolves the app ID through `modal app list --json` and calls
`modal app stop <app-id>` for every non-stopped app with that description.
Stopping by app name alone does not work for detached run-apps. It then
removes the managed SSH block (`--keep-config` preserves it).

`stop` never deletes the volume. Only remove a volume when the user
explicitly asks, using `modal volume delete <name>`.

## Pitfalls

- **Stop by app ID.** Detached `modal run` apps are ephemeral; `modal app stop
  <name>` reports "Could not find a deployed app". Always resolve the ID.
- **New endpoint every launch.** Expect a new `HostName`/`Port`; the managed
  config block handles it. Never hand-edit the block.
- **Ephemeral rootfs, persistent volume.** System packages, Node, Python
  venvs outside `/workspace`, and running processes vanish on respawn.
  Re-provision after relaunch.
- **The endpoint is public but key-only.** `PasswordAuthentication` is off and
  only the authorized keys can log in. Do not paste private keys into the
  container.
- **Image choice.** The app uses Debian 12 (bookworm). Avoid basing new images
  on Debian 11 (bullseye): its security pool is purged and `apt` 404s.
- **Cost.** Roughly $0.6/h for 8 CPU + 32 GB, about $1.6/h with an L4. Idle
  sessions still bill until the timeout. Stop sessions when done.
- **One session per name.** Launching the same name twice creates a duplicate
  app. Run `stop --name X` first when relaunching.

More detail and recovery procedures: [references/TROUBLESHOOTING.md](references/TROUBLESHOOTING.md).

## Completion report

When the work is done, report in this shape:

```text
Session: <name>
GPU: <none | model>
Endpoint: <host>:<port>
SSH: ssh <name>
VS Code: Remote-SSH -> <name>
Volume: <name>-ws (persistent at /workspace)
Provisioning: <skipped | exit 0 | failed>
Stop: python3 scripts/modal_ssh_session.py stop --name <name>
```
