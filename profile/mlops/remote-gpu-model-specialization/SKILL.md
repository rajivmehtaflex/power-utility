---
name: remote-gpu-model-specialization
description: Use for SSH GPU model specialization workflows.
license: MIT
metadata:
  author: Hermes Agent
  hermes_related_skills: mlops/pi-model-specialization-orchestration, mlops/llm-agent-lifecycle, devops/cli-tool-installation
  hermes_tags: SSH, GPU, distillation, SFT, GRPO, HF, resumability, Pi
  platforms: linux, macos
  version: 1.0.0
---

# Remote GPU Model Specialization

Use this skill when a Pi extension or coding agent must run a staged model-specialization workflow on a manually provisioned, SSH-accessible Linux GPU machine rather than inside the current chat session or a Modal job.

The control plane is the Pi extension and its phase ledger. The remote SSH host is the compute plane. Hugging Face Git/LFS is the durable recovery store. GitHub stores source code. The workflow must survive GPU-machine loss by checkpointing state and artifacts before and during every long phase.

## Core decisions

- Treat the SSH host as provider-neutral. Do not hard-code Modal commands or assume a cloud-specific volume API.
- Require Linux x86_64, Bash 5.x, GNU utilities, NVIDIA `nvidia-smi`, persistent storage, and outbound access to GitHub/Hugging Face and the teacher endpoint.
- Run teacher and student sequentially on one host by default: generate/verify teacher data, stop or unload the teacher, then load/train/evaluate the student.
- Use an OpenAI-compatible llama.cpp endpoint or `llama-server` for the teacher. Ollama is not part of this workflow and must not be used as a fallback.
- Use a trainable Transformers checkpoint for the student. Do not attempt to train a GGUF file directly.
- Use response-level offline distillation/SFT first. Teacher and student do not need to be resident simultaneously. GRPO may require a student policy plus a frozen reference model, but not the teacher.
- Never execute model-generated shell scripts on the development Mac. Run candidate scripts only in a disposable Linux sandbox with hidden fixtures and verifiers.

## Repository topology

Use two explicit repositories unless the user chooses a different topology:

```text
GitHub: rajivmehtaflex/pi-shell-specialization
  source, tests, workers, docs, extension code

Hugging Face: rajivmehtapy/pi-shell-specialization
  state/phase-ledger.json
  state/artifact-manifest.json
  state/resume.json
  prompts, verified JSONL, reports, model metadata, Git-LFS weights/revisions
```

A normal remote checkout might be:

```text
/workspace/pi-shell-specialization/
/workspace/pi-shell-specialization-state/
/workspace/models/
/workspace/checkpoints/
```

Do not put tokens in remotes, files, logs, ledgers, or prompts. Use `gh`/HF login state or runtime secret injection.

## Required preflight

Before implementation or live phases, collect non-secret values:

```text
provider and image/OS
SSH host/user/port or provider connection command
GPU model and VRAM
CPU cores and system RAM
persistent disk size and mount path
Python/uv/Node versions
GitHub and HF repository URLs
teacher base URL/model name
student model ID/revision
SFT/GRPO configuration
```

Recommended minimums for a 27B quantized teacher plus 9B student workflow:

```text
Linux x86_64
L4 24 GB or better
8 CPU cores
32 GB system RAM minimum; 64 GB preferred
100 GB persistent disk minimum; 120 GB preferred
Bash 5.x + GNU userland
CUDA-visible NVIDIA driver
```

Sixteen GB system RAM may be sufficient for limited inference but is not an acceptable default gate for the complete SFT/data/checkpoint workflow; stop and report the shortfall instead of silently reducing the plan.

Verify the remote route before claiming that the agent can continue there:

```bash
pwd
nvidia-smi
git -C /workspace/pi-shell-specialization status --short
git -C /workspace/pi-shell-specialization-state status --short
hf auth whoami
gh auth status
```

An instance name alone is not SSH access. Require the generated host/user/port/key configuration or a connected remote backend. Never ask the user to paste a private key or token into chat.

## Environment setup order

1. Verify SSH access, OS, architecture, GPU, RAM, disk, and persistent mount.
2. Install/verify Bash, GNU coreutils/findutils, `git`, `git-lfs`, `curl`, `jq`, `rsync`, `cmake`, `gh`, `uv`, and Node/npm as needed.
3. Create isolated control, training, and serving Python environments. Keep vLLM separate from training dependencies when pins conflict.
4. Clone/pull the GitHub code repository and HF durable-state repository.
5. Verify GitHub account/remote and HF write access without printing credentials.
6. Verify the exact teacher endpoint/model and the exact trainable student checkpoint/revision.
7. Record SFT/GRPO defaults in non-secret workflow configuration.
8. Run the local package tests/build on the remote checkout.
9. Run one dry-run before any real teacher, GPU, script execution, or push.
10. Run one external Linux live smoke only after the dry-run passes.

