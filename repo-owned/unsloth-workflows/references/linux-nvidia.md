# Linux/NVIDIA setup

The execution environment for this skill targets Linux x86_64 with NVIDIA drivers, a visible CUDA GPU, Python 3.12, and a project-local `.unsloth/venv`.

## Hardware support

- **NVIDIA GPU Architectures**: Compute Capability 6.0+ (Pascal, Volta, Turing, Ampere, Ada Lovelace, Hopper, and Blackwell RTX 50 series / B200).
- **Specialized Architectures**: Blackwell introduces native Dynamic NVFP4 for high-throughput 4-bit inference. Multi-GPU enterprise setups include NVIDIA DGX Station and NVIDIA DGX Spark.
- **Broader Ecosystem (Discuss Mode)**: While the local automated execution runner targets Linux/NVIDIA, upstream Unsloth also supports AMD ROCm GPUs (MI300/Radeon 7900 series), Intel GPUs, Apple Silicon macOS, and Windows via Unsloth Desktop, Unsloth Studio, or Docker containers.

## Runner rules and preflight

`doctor` is strictly read-only:
- Reports operating system, CPU architecture, Python version, availability of `uv` and `nvidia-smi`.
- Queries total VRAM, GPU device names, driver versions, and evaluates execution eligibility without mutating disk state.

`setup` executes within the project directory only after `nvidia-smi` confirms a visible NVIDIA GPU:
1. Never alters system-wide drivers or touches an unrelated external environment.
2. Prefers `uv` for virtual environment creation and package installation:
   ```bash
   uv venv .unsloth/venv --python 3.12
   uv pip install --python .unsloth/venv/bin/python unsloth --torch-backend=auto
   ```
3. If `uv` is missing on the host, bootstraps a local copy inside `.unsloth/bootstrap/`.
4. Performs verification: tests imports (`unsloth`, `torch`, `transformers`, `trl`, `peft`), confirms `torch.cuda.is_available()`, executes a single-element CUDA tensor computation, and verifies dependency consistency with `pip check`.
5. Records environment versions and metadata into `.unsloth/install.json`.

Sources: [Unsloth installation](https://unsloth.ai/docs/get-started/install/pip-install.md), [requirements](https://unsloth.ai/docs/get-started/fine-tuning-for-beginners/unsloth-requirements.md), [Blackwell RTX 50 series](https://unsloth.ai/docs/blog/fine-tuning-llms-with-blackwell-rtx-50-series-and-unsloth.md), [NVIDIA DGX Spark](https://unsloth.ai/docs/blog/fine-tuning-llms-with-nvidia-dgx-spark-and-unsloth.md), [AMD GPU guide](https://unsloth.ai/docs/get-started/install/amd.md).
