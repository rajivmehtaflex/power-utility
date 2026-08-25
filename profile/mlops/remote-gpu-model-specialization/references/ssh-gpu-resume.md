# SSH GPU checkpointing and resume reference

This reference applies when compute runs on a manually provisioned SSH GPU host rather than Modal.

## Remote layout

Keep source and durable artifacts explicit:

```text
/workspace/pi-shell-specialization/       # GitHub source checkout
/workspace/pi-shell-specialization-state/ # HF Git/LFS state checkout
/workspace/models/
/workspace/checkpoints/
```

Use a persistent attached disk for caches and temporary checkpoints, but never depend on it as the only recovery mechanism. The HF state repository is the recovery source of truth.

## Checkpoint transaction

For each phase, perform these transactions in order:

1. Atomically write `status=working`, `executionMode`, attempt, inputs, and next action.
2. Commit/push the ledger before starting the remote process.
3. Start the process and immediately persist its PID/job identifier.
4. After every durable batch, atomically append output, calculate SHA-256, update `inputCursor` and `lastCheckpoint`, and commit/push.
5. Validate output schema, hidden verification, and phase gates.
6. Set `status=done`, record final artifacts/hashes/revision, and commit/push again.

A successful local write that was not pushed is not durable after host loss.

## Resume matrix

| Remote state | Recovery action |
|---|---|
| `pending` | Start phase after dependency gates pass. |
| `working` with saved PID/job ID | Check whether the process/job is alive; poll it before starting another. |
| `working` without PID/job ID | Mark `interrupted`; inspect artifacts; restart from the last pushed cursor. |
| `interrupted` with cursor | Resume only uncompleted deterministic IDs. |
| `done` with matching hashes | Skip phase. |
| `done` with missing/mismatched hash | Block workflow and repair artifact before continuing. |
| `failed` | Preserve logs and artifacts; require explicit retry. |
| `blocked` | Do not launch dependent phases. |

## New-host bootstrap

A replacement host should:

```text
git clone/pull GitHub source
git clone/pull HF state
git lfs install
verify `git remote -v` and branch
verify `hf auth whoami` and `gh auth status`
load `state/phase-ledger.json`
load `state/artifact-manifest.json`
verify every referenced file hash
poll saved remote process/job IDs
mark stale working-without-ID as interrupted
resume from `inputCursor`/`lastCheckpoint`
```

Do not regenerate completed teacher responses. Assign deterministic IDs before generation and deduplicate by ID when appending JSONL.

## Teacher/student sequencing

For response-level distillation:

```text
teacher loaded or served
  -> generate teacher responses
  -> verify responses
  -> push verified dataset
  -> stop/unload teacher
student loaded
  -> SFT/QLoRA
  -> evaluate
```

Do not load both large models on the same GPU unless a later experiment explicitly requires online/logit distillation. GRPO uses the student policy and a frozen reference model; it does not use a live teacher.

## SSH handoff contract

An instance name is not enough. The agent needs a connected SSH/remote backend or a generated connection command plus a working directory. Collect only non-secret values:

```text
provider
host
user
port
remote working directory
persistent disk mount
GPU/VRAM
RAM/CPU
GitHub checkout path
HF checkout path
```

Never request private keys, passwords, or tokens in chat. Verify access with harmless commands before editing:

```bash
pwd
nvidia-smi
git status --short
hf auth whoami
gh auth status
```

## Ollama policy

Ollama is not a dependency or fallback for this workflow. Use llama.cpp/OpenAI-compatible HTTP for the teacher, Transformers/QLoRA for the student, and the deterministic shell verifier for GRPO reward. Do not run generated scripts on the development Mac.