## Model residency by phase

```text
P0 baseline:       student only
P2.0/P2.1 data:    teacher only or teacher endpoint
P2.2 audit:        no model required
P2.3 SFT:          student base + LoRA adapter
P2.5 evaluation:  base and trained student in separate runs
P2.6 GRPO:         student policy + frozen reference; no teacher
P2.7 serving:      final student only
```

If the teacher is served on the same GPU, stop/unload it before student training. A separate teacher endpoint is optional, not required.

## Phase ledger and checkpoint transaction

Every phase must have a typed status:

```text
pending | working | done | failed | blocked | interrupted
```

Record at least:

```text
execution mode: dry-run/live
attempt number
remote job/process ID
input cursor and total inputs
last checkpoint/batch ID
artifact paths and SHA-256 hashes
GPU seconds and estimated/actual cost
GitHub/HF commit and model revision
next action and error details
```

Use this transaction for every durable boundary:

```text
1. write status=working atomically
2. commit/push before launching work
3. record remote process/job ID immediately
4. after each durable batch, append artifacts atomically, hash, update cursor, commit/push
5. validate the phase gate
6. write status=done, hashes, revision, and next action
7. commit/push completion state
```

No unpushed local file is recoverable after host loss. Never mark a phase done merely because a process exited zero; verify artifacts and gates first.

## Resume procedure after host loss

On a replacement SSH host:

```text
clone/pull GitHub code
clone/pull HF state
verify branch/remotes/Git-LFS/auth
read phase-ledger.json
verify every referenced artifact hash
poll any saved remote process/job ID
mark stale working-without-ID as interrupted
skip done phases
resume from inputCursor/lastCheckpoint
never regenerate completed IDs
```

Use deterministic IDs, append-only batch artifacts, atomic file replacement, and deduplication by task ID. See `references/ssh-gpu-resume.md` for restart cases and the exact recovery matrix.

## Pi implementation boundaries

The remote environment does not by itself complete the package. The package still needs:

```text
central orchestrator and phase gates
shell_specialization_* Pi tools
in-process phase dashboard
SSH/provider-neutral resume bootstrap
real remote process executor
SFT/evaluation/GRPO/serve workers
HF checkpoint integration
```

Keep these as modules. Do not make `src/index.ts` a monolith. Keep deterministic gates outside the LLM: schema validation, safety checks, hidden verification, hashing, split/leakage checks, cost limits, and checkpoint policy.

## Dry-run and live gates

Dry-run must use fake teacher/remote/Git adapters and one prompt:

```text
network calls = 0
GPU jobs = 0
teacher calls = 0
remote pushes = 0
all phase transitions simulated
```

The first live SSH smoke must use one prompt and one verified answer. Execute the generated script only inside the disposable Linux sandbox. Push the checkpoint before proceeding to the full dataset.

Do not claim model specialization success until a real held-out evaluation demonstrates improvement over the base student without unacceptable regression.

## Pitfalls

- Treating Modal as mandatory after the user selected an SSH GPU provider.
- Treating a Lightning Studio/instance name as a complete SSH connection.
- Accepting 16 GB system RAM for a full 27B-teacher/9B-training workflow without an explicit reduced-scope decision.
- Loading teacher and student simultaneously when offline response-level SFT is sufficient.
- Using Ollama as an implicit fallback; the intended teacher transport is llama.cpp/OpenAI-compatible HTTP.
- Running generated scripts on the Mac.
- Storing state only on the VM’s ephemeral disk.
- Waiting until a long phase ends before pushing its cursor and artifacts.
- Writing model weights into ordinary Git history instead of Git LFS/HF revisions.
- Mixing macOS/BSD and Linux/GNU shell semantics without a dialect field.
- Declaring dry-run artifacts or simulated metrics to be real model results.

## Verification checklist

- [ ] SSH route and remote working directory are verified.
- [ ] GPU/CUDA/Bash/GNU/disk/RAM gates pass.
- [ ] GitHub and HF authentication/remotes pass without secrets in URLs.
- [ ] Teacher endpoint/model and student checkpoint/revision are exact and loadable.
- [ ] Training and serving environments are isolated and import checks pass.
- [ ] `npm test` and `npm run build` pass on the remote checkout.
- [ ] Dry-run completes all phases with zero external side effects.
- [ ] One-prompt Linux smoke passes and pushes a checkpoint.
- [ ] Dashboard and Pi tools are verified in a real interactive Pi session.
- [ ] Replacement-host resume test recovers a saved cursor/job ID.
- [ ] Final held-out evaluation is real, not synthetic.

For state transaction examples and recovery cases, read `references/ssh-gpu-resume.md`.
