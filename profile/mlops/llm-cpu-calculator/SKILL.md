---
name: llm-cpu-calculator
description: Estimate CPU and RAM needs for plain-English LLM workloads.
license: MIT
metadata:
  author: Rajiv Mehta, Hermes Agent
  hermes_related_skills: ""
  hermes_tags: llm, cpu, ram, model-sizing, speculative-decoding
  platforms: macos, linux
  version: 0.2.0
---

# LLM CPU Calculator Skill

Convert a user's plain-English LLM workload description into a grounded CPU and memory requirement estimate **for a named target machine** — typically a remote server (cloud GPU/CPU box, Lightning.ai instance, rented Linux host). The machine executing this skill is only the calculator host: it runs `scripts/estimate.py` and nothing else. Never profile the local machine, never produce a local-run verdict, and never recommend local LLM deployment.

This is an estimator, not a benchmark. Never present an exact throughput or an exact KV-cache size when the model architecture, runtime, or concurrency is unknown. Separate measured host facts from estimates and label uncertainty.

## When to Use

Use when the user asks for CPU, RAM, system-memory, SIMD, or server-sizing requirements for an LLM workload intended for a named or remote machine:

- "What CPU and RAM do I need for a 14B Q4 model?"
- "Size a server for speculative decoding."
- "Will an 8 vCPU / 32 GiB cloud box handle this?"
- "Compare two remote server options for this workload."

Do not use for model quality comparisons, training hardware, or a benchmark that requires running the model. For GPU/VRAM-only sizing, explain that this skill can provide only a secondary CPU/RAM estimate unless the user also requests CPU requirements.

**Out of scope, always:** assessing whether the machine running this skill can host the workload. If a question implies local deployment ("can my MacBook run this?"), answer with the target-machine requirements only and state that local deployment is not part of this workflow.

## Inputs to Parse

Extract values from plain English. Preserve the user's values exactly, then normalize them for calculation:

- Target model name and parameter count, such as `9B`, `14 billion`, or `70B`.
- Quantization precision: effective bits per parameter. Accept `Q4`, `Q4_K_M`, `4-bit`, `8-bit`, `FP16`, and `16-bit`; use the stated effective precision and mention that named quantization formats may have overhead.
- Draft model size for speculative decoding, in millions or billions. Default to `300M` only when speculative decoding is explicitly requested but no draft size is supplied.
- Context length in tokens. Default to `4096` only when omitted, and mark it as an assumption.
- Concurrent sequences, batch size, and expected prompt/output workload when supplied. Default concurrency to `1`.
- Runtime/backend: llama.cpp, vLLM, SGLang, or unknown. Do not assume a backend silently changes the memory estimate.
- **Target-machine specs**: installed RAM, physical cores, SIMD flags, GPU/VRAM — only as supplied by the user for the named target, or collected on that target (e.g., over SSH) when the user explicitly asks. Never collect them from the machine running this skill.

If the target parameter count is missing, ask for it. If the user gives a model name but no size, use a reliable model source or ask for the exact model variant rather than inventing its size. If context length or quantization is missing, calculate using an explicitly stated default and show how the result changes at common alternatives.

## Calculation Rules

Use binary GiB for all displayed memory values and state that convention. Use these estimates unless model metadata gives better values:

1. **Weights**

   `weight_GiB = parameters × 10^9 × (effective_bits / 8) / 2^30`

   For a draft model specified in millions, convert millions to billions before applying the formula. When a measured file size (GB, 10^9 bytes) is known, prefer `file_GiB = size_GB × 10^9 / 2^30` over the formula.

2. **KV cache**

   Prefer architecture metadata:

   `KV_bytes = 2 × layers × context_tokens × concurrent_sequences × kv_heads × head_dim × bytes_per_KV_value`

   Use `bytes_per_KV_value = 2` for FP16/BF16 KV and `1` for 8-bit KV. Count only KV-bearing layers (attention layers), not total layers. Include both target and draft KV caches for speculative decoding when draft architecture is known. If layers, KV heads, or head dimension are unavailable, use a clearly labeled range and say the KV figure is a rough placeholder; do not claim it scales correctly to other context lengths.

3. **Runtime and operating-system reserve**

   Add model-loading/runtime overhead and OS headroom on the target. Use at least `3 GiB` for a light dedicated single-user target and `6 GiB` or more for a workstation/server target, multiple sequences, or a desktop environment. Add an additional 10–20% of model weights when the runtime's memory behavior is unknown. Do not double-count a reserve already included in a supplied runtime measurement.

4. **Total working memory**

   `total_required_GiB = target_weights + draft_weights + target_KV + draft_KV + runtime_overhead + OS_reserve`

   For ordinary inference, omit draft weights and draft KV. For speculative decoding, include both models and state that the target and draft must be resident on the target at the same time.

5. **Safety margin**

   Recommend installed memory on the target above the working estimate: at least 15% free for a dedicated Linux host and 20–30% free for a multi-purpose or desktop-like target. Treat a configuration that only fits by using swap as constrained, not feasible.

