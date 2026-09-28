---
name: unsloth-workflows
description: Explain, prepare, and execute Unsloth workflows on Linux/NVIDIA machines. Covers Unsloth Studio/Desktop, environment setup, datasets/Data Recipes, SFT, LoRA/QLoRA/QAT, CPT, GRPO/GSPO/RL, multimodal models, evaluation, export, Dynamic 3.0 GGUFs, and local/agent serving (OpenAI/Anthropic APIs, Claude Code, Hermes Agent).
license: Apache-2.0
compatibility: Requires a Linux shell for execution; training requires NVIDIA drivers, a visible CUDA GPU, Python 3.12, network access for package/model downloads, and enough disk/VRAM for the selected model. Discuss and dry-run modes are CPU/read-only.
metadata:
  version: "1.1.0"
  author: rajivmehtaflex
  source: "https://unsloth.ai/docs/llms.txt"
  execution_platform: linux-nvidia
---

# Unsloth Workflows

Use this skill as a framework guide and a shell workflow runner. Keep three modes distinct:

- **Discuss:** explain concepts, explore models, or inspect a request. Covers Unsloth Studio/Desktop, cross-platform hardware, and agent runtimes. Do not install, write files, download models, or train.
- **Prepare:** create reviewable configuration or task-specific scripts (e.g. custom RL reward functions, Data Recipes, multimodal pipelines). Do not install dependencies or start GPU work.
- **Execute:** perform the requested operation after preflight. Installation and model downloads are side effects and must be limited to the selected project.

## Route a request

1. **Identify the objective**: domain adaptation (CPT), supervised demonstrations (SFT), preferences (DPO/ORPO/KTO/SimPO), reinforcement learning (GRPO/GSPO/Agent RL), quantization-aware training (QAT), multi-token prediction (MTP), multimodal (vision/audio), embeddings, or serving/export.
2. **Identify parameter method and precision**: full fine-tuning, LoRA, QLoRA, FP8, or Dynamic NVFP4.
3. **Inspect inputs and targets**: model family/revision, chat/tool template, dataset schema, sequence length (up to 500K context), GPU memory, and target runtime (vLLM, GGUF, local API, Claude Code, Hermes Agent).
4. **Select mode**:
   - For **Discuss**, use the references and live documentation queries without modifying disk state.
   - For **Prepare**, author reviewable JSON configs and adaptation scripts.
   - For **Execute**, run the runner commands below from this skill directory.

## Runner

```bash
python scripts/unsloth_workflow.py doctor --project .
python scripts/unsloth_workflow.py setup --project .
python scripts/unsloth_workflow.py validate-data --dataset data/train.jsonl
python scripts/unsloth_workflow.py train --project . --config run.json --dry-run
python scripts/unsloth_workflow.py train --project . --config run.json
python scripts/unsloth_workflow.py evaluate --project . --config run.json
python scripts/unsloth_workflow.py export --project . --config run.json
```

The runner lives in `scripts/`. The reusable text path accepts ChatML `messages` records or Alpaca `instruction`/`input`/`output` records. Its configuration is strict: unknown keys and invalid methods fail before installation or GPU work. Use `--dry-run` to inspect a resolved operation; it must not create an environment, output directory, or downloaded artifact.

## Environment rules

Execution targets Linux/NVIDIA only. `setup` first requires a visible NVIDIA GPU, then owns `.unsloth/` inside the selected project, prefers `uv`, creates a Python 3.12 environment at `.unsloth/venv`, installs Unsloth with the automatic PyTorch backend, and proves imports, dependency consistency, CUDA availability, and a small CUDA computation before recording version evidence. It reuses only a verified environment and never replaces system drivers or an unrelated active environment.

## Evidence and safety

Report these separately: configuration validated, environment verified, training completed, evaluation completed, and export reloaded successfully. Preserve the model name/revision, dataset paths and hashes, tokenizer/template, dependency versions, training settings, logs, checkpoints, and artifact paths. Never silently change model, method, precision, chat template, or evaluation split after an error.

Read only the reference needed for the current request:

- [framework-map.md](references/framework-map.md) for the mental model, ecosystem components, and dynamic documentation queries.
- [linux-nvidia.md](references/linux-nvidia.md) for setup, NVIDIA architectures (including Blackwell/NVFP4), and capability checks.
- [data-and-templates.md](references/data-and-templates.md) for schemas, Data Recipes, tool calling, and loss masking.
- [training.md](references/training.md) for SFT, LoRA/QLoRA, QAT, 500K context, MTP, kernels + packing, and checkpoints.
- [rl-and-specialized.md](references/rl-and-specialized.md) for preferences, GRPO, GSPO, VLM RL, Agent RL, reward hacking mitigations, and 12x MoE.
- [efficiency-and-scale.md](references/efficiency-and-scale.md) for Dynamic 3.0 GGUFs, 1.58-bit quants, NVFP4, and multi-GPU DDP.
- [evaluation-and-serving.md](references/evaluation-and-serving.md) for evaluation, export, local OpenAI/Anthropic APIs, coding agent integrations, and mobile ExecuTorch.

The references summarize the official map at [Unsloth documentation](https://unsloth.ai/docs/llms.txt). They distinguish upstream-documented behavior, local detection, and smoke-tested behavior; do not present an untested combination as verified.
