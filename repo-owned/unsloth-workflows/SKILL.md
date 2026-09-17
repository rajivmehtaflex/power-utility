---
name: unsloth-workflows
description: Explain, prepare, and execute Unsloth model training workflows on Linux/NVIDIA machines. Use for Unsloth environment setup, datasets, SFT, LoRA/QLoRA, CPT, preference/RL training, multimodal models, evaluation, export, quantization, and local serving.
license: Apache-2.0
compatibility: Requires a Linux shell for execution; training requires NVIDIA drivers, a visible CUDA GPU, Python 3.12, network access for package/model downloads, and enough disk/VRAM for the selected model. Discuss and dry-run modes are CPU/read-only.
metadata:
  version: "1.0.0"
  author: rajivmehtaflex
  source: "https://unsloth.ai/docs/llms.txt"
  execution_platform: linux-nvidia
---

# Unsloth Workflows

Use this skill as a framework guide and a shell workflow runner. Keep three modes distinct:

- **Discuss:** explain concepts or inspect a request. Do not install, write files, download models, or train.
- **Prepare:** create reviewable configuration or task-specific scripts. Do not install dependencies or start GPU work.
- **Execute:** perform the requested operation after preflight. Installation and model downloads are side effects and must be limited to the selected project.

## Route a request

1. Identify the objective: domain adaptation (continued pretraining), examples-to-behavior (SFT), preferences (DPO/ORPO/KTO), reward-driven behavior (GRPO/RL), embeddings, vision, speech, or inference/export.
2. Identify the adaptation method independently: full fine-tuning, LoRA, or QLoRA.
3. Inspect model family, revision, modality, chat template, dataset schema, sequence length, GPU memory, and desired output format.
4. For Discuss, use the references without running commands. For Prepare, create a JSON config and conversion script. For Execute, run the command below from this skill directory.

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

Execution targets Linux/NVIDIA only. `setup` owns `.unsloth/` inside the selected project, prefers `uv`, creates a Python 3.12 environment at `.unsloth/venv`, installs Unsloth with the automatic PyTorch backend, and records an install marker. It reuses a passing environment and never replaces system drivers or an unrelated active environment. If the host is unsupported, report the exact platform and recovery path.

## Evidence and safety

Report these separately: configuration validated, environment verified, training completed, evaluation completed, and export reloaded successfully. Preserve the model name/revision, dataset paths and hashes, tokenizer/template, dependency versions, training settings, logs, checkpoints, and artifact paths. Never silently change model, method, precision, chat template, or evaluation split after an error.

Read only the reference needed for the current request:

- [framework-map.md](references/framework-map.md) for the mental model and method selection.
- [linux-nvidia.md](references/linux-nvidia.md) for setup and capability checks.
- [data-and-templates.md](references/data-and-templates.md) for schemas, templates, and masking.
- [training.md](references/training.md) for SFT, LoRA/QLoRA, CPT, and checkpoints.
- [rl-and-specialized.md](references/rl-and-specialized.md) for preferences, RL, vision, speech, embeddings, and MoE.
- [efficiency-and-scale.md](references/efficiency-and-scale.md) for precision, packing, long context, and multi-GPU.
- [evaluation-and-serving.md](references/evaluation-and-serving.md) for evaluation, export, quantization, inference, and troubleshooting.

The references summarize the official map at [Unsloth documentation](https://unsloth.ai/docs/llms.txt). They distinguish upstream-documented behavior, local detection, and smoke-tested behavior; do not present an untested combination as verified.
