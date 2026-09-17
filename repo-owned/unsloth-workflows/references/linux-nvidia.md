# Linux/NVIDIA setup

The supported execution shape is Linux x86_64 with an NVIDIA driver, a visible GPU, Python 3.12, and a project-local `.unsloth/venv`. `doctor` is read-only and reports platform, architecture, Python, `uv`, `nvidia-smi`, GPU names/memory/driver, and whether the host is eligible.

`setup` may create the project environment and install packages. It must not install drivers, modify an active unrelated environment, or delete an incompatible environment. Use the official automatic backend path first:

```bash
uv venv .unsloth/venv --python 3.12
uv pip install --python .unsloth/venv/bin/python unsloth --torch-backend=auto
```

If `uv` is absent, bootstrap it in `.unsloth/bootstrap`. Record versions and commands in `.unsloth/install.json`. Source: [Unsloth installation](https://unsloth.ai/docs/get-started/install/pip-install.md) and [requirements](https://unsloth.ai/docs/get-started/fine-tuning-for-beginners/unsloth-requirements.md).
