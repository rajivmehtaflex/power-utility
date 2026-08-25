---
name: llm-agent-lifecycle
description: Unsloth GRPO training, HF export and vLLM serving lifecycle.
license: MIT
metadata:
  author: Hermes Agent
  hermes_tags: unsloth, grpo, lora, huggingface, vllm, cuda, agent-training
  version: 1.0.0
---

# LLM Agent Lifecycle — Train, Export, Handoff, Serve

Covers the full lifecycle split across two hosts that recurs in the Unsloth GRPO Git-assistant work: provision a GPU container for training, run a bounded GRPO fine-tune, export LoRA → merged 16-bit HF model, publish/commit-pin, and redeploy via HF Hub on a new machine with isolated vLLM. Captures the non-obvious environment decisions that are easy to re-break.

## When to Use

- Provisioning a Debian/Bullseye container (or any containerized session with no systemd/Docker daemon) for Unsloth + ART/TRL GPU training.
- Running a short GRPO smoke run (15 steps is the validated gate) on `Qwen/Qwen2.5-Coder-1.5B-Instruct` or similar 1–2B coder with Git-task reward verifiers.
- Merging adapter → standalone Transformers model and publishing/pinning a HF Hub release.
- Serving the published model with `vllm==0.26.0` where Transformers requirements conflict with the training stack, or where CUDA 13 is bundled at `.../nvidia/cu13`.
- Any "model already published, deploy on a fresh machine" handoff where the Hub is source-of-truth (no retraining).

**Don't use for:** generic Modal-only deploys (see `modal-deploy`), or single-tool `vllm serve` without the training/export context.

## Host Profiles

| Host | Canonical shape (validated) | Key flag |
|------|-----------------------------|----------|
| **Current OS (training)** | Debian 11 Bullseye, Python 3.11.0, NVIDIA L4 22.03 GiB, driver 580.95.05, CUDA 13.0, PID1=`dumb-init`, no Docker socket | Direct Python, no Docker |
| **New Machine (handoff)** | Any Linux, Python ≥3.10, NVIDIA GPU holding ~3.1 GB BF16 + runtime, outbound HTTPS to `huggingface.co` | Clean venv, no copied envs |

## Workflow

### 1. Provision — two-venv isolation

Training and serving Transformers constraints conflict — never share one venv.

```bash
# Training env
/usr/local/bin/python3 -m venv /root/unsloth-agent-env
/root/unsloth-agent-env/bin/python -m pip install --upgrade pip setuptools wheel
/root/unsloth-agent-env/bin/python -m pip install 'torch==2.11.0+cu130' --extra-index-url https://download.pytorch.org/whl/cu130
/root/unsloth-agent-env/bin/python -m pip install 'unsloth==2026.8.5' 'openpipe-art==0.5.18'
# note: original `art-agent` renamed → `openpipe-art`

# Serving env (isolated)
 /usr/local/bin/python3 -m venv /root/vllm-agent-env
/root/vllm-agent-env/bin/python -m pip install --upgrade pip setuptools wheel
/root/vllm-agent-env/bin/python -m pip install 'vllm==0.26.0'
/root/vllm-agent-env/bin/python -m pip check
```

Verify with the checked-in smoke (see `references/playbook-distillation.md`):
`/root/unsloth-agent-env/bin/python /root/content/verify_agent_infrastructure.py` — checks CUDA+L4, imports (Unsloth/ART/Transformers/bnb), and a 4-bit `Qwen/Qwen2.5-Coder-1.5B-Instruct` init.

New-machine counterpart is lighter:
```bash
python3 -m venv ./git-assistant-vllm-env
./git-assistant-vllm-env/bin/python -m pip install --upgrade pip setuptools wheel
./git-assistant-vllm-env/bin/python -m pip install 'vllm==0.26.0'
./git-assistant-vllm-env/bin/python - <<'PY'
import torch, vllm
print(torch.__version__, torch.cuda.is_available(), vllm.__version__)
PY
```

### 2. Train + Export (Current OS)

Preflight:
```bash
/root/unsloth-agent-env/bin/python -m py_compile /root/content/train_agent.py /root/content/export_model.py /root/content/test_train_agent.py
/root/unsloth-agent-env/bin/python /root/content/test_train_agent.py
```

Canonical GRPO config (validated 15-step smoke):
- Tasks: `init_commit`, `branch_create`, `commit_and_tag`, `merge_branch`
- `num_generations=4`, `batch=1`, `grad_accum=4`, BF16 if supported, `8-bit AdamW`
- `max_tokens=2048` (VRAM cap on L4), `fast_inference=False`, `use_vllm=False`
- Sandbox verifier: isolated HOME, Git identity, timeout, path/command safety
- Checkpoints → `/root/content/git_agent_checkpoints/checkpoint-{10,15}`

