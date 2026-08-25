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
    .apt_install("curl")
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
