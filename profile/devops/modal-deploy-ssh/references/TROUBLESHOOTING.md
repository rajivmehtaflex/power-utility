# Troubleshooting

Recovery procedures for common failures. Each item states the symptom, the
cause, and the fix. These were verified against Modal CLI 1.2.6 on
2026-10-17.

## `modal: command not found`

The manager searches `PATH`, then `~/Library/Python/3.*/bin/modal`,
`~/.local/bin/modal`, `/usr/local/bin/modal`, and `/opt/homebrew/bin/modal`.
If your install is elsewhere:

```sh
python3 scripts/modal_ssh_session.py launch --name g-demo --modal /path/to/modal
```

Install Modal with `pip install modal` or `uv tool install modal`, then run
`modal setup` once.

## "Token missing. Could not authenticate client."

`modal profile list` exists but no profile is active, or the token was
removed. Re-run `modal setup`. Check for multiple accounts:

```sh
modal profile list
modal profile activate <profile>
```

Credentials live in `~/.modal.toml`. Do not print the secret value in logs.

## `Could not find a deployed app named '<name>'`

Detached `modal run` apps are ephemeral, not deployed, so `modal app stop
<name>` cannot resolve them. Resolve the app ID first:

```sh
modal app list --json
modal app stop <app-id>
```

`modal_ssh_session.py stop --name <name>` does this automatically.

## SSH connection refused or times out

1. Confirm the app is still running: `modal app list` (state should not be
   `stopped`).
2. Confirm the relay endpoint is current: `status --name <name>` and compare
   with the app's launch output.
3. Retry after a few seconds. Relay DNS can lag briefly after allocation.
4. Check verbose output:

   ```sh
   ssh -vvv <name>
   ```

5. If the app restarted, the old `HostName`/`Port` are dead. Re-run `launch
   --name <name>`; the managed block is rewritten.

## Permission denied (publickey)

- The container authorizes the key passed at launch (`--pubkey`, default
  `~/.ssh/id_ed25519.pub`). Confirm the config block's `IdentityFile` points
  at the matching private key.
- If the key was generated after the launch, relaunch with `--pubkey`.
- `ssh-add -l` shows what the agent offers. Prefer explicit `IdentityFile`
  over agent-only auth in containers.

## `WARNING: private key ... not found next to the public key`

The public key exists but its private half does not (for example a key copied
from another machine). Either copy the private key to `~/.ssh/`, use a keypair
that exists locally via `--pubkey`, or rely on the SSH agent.

## `modal run` fails during image build

- The template builds from `debian_slim(python_version="3.12")` (Debian 12,
  bookworm). Do not switch the base to Debian 11 (bullseye): its security
  package pool was purged after EOL and `apt` returns 404s.
- If a package name is unavailable, remove it from the `apt_install` list.
  Required packages are only `openssh-server`; the rest are conveniences.
- Build logs are printed by `modal run`; the failing layer is named.

## GPU allocation takes forever

H100/H200/B200 have limited capacity. `modal run` waits in the allocation
queue; L4/T4/A10 are usually fast. Use a fallback list in a custom app
(`gpu=["H100", "A100-40GB:2", "L4"]`) or deploy CPU-only while waiting.

If a GPU deploy is stuck, cancel it and check with:

```sh
modal app list
modal app logs <app-id>
```

## Installed packages disappeared after relaunch

Expected. Only the volume at `/workspace` persists. System packages, Node,
Python environments outside `/workspace`, and running services live in the
ephemeral container root filesystem. Re-run `--provision` after each launch.

To persist tool state across relaunches, write it under `/workspace` and point
the tool at that path (for example `NVM_DIR=/workspace/.nvm`).

## Volume data is missing

- Confirm the same `--volume` name is used. A new name creates a new empty
  volume.
- Confirm the path is `/workspace` inside the container.
- List the volume from the host:

  ```sh
  modal volume list
  modal volume ls <volume>
  ```

Never run `modal volume delete` unless the user explicitly asked for the data
to be erased.

## VS Code Remote-SSH still points at the old host

VS Code caches host details and an SSH ControlMaster socket can hold the old
connection. Close the remote window, then:

```sh
ssh -O exit <name> 2>/dev/null || true
```

Reconnect. If it persists, run the VS Code command "Remote-SSH: Kill VS Code
Server on Host" and reconnect.

## Duplicate sessions

Launching the same name twice creates two apps with the same description. Both
bill until stopped. `stop --name <name>` stops every non-stopped app with that
description. Check first with `status`.

## macOS: SSH config permissions

`~/.ssh/config` must not be group/world writable. The manager sets `0600` when
it writes the file. If SSH refuses to read it:

```sh
chmod 600 ~/.ssh/config
```

## Windows

The manager targets macOS/Linux. On Windows, use OpenSSH in WSL2 or Git Bash
and pass `--pubkey` explicitly; VS Code Remote-SSH reads the same
`~/.ssh/config` inside WSL if launched there.
