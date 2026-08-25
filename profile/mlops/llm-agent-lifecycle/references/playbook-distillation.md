# Playbook Distillation — 2026-08-06 Revision

Source: three Current-OS adaptations + HF handoff in `unsloth/` (revision 2026-08-06). Distilled for reuse without re-reading PDFs.

## Published Release (Handoff Anchor)

- Repo: `rajivmehtapy/git-assistant-qwen2.5-coder-1.5b` — https://huggingface.co/rajivmehtapy/git-assistant-qwen2.5-coder-1.5b
- Pinned commit: `cb60cc84f74a1a42e3af98c5a68261416cc7dbcf`
- Contents: merged 16-bit weights (`model.safetensors` ~3.1 GB BF16) + `config.json` + `generation_config.json` + `tokenizer.json` + `tokenizer_config.json` + `chat_template.jinja` + `README.md`. Adapter/checkpoints not published.
- Base: `Qwen/Qwen2.5-Coder-1.5B-Instruct`, `max_model_len=2048`, served as `git-assistant`.

## Pinned Dependency Set

| Component | Pin | Note |
|-----------|-----|------|
| Python | 3.11.0 (Current OS), ≥3.10 (New Machine) | — |
| torch | `2.11.0+cu130` + `--extra-index-url https://download.pytorch.org/whl/cu130` | CUDA 13.0 runtime |
| unsloth | `2026.8.5` | — |
| openpipe-art | `0.5.18` | replaced `art-agent` |
| vllm | `0.26.0` | isolated venv, incompatible Transformers pin |
| Node/CUDA | Debian 11 Bullseye, NVIDIA L4 22.03 GiB, driver 580.95.05, CUDA 13.0, `dumb-init` PID1, no systemd/Docker | direct Python only |

## File Layout (Current OS)

```
/root/unsloth-agent-env/              # training stack
/root/vllm-agent-env/                 # serving stack (vllm==0.26.0)
/root/content/
  verify_agent_infrastructure.py      # CUDA+GPU+imports+4bit smoke
  train_agent.py                      # 15-step GRPO entrypoint
  export_model.py                     # LoRA → merged 16-bit
  test_train_agent.py                 # py_compile + reward-function checks
  unsloth_git_agent_lora/             # adapter output
  final_git_agent_model/              # merged model (serving input)
  git_agent_checkpoints/checkpoint-{10,15}
```

New Machine:
```
./git-assistant-vllm-env/             # single vLLM env
./models/git-assistant-qwen2.5-coder-1.5b/
  model.safetensors, README.md, config.json, generation_config.json,
  tokenizer.json, tokenizer_config.json, chat_template.jinja
```

## GRPO Canonical Config

- Objective: 15-step smoke/training on four Git tasks — `init_commit`, `branch_create`, `commit_and_tag`, `merge_branch`.
- `num_generations=4`, batch=1, grad_accum=4, BF16 when supported, 8-bit AdamW.
- `max_tokens=2048` (L4 VRAM cap), `fast_inference=False`, `use_vllm=False`.
- Verifier: Git sandbox with isolated HOME, Git identity, timeout, path/command safety checks.
- Completion: adapter + `checkpoint-15`; export writes `final_git_agent_model/model.safetensors`.

## Container Error Transcript (why the workarounds exist)

On the Debian 11 container with `vllm==0.26.0`:

1. **Missing `/usr/local/cuda`** — bundled CUDA toolkit lives at `.../site-packages/nvidia/cu13`, not at the system path vLLM expects. Fix: `CUDA_HOME=.../nvidia/cu13` + `PATH` prefix.
2. **FlashInfer JIT failure** — `VLLM_USE_FLASHINFER_SAMPLER` tries to JIT-compile against incompatible CUDA headers (no compiler/header pairing in container). Fix: `VLLM_USE_FLASHINFER_SAMPLER=0` (fallback sampler sufficient for validation).
3. **MiniMax Triton warmup import** — `vllm/model_executor/warmup/kernel_warmup.py` imports an unrelated MiniMax M3 Triton warmup that fails to compile. Fix: narrow patch to skip only that optional warmup; keep the patch when recreating the env.
4. **CUDA-graph capture** — kernel warmup / graph capture fails on this stack without eager. Fix: `--enforce-eager`.