```bash
/root/unsloth-agent-env/bin/python -u /root/content/train_agent.py
/root/unsloth-agent-env/bin/python -u /root/content/export_model.py
# artifacts: /root/content/unsloth_git_agent_lora  →  /root/content/final_git_agent_model
```

Completion: `final_git_agent_model/model.safetensors` exists; `pip check` clean in training env.

### 3. Publish / Pin (boundary between hosts)

Publish the merged 16-bit model (weights + tokenizer + `chat_template.jinja` + `generation_config.json`) to HF Hub. Record repo + pinned commit — that commit is the new-machine source-of-truth.

Validated release (example): `rajivmehtapy/git-assistant-qwen2.5-coder-1.5b` @ `cb60cc84f74a1a42e3af98c5a68261416cc7dbcf`.

### 4. Handoff — New Machine via HF Hub (no retraining)

```bash
./git-assistant-vllm-env/bin/hf auth login   # optional for public repos, helps rate limits
./git-assistant-vllm-env/bin/hf auth whoami
./git-assistant-vllm-env/bin/hf models info rajivmehtapy/git-assistant-qwen2.5-coder-1.5b
mkdir -p ./models
./git-assistant-vllm-env/bin/hf download rajivmehtapy/git-assistant-qwen2.5-coder-1.5b \
  --revision cb60cc84f74a1a42e3af98c5a68261416cc7dbcf \
  --local-dir ./models/git-assistant-qwen2.5-coder-1.5b
stat ./models/git-assistant-qwen2.5-coder-1.5b/model.safetensors
```

Then serve — **try clean first**:
```bash
./git-assistant-vllm-env/bin/vllm serve ./models/git-assistant-qwen2.5-coder-1.5b \
  --served-model-name git-assistant --max-model-len 2048 --host 127.0.0.1 --port 8000
# also valid: vllm serve rajivmehtapy/git-assistant-qwen2.5-coder-1.5b ...
```

### 5. Serve — container workarounds (only if clean fails)

The Current OS container requires three coupled workarounds for `vllm==0.26.0` + bundled CUDA 13 (no `/usr/local/cuda`):

```bash
CUDA_HOME=/root/vllm-agent-env/lib/python3.11/site-packages/nvidia/cu13 \
PATH=/root/vllm-agent-env/bin:/root/vllm-agent-env/lib/python3.11/site-packages/nvidia/cu13/bin:$PATH \
VLLM_USE_FLASHINFER_SAMPLER=0 \
/root/vllm-agent-env/bin/python -m vllm.entrypoints.openai.api_server \
  --model /root/content/final_git_agent_model \
  --served-model-name git-assistant --max-model-len 2048 --enforce-eager \
  --host 127.0.0.1 --port 8000
```

Narrow patch: `vllm/model_executor/warmup/kernel_warmup.py` — skip only the optional MiniMax M3 Triton warmup import that fails to compile. Keep the patch when recreating the env.

**Policy:** On a new machine, do NOT apply these automatically. Apply only if the same specific `CUDA_HOME`/FlashInfer/warmup errors reproduce; record any machine-specific change separately. (See `references/playbook-distillation.md` for the exact error transcript.)

### 6. Verify (both hosts)

```bash
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1:8000/v1/models   # must list `git-assistant`
curl -fsS http://127.0.0.1:8000/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"model":"git-assistant","messages":[{"role":"user","content":"Give a bash command to initialize a git repository in project and commit README.md."}],"max_tokens":80,"temperature":0}'
# pass: 200 on all three, non-empty generation containing git init/add/commit workflow
```

Remote access: `ssh -L 8000:127.0.0.1:8000 user@host` preferred; unauthenticated vLLM on `0.0.0.0` only behind authenticated reverse proxy + firewall.

## Pitfalls

1. **One venv for both stacks breaks.** Unsloth and current vLLM have incompatible Transformers pins — keep `/root/unsloth-agent-env` and `/root/vllm-agent-env` separate. `pip check` must be clean before launching vLLM.
2. **`fast_inference=True` / `use_vllm=True` during GRPO.** Must be `False` on this container; vLLM is for post-export validation only.
3. **Copying venvs to the new machine.** Do not copy `/root/unsloth-agent-env`/`/root/vllm-agent-env` after flush — recreate from scratch.
4. **Blindly applying container workarounds on a new host.** The HF playbook explicitly reverses them. Try clean serve first.
5. **Unpinned downloads.** Always `hf download --revision <commit>` against the published commit; the floating `main` is not the deployment gate.
6. **Experimental release scope.** 15-step GRPO on four Git templates, no benchmark score, no shell/credential/network access for the model. Validate generations before execution.

## References

- `references/playbook-distillation.md` — distilled facts, pinned versions, file layout, and container error transcript from the three 2026-08-06 playbooks.
