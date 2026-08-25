# Distillation → Git Specialist (Ridge-27B teacher → Qwen3.5-4B student)

Design session 2026-08-18. The deterministic data generator was VALIDATED (ran live on the
user's Mac, 5 rows with genuine git outputs). The end-to-end pipeline (Modal data-gen → SFT →
export) was NOT yet executed — items below are verified facts plus argued design decisions,
not a proven run report.

## Verified model facts (HF API, checked 2026-08-18)

| Role | Repo | Format | Notes |
|---|---|---|---|
| Teacher | `empero-ai/Qwen3.8-27B-Ridge-GGUF` | GGUF only | `Qwen3.8-27B-Ridge-3.7bpw.gguf` (~12.5 GB) + `mmproj-…-BF16.gguf`; NO safetensors repo exists anywhere. Community finetune, 12.8K downloads, unbenchmarked on git tasks |
| Student | `Qwen/Qwen3.5-4B` | 2 safetensors shards + config.json | Apache-2.0, fine-tunable. `Qwen/Qwen3.5-4B-Base` also exists if starting from base |

Format/license pre-check recipe: `curl https://huggingface.co/api/models/<id>` → inspect
`siblings[].rfilename` (safetensors? config.json?) and `tags[]` (license).

## Core architectural insight

GGUF cannot be TRAINED (inference-only quantized format, no gradients) but is perfectly
valid as a distillation TEACHER — behavioral distillation needs the teacher only to GENERATE,
which llama.cpp/Ollama do natively with GGUF. The common warning "GGUF can't be trained"
kills "train the 27B GGUF and shrink it", NOT "distill FROM a GGUF teacher into a
safetensors student". The latter is the legal version of that idea.

GRPO vs distillation (from the user's source doc, consistent with TRL's API shape):
- GRPO: same model in and out; reward-driven sharpening; policy IS the trained model.
- Distillation: two models; teacher frozen; student matches teacher outputs.
- A live oracle/model inside the GRPO loop collapses the group's reward spread → advantage
  variance → zero training signal. Rule: "borrow intelligence into the weights, not the
  runtime." A bigger model is safe as distillation teacher or as judge of unaided attempts.

## Pipeline design (argued with user, accepted direction)

**Stage 1 — data-gen** (Modal L40S 48GB, llama.cpp batch inference; 12.5 GB quant leaves
large headroom): curated prompt taxonomy (init/commit, branching, merge conflicts, rebase,
stash, reflog recovery, tags, submodules, bisect, hooks) → teacher generations →
REJECTION SAMPLING: execute each teacher answer in a throwaway git sandbox; admit only rows
whose post-execution repo state matches the request. ~30% extra Stage-1 cost, filters
teacher errors before SFT bakes them in; the same verifiers double as future GRPO reward
functions.

**Stage 2 — SFT**: TRL `SFTTrainer`, conversational JSONL (`messages`), assistant-only
loss (default). LoRA for iteration cycles (~$2/run); optional full-FT for the frozen-data
release run. Mix ~10–15% general instruction data against catastrophic narrowing.

**Data mix**: ~70% verified teacher / ~15% deterministic synthetic / ~15% general.

**Stage 3 — export**: merge LoRA → publish HF (commit-pin) → GGUF Q4_K_M → Ollama.
Reuses steps 3–4 of the main lifecycle workflow.

## Cost envelope (L40S @ $1.95/hr)

| Stage | Est. time | Est. cost |
|---|---|---|
| Teacher gen: 10k prompts × ~700 tok out | 4–8 h | $8–16 |
| SFT LoRA 2–3 epochs | <1 h | ~$2 |
| Merge + GGUF export | ~15 min | ~$0.50 |
| Full cycle | | ≈ $10–20, rerunnable |

First move before ANY cloud spend: audition the teacher locally via Ollama (12.5 GB quant
fits Apple Silicon unified memory), ~30 git prompts, $0 — a weak community finetune poisons
everything downstream.

## TRL × Modal integration facts (researched 2026-08-18)

- Official example: https://modal.com/docs/examples/grpo_trl (source:
  `modal-labs/modal-examples/06_gpu_and_ml/reinforcement-learning/grpo_trl.py`). Pins
  `trl[vllm]==0.28.0`, `vllm==0.12.0`, `transformers==4.57`. Pattern:
  `GRPOConfig(use_vllm=, vllm_mode=)`, H100 function configs with 24h timeout, checkpoints
  to `modal.Volume`, W&B via Modal Secret, `modal run --detach`.
- TRL vLLM modes: `colocate` (DEFAULT since TRL v1 / PR #5255 — in-process, shares GPU with
  the trainer; tune `vllm_gpu_memory_utilization`, enable `vllm_enable_sleep_mode` on OOM)
  and `server` (`trl vllm-serve --model …` on separate GPUs; split via CUDA_VISIBLE_DEVICES).
- Modal RL siblings worth knowing: `learn_math.py` (verifiers library, 4×H100, sandboxed
  code exec via Modal Sandboxes — the natural home for git reward verifiers) and
  `grpo_verl.py` (verl + Ray).

## Sample-data-kit pattern (for first-time trainers)

Built at `~/Desktop/git-distill-samples/` — reuse this lineage shape whenever a user asks
"show me what the training data looks like":

```
00_README.md               honesty labels: authored vs illustrative vs real
01_prompts.jsonl           authored input taxonomy (prompts are ours to design)
02_teacher_raw.jsonl       teacher answers pre-filter    [label ILLUSTRATIVE if mocked]
03_verified_sft.jsonl      post-sandbox rows, TRL schema [rejections carry reject_reason]
04_deterministic_synth.jsonl  REAL rows generated by live command execution
05_what_trainer_sees.txt   one row rendered through the chat template + token accounting
```

Token accounting per typical row: ~35 system + ~60 user (masked) + ~450 assistant (trained)
+ ~15 template ≈ 560-token context. 10k samples ≈ 10M teacher tokens ≈ the $8–16 Stage-1
budget line. Rules: only assistant tokens carry loss (training on prompts teaches asking,
not answering); never present mocked teacher outputs as real — label them; always eyeball
rendered rows before training (subtle corruption survives automated checks).
