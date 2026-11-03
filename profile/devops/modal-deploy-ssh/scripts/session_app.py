"""Persistent Modal SSH function used by modal_ssh_session.py."""
import os
import subprocess
import time

import modal

NAME = os.environ.get("MODAL_SSH_NAME", "g-session").strip()
CPU = float(os.environ.get("MODAL_SSH_CPU", "8"))
MEMORY = int(os.environ.get("MODAL_SSH_MEMORY", "32768"))
TIMEOUT = int(os.environ.get("MODAL_SSH_TIMEOUT", "86400"))
VOLUME = os.environ.get("MODAL_SSH_VOLUME", "").strip() or "{}-ws".format(NAME)
CREATE_VOLUME = os.environ.get("MODAL_SSH_CREATE_VOLUME", "true").lower() not in {
    "0",
    "false",
    "no",
}
PUBKEY1 = os.environ.get("MODAL_SSH_PUBKEY1", "").strip()
PUBKEY2 = os.environ.get("MODAL_SSH_PUBKEY2", "").strip()

app = modal.App(NAME)

# Install gcc in the base setup layer. Older Modal image-builder versions
# install a pinned aiohttp release while bootstrapping the image; on Python
# 3.12 that release may need a source build.
image = (
    modal.Image.from_registry(
        "python:3.12-slim-bookworm",
        setup_dockerfile_commands=[
            "RUN apt-get update && apt-get install -y --no-install-recommends gcc "
            "&& rm -rf /var/lib/apt/lists/*"
        ],
    )
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

volume = modal.Volume.from_name(VOLUME, create_if_missing=CREATE_VOLUME)


@app.function(
    image=image,
    cpu=CPU,
    memory=MEMORY,
    timeout=TIMEOUT,
    volumes={"/workspace": volume},
    env={
        "MODAL_SSH_NAME": NAME,
        "MODAL_SSH_CPU": str(CPU),
        "MODAL_SSH_MEMORY": str(MEMORY),
        "MODAL_SSH_TIMEOUT": str(TIMEOUT),
        "MODAL_SSH_VOLUME": VOLUME,
        "MODAL_SSH_CREATE_VOLUME": "true" if CREATE_VOLUME else "false",
    },
)
def persistent_ssh(
    endpoint_dict_id: str, public_key_1: str, public_key_2: str = ""
) -> None:
    """Run sshd and keep Modal's raw TCP tunnel open until the session timeout."""
    endpoint = modal.Dict.from_id(endpoint_dict_id)
    os.makedirs("/root/.ssh", mode=0o700, exist_ok=True)
    authorized_keys = [key.strip() for key in (public_key_1, public_key_2) if key.strip()]
    if not authorized_keys:
        raise RuntimeError("At least one SSH public key is required.")
    key_path = "/root/.ssh/authorized_keys"
    with open(key_path, "w") as key_file:
        key_file.write("\n".join(authorized_keys) + "\n")
    os.chmod("/root/.ssh", 0o700)
    os.chmod(key_path, 0o600)

    with open("/root/.profile", "a") as profile:
        profile.write("cd /workspace\n")

    subprocess.run(
        ["ssh-keygen", "-A"],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    sshd = subprocess.Popen(
        [
            "/usr/sbin/sshd",
            "-D",
            "-e",
            "-o",
            "PasswordAuthentication=no",
            "-o",
            "PermitRootLogin=prohibit-password",
        ]
    )
    time.sleep(1)
    if sshd.poll() is not None:
        raise RuntimeError("sshd exited before the TCP tunnel was opened.")

    with modal.forward(port=22, unencrypted=True) as tunnel:
        host, port = tunnel.tcp_socket
        endpoint["host"] = host
        endpoint["port"] = port
        print("SSH_ENDPOINT_READY host={} port={}".format(host, port), flush=True)
        time.sleep(TIMEOUT)


@app.local_entrypoint()
def main() -> None:
    if not PUBKEY1:
        raise SystemExit(
            "MODAL_SSH_PUBKEY1 is required. Pass a public key with --pubkey."
        )

    # The ephemeral Dict passes the tunnel endpoint from the running function
    # back to this short-lived launcher without creating a persistent resource.
    with modal.Dict.ephemeral() as endpoint:
        persistent_ssh.spawn(endpoint.object_id, PUBKEY1, PUBKEY2)
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            host = endpoint.get("host")
            port = endpoint.get("port")
            if host and port:
                print("SSH_READY host={} port={}".format(host, port), flush=True)
                print("SESSION_NAME={}".format(NAME), flush=True)
                print("SESSION_CPU={}".format(CPU), flush=True)
                print("SESSION_MEMORY={}".format(MEMORY), flush=True)
                print("SESSION_GPU=none", flush=True)
                return
            time.sleep(1)
        raise RuntimeError("Timed out waiting for the persistent SSH function endpoint.")
