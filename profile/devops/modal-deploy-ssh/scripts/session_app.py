"""Modal app template used by modal-deploy-ssh.

Normally launched through `modal_ssh_session.py launch`, which sets the
MODAL_SSH_* environment variables below. It can also be run directly:

    MODAL_SSH_NAME=g-demo MODAL_SSH_PUBKEY1="$(cat ~/.ssh/id_ed25519.pub)" \
        modal run --detach session_app.py

The sandbox runs sshd on port 22 and asks Modal for an unencrypted (raw TCP)
port forward, which is what makes direct SSH possible. The SSH protocol
encrypts the connection end-to-end; only the TCP endpoint is public, and
password authentication is disabled.

Environment variables:
    MODAL_SSH_NAME       App/session name (default: g-session)
    MODAL_SSH_CPU        CPU cores, float allowed (default: 8)
    MODAL_SSH_MEMORY     Memory in MiB (default: 32768)
    MODAL_SSH_GPU        GPU spec, e.g. "L4", "H100:2"; empty = CPU-only
    MODAL_SSH_TIMEOUT    Sandbox lifetime in seconds (default: 86400)
    MODAL_SSH_VOLUME     Persistent volume name (default: <name>-ws)
    MODAL_SSH_PUBKEY1    Required SSH public key (authorized_keys)
    MODAL_SSH_PUBKEY2    Optional second SSH public key
"""
import os

import modal

NAME = os.environ.get("MODAL_SSH_NAME", "g-session").strip()
CPU = float(os.environ.get("MODAL_SSH_CPU", "8"))
MEMORY = int(os.environ.get("MODAL_SSH_MEMORY", "32768"))
GPU = os.environ.get("MODAL_SSH_GPU", "").strip() or None
TIMEOUT = int(os.environ.get("MODAL_SSH_TIMEOUT", "86400"))
VOLUME = os.environ.get("MODAL_SSH_VOLUME", "").strip() or "{}-ws".format(NAME)
PUBKEY1 = os.environ.get("MODAL_SSH_PUBKEY1", "").strip()
PUBKEY2 = os.environ.get("MODAL_SSH_PUBKEY2", "").strip()

if not PUBKEY1:
    raise SystemExit(
        "MODAL_SSH_PUBKEY1 is required. Set it to the contents of an SSH "
        "public key, e.g. MODAL_SSH_PUBKEY1=\"$(cat ~/.ssh/id_ed25519.pub)\"."
    )

app = modal.App(NAME)

image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install(
        "openssh-server",
        "curl",
        "wget",
        "git",
        "zstd",
        "unzip",
        "tmux",
        "procps",
        "ca-certificates",
    )
    .run_commands("mkdir -p /run/sshd")
)

volume = modal.Volume.from_name(VOLUME, create_if_missing=True)

STARTUP_SCRIPT = """
set -eu
mkdir -p /root/.ssh
echo "$SSH_PUBLIC_KEY" >> /root/.ssh/authorized_keys
if [ -n "${SSH_PUBLIC_KEY_2:-}" ]; then
  echo "$SSH_PUBLIC_KEY_2" >> /root/.ssh/authorized_keys
fi
chmod 700 /root/.ssh
chmod 600 /root/.ssh/authorized_keys
echo "cd /workspace" >> /root/.profile
/usr/sbin/sshd -D -e
"""


@app.local_entrypoint()
def main():
    sandbox = modal.Sandbox.create(
        *("sh", "-c", STARTUP_SCRIPT),
        app=app,
        image=image,
        cpu=CPU,
        memory=MEMORY,
        gpu=GPU,
        timeout=TIMEOUT,
        volumes={"/workspace": volume},
        unencrypted_ports=[22],  # raw TCP relay: the SSH path
        secrets=[
            modal.Secret.from_dict(
                {"SSH_PUBLIC_KEY": PUBKEY1, "SSH_PUBLIC_KEY_2": PUBKEY2}
            )
        ],
    )
    hostname, port = sandbox.tunnels(timeout=600)[22].tcp_socket

    # Machine-readable lines consumed by modal_ssh_session.py.
    print("SSH_READY host={} port={}".format(hostname, port), flush=True)
    print("SESSION_NAME={}".format(NAME), flush=True)
    print("SESSION_GPU={}".format(GPU or "none"), flush=True)
    print(
        "ssh -p {} root@{}".format(port, hostname),
        flush=True,
    )