See playbooks §4–5 (Infra + Training) for the combined command. New Machine §9 explicitly says: do not apply on the new host unless the same errors reproduce.

## Lifecycle & Gates

```
Infra (two venvs + verify_agent_infrastructure.py exit 0 + pip check clean)
  → Train (GRPO exit 0, adapter+checkpoint-15)
  → Export (model.safetensors exists)
  → Serving validation (/health 200, /v1/models lists git-assistant, /v1/chat/completions 200)
  → Publish (HF Hub, record repo+commit)
  → (Flush)
  → New Machine (hf download --revision <commit> → clean vllm serve → same three curl checks)
```

## Payload Shape (all three playbooks converge on this)

These are the confirmed command literally used in validation — do not paraphrase:

**Infrastructure verify:**
```bash
/root/unsloth-agent-env/bin/python /root/content/verify_agent_infrastructure.py
```

**Training preflight + run + export:**
```bash
/root/unsloth-agent-env/bin/python -m py_compile /root/content/train_agent.py /root/content/export_model.py /root/content/test_train_agent.py
/root/unsloth-agent-env/bin/python /root/content/test_train_agent.py
/root/unsloth-agent-env/bin/python -u /root/content/train_agent.py
/root/unsloth-agent-env/bin/python -u /root/content/export_model.py
```

**Serving validation (Current OS isolated env):**
```bash
CUDA_HOME=/root/vllm-agent-env/lib/python3.11/site-packages/nvidia/cu13 \
PATH=/root/vllm-agent-env/bin:/root/vllm-agent-env/lib/python3.11/site-packages/nvidia/cu13/bin:$PATH \
VLLM_USE_FLASHINFER_SAMPLER=0 \
/root/vllm-agent-env/bin/python -m vllm.entrypoints.openai.api_server \
  --model /root/content/final_git_agent_model --served-model-name git-assistant \
  --max-model-len 2048 --enforce-eager --host 127.0.0.1 --port 8000
```

**HF handoff (New Machine, clean first):**
```bash
./git-assistant-vllm-env/bin/hf models info rajivmehtapy/git-assistant-qwen2.5-coder-1.5b
./git-assistant-vllm-env/bin/hf download rajivmehtapy/git-assistant-qwen2.5-coder-1.5b \
  --revision cb60cc84f74a1a42e3af98c5a68261416cc7dbcf --local-dir ./models/git-assistant-qwen2.5-coder-1.5b
./git-assistant-vllm-env/bin/vllm serve ./models/git-assistant-qwen2.5-coder-1.5b \
  --served-model-name git-assistant --max-model-len 2048 --host 127.0.0.1 --port 8000
```

**Shared serving contract:**
```bash
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1:8000/v1/models
curl -fsS http://127.0.0.1:8000/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"model":"git-assistant","messages":[{"role":"user","content":"Give a bash command to initialize a git repository in project and commit README.md."}],"max_tokens":80,"temperature":0}'
```

## Security Notes (session-specific detail carried forward)

- No API key created by any playbook. Prefer `ssh -L 8000:127.0.0.1:8000 user@host` over binding `0.0.0.0`; if bound publicly, require authenticated reverse proxy + firewall.
- `hf auth login` optional for public model but useful for rate limits; never commit token.
- Experimental 15-step release — no benchmark, four Git templates only; must not grant shell/credentials/network.
- Optional Transformers smoke test exists for clients that need `AutoModelForCausalLM` (`torch_dtype=torch.bfloat16`, `device_map="auto"`) in addition to vLLM.
