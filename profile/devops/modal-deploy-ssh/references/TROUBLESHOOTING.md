# Troubleshooting

Use these checks to identify the failure before relaunching. The lifecycle
manager uses Modal CLI 1.6.3 or newer; when it finds an older CLI, it uses
uvx if available.

## Modal CLI not found or too old

Check that `uvx` is available, or install a current Modal CLI and authenticate it
with the intended profile. `--modal` accepts an explicit current CLI path. The manager
does not upgrade the user's global installation.

## Modal authentication failure

`modal profile list` must show the intended profile/workspace. Credentials are read from
Modal's normal local configuration. Never print token files or secrets.

## SSH connection refused or timed out

1. Read `modal app list` and `modal container list`. The named app should have one
   active task/container.
2. Confirm the managed host uses the newest endpoint with
   `ssh -G <session-name>`.
3. Run `ssh -vvv <session-name>` once and preserve the connection error.
4. Check Modal function logs for sshd or tunnel startup failures.
5. Stop and report if the function or relay is gone. Correct the observed cause
   before launching again; each launch receives a new endpoint.

The SSH function keeps `modal.forward(port=22, unencrypted=True)` open while it sleeps for
the session timeout. Do not return from the function while the tunnel is needed.

## Public-key authentication failed

Confirm the managed SSH block's `IdentityFile` matches the public key passed with
`--pubkey`. The public key is passed as a function argument and written to
`/root/.ssh/authorized_keys`. Do not pass the private key to Modal.

## Persistent function does not receive the key

The local launcher and Modal function run in different processes. Do not check
`MODAL_SSH_PUBKEY1` at module import time inside the remote function. Validate it in the
local entrypoint, then pass the public key to `Function.spawn`.

## Image build failure

- Use `python:3.12-slim-bookworm`, not Debian 11 (bullseye); the old security pool
  returns 404.
- The base setup layer installs gcc before Modal's bootstrap dependencies.
  If a custom image fails building `aiohttp` with `gcc: No such file or directory`,
  move gcc installation into the base setup layer before Modal bootstraps its
  pinned packages.
- Retrieve image build details with `modal image logs <image-id>` before changing
  the image definition.

## Existing volume not found

Use `modal volume list` to inspect names. With `--existing-volume`, the manager
fails before launch if the selected name is absent and the app references the
volume without auto-creation. Never use `modal volume delete` unless the user
explicitly asks to erase that volume.

## Provisioning reports nvtop unavailable

On Debian Bookworm, `nvtop` is in the `contrib` component. If the user requires every
optional package in the provisioning summary, enable that component in the
container's apt sources before rerunning the installer. The default full
installer can report `Overall: PARTIAL` for optional packages while exiting 0;
report both the exit code and the script summary.

Provisioning downloads and installs packages, CLIs, Node, and Ollama. A warm
cached image can make allocation and SSH verification fit a three-minute
target, but the full cold provisioning run is not guaranteed to do so. For
repeat launches that need the toolchain immediately, bake reusable
dependencies into a cached image.

## Packages disappeared after a respawn

Expected for packages installed at runtime. Only the Modal volume persists.
Re-run provisioning after a new container starts, or build the reusable tools
into a cached image. To preserve the user's volume contents, run
current-directory installers from `/root` and inspect any script that writes
explicitly to `/workspace`.

## Duplicate sessions

Launching a name that already has an active task can create another app with
the same description. Check `modal app list` first. Stop a failed app by app ID
or use `modal_ssh_session.py stop --name <name>`; stopping does not delete
the volume.

## VS Code still uses an old endpoint

The manager replaces its marked SSH config block on each launch. If VS Code
retains a stale control connection, close the remote window and run:

```sh
ssh -O exit <session-name> 2>/dev/null || true
```

Then reconnect through Remote-SSH.

## macOS SSH config permissions

The manager sets `~/.ssh/config` to mode `0600`. If SSH refuses to read it, check
that it is not group/world writable.

## Windows

The manager targets macOS/Linux. Use OpenSSH in WSL2 or Git Bash and pass
`--pubkey` explicitly; VS Code Remote-SSH must use the same environment.