## CPU Recommendation Rules

Classify CPU requirements separately from memory requirements, always for the target machine:

- **Minimum usable:** enough physical cores to keep the runtime responsive, with SIMD support. Use 4 physical cores for sub-7B Q4 single-user workloads, 8 for roughly 7–14B, 12–16 for roughly 20–34B, and 16+ for 70B-class CPU inference. Adjust upward for concurrency, long prompts, or strict latency targets.
- **Recommended:** use the next practical tier when the user asks for comfortable interactive use: generally 6–8 physical cores for sub-7B, 8–12 for 7–14B, 12–16 for 20–34B, and 24+ for 70B-class models. State that these are heuristic tiers, not throughput guarantees.
- **SIMD:** prefer ARM NEON/ASIMD on ARM targets and AVX2 (or AVX-512 when available) on x86 targets. Missing SIMD does not necessarily prevent execution but can make CPU inference impractically slow.
- **Threads:** for Linux targets, start near physical cores minus 1–2 for system headroom, then benchmark. Never imply that setting threads equal to all logical CPUs is automatically faster.
- **Remote server:** recommend a CPU server only when the user requests CPU-only or no suitable accelerator is available on the target. Mention a GPU option separately when it materially changes the recommendation; do not replace a CPU answer with a GPU answer.

## Sizing via the Calculator Script

The local machine's only job is to run the estimator script (stdlib Python, no network, no model download):

```
python3 <skill_dir>/scripts/estimate.py --params 9 --weight-file 5.9 \
  --layers 8 --kv-heads 4 --head-dim 256 --ctx 4096
```

- Parse the workload, map it to script flags, run the script, and audit its output against the calculation rules above.
- Use `--weight-file <GB>` when a measured model file size is known (preferred); otherwise pass `--bits <effective-bits-per-param>`.
- For speculative decoding add `--draft-params` / `--draft-bits` / `--draft-weight-file`, and draft KV geometry (`--draft-layers`, ...) when known.
- Pass `--target-ram <GiB>` when the named target's installed RAM is known to get a suitability verdict for that target.
- `--json` gives machine-readable output for further processing.
- If the script is unavailable, do the math manually with the same formulas and say so.

## Response Format

Return the result in this order:

1. **Parsed workload** — target, draft, quantization, context, concurrency, runtime, and target-machine specs (or "not supplied").
2. **Assumptions and confidence** — identify every default and any unknown architecture value.
3. **Memory footprint** — target weights, draft weights, target KV, draft KV, runtime/OS reserve, total working set, and recommended installed memory in GiB (script output).
4. **CPU requirement** — minimum and recommended physical cores, SIMD, thread guidance, and expected bottleneck.
5. **Hardware tiers** — minimum, recommended, and comfortable target options with CPU/RAM and an optional GPU/offload note.
6. **Suitability verdict** — only when target-machine specs are supplied or profiled on the named target: pass, constrained, or unsuitable, with swap risk explicitly called out. If no target specs exist, write "requirements only — no verdict possible" and stop there. Never a verdict about the machine running this skill.
7. **Runtime guidance** — for CPU-only llama.cpp on the target suggest `-ngl 0` and a starting `-t` near physical cores minus 1–2; mention `-ngl 999` only when the target has a GPU and offload is requested.
8. **What would improve accuracy** — request model architecture metadata, exact quantization file, KV-cache type, concurrency, or a benchmark on the target when those materially affect the result.

Use a compact table for calculations and show the formulas or enough intermediate values for the user to audit the result. Do not bury the final RAM and CPU recommendation in prose.

## Pitfalls

- Parameter count is not a complete memory specification. MoE models, embedding tables, quantization overhead, runtime arenas, and KV-cache layout can change the result.
- Context length and concurrency multiply KV-cache memory. Never reuse a 4K estimate unchanged for 8K, 16K, or multiple simultaneous sequences.
- A model fitting in RAM does not mean it will run at useful speed. Report SIMD, core count, and expected latency risk independently.
- Speculative decoding usually increases memory use because both target and draft models stay loaded; it may improve tokens per second but is not a free memory optimization.
- Do not promise that a particular instance type or server will achieve a specific tokens-per-second rate without a benchmark on that target.
- Do not treat swap-backed execution as a pass. Flag it as memory-constrained and explain the likely thrashing risk.
- Keep user-provided model names, quantization labels, and sizes literal. If a label is ambiguous, preserve it and state the interpretation used.
- **Never profile or judge the machine executing this skill** — it is the calculator host, not a deployment target.

## Verification

Before finalizing, verify that:

- Every user-supplied parameter appears in the parsed-workload section or is explicitly marked unsupported.
- All defaults and unknowns are listed under assumptions.
- The displayed total equals the sum of the displayed components, allowing only documented rounding.
- Draft model memory is included exactly when speculative decoding is requested.
- Recommended installed memory includes the stated safety margin.
- CPU cores, SIMD, memory capacity, and swap risk are reported as separate considerations.
- Any host claim came from user-supplied target specs or a fresh profile of the named target — never from the machine running this skill.
