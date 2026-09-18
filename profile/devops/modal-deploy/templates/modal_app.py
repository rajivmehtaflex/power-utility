import modal
import os
import sys
from dotenv import load_dotenv
import config

load_dotenv()

app = modal.App("modal-web-terminal")  # <-- Change this

# Optimized image with mount filtering
image = (
    modal.Image.debian_slim()
    # bullseye is EOL (Aug 2026): security pool purged upstream, so bare
    # .apt_install 404s. Repoint at archive.debian.org, then update+install.
    # Full recipe + rationale: SKILL.md -> bullseye pitfall (v3.5.3).
    .run_commands(
        "printf 'deb http://archive.debian.org/debian bullseye main\\n"
        "deb http://archive.debian.org/debian bullseye-updates main\\n' > /etc/apt/sources.list",
        "apt-get -o Acquire::Check-Valid-Until=false update -qq",
        "apt-get -o Acquire::Check-Valid-Until=false install -y --no-install-recommends curl git zstd openssh-client",
        "rm -rf /var/lib/apt/lists/*",
    )  # keep ALL .add_local_* calls LAST
    .pip_install("fastapi", "uvicorn", "python-dotenv")
    .add_local_dir(
        ".",
        remote_path="/root",
        ignore=[
            ".git",
            ".venv",
            "__pycache__",
            "*.pyc",
            "*.pyo",
            "docs/",
            "*.md",
            "uv.lock",
            ".env",
        ]
    )
)

# Parse resource configuration from config.py
cpu = config.CPU
memory = config.MEMORY
gpu_count = config.GPU_COUNT
gpu_model = config.GPU_MODEL
timeout = config.TIMEOUT
volume_name = config.VOLUME_NAME

# Build GPU config string
gpu_config = None
if gpu_count > 0:
    if gpu_model:
        gpu_config = f"{gpu_model}:{gpu_count}"
    else:
        gpu_config = str(gpu_count)

# Configure persistent volumes if specified
volumes = {}
if volume_name:
    volumes["/workspace"] = modal.Volume.from_name(volume_name, create_if_missing=True)

@app.function(
    image=image,
    cpu=cpu,
    memory=memory,
    gpu=gpu_config,
    volumes=volumes,
    scaledown_window=300,
    timeout=timeout
)
@modal.asgi_app()
def fastapi_app():
    sys.path.append("/root")
    os.chdir("/root")
    from main import app as fastapi_instance
    return fastapi_instance
