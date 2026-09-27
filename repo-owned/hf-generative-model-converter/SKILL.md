---
name: hf-generative-model-converter
description: Use when converting a Hugging Face text-generation or vision-language model into a local runtime format and validating it by real inference — GGUF for llama.cpp (verified route today), ONNX or LiteRT-LM (planned rows, not yet verified — check references/compatibility.md first) — and when packaging the verified artifacts with a SHA-256 manifest or publishing them to the Hugging Face Hub. Triggers include "convert model to GGUF", "gguf conversion", "export this model for llama.cpp", "publish converted model to HF Hub", "make a .litertlm bundle", and "verify the converted model runs without the source weights". Enforces immutable revision pinning, source-built toolchains, license checks, staged packaging, and guarded publication.
license: Apache-2.0
compatibility: Linux x86_64 shell with git, CMake >=3.14, a C++17 compiler, Python 3.12 with uv, and network access to github.com and huggingface.co. CPU-only inference baseline; no GPU assumed. Source builds need ~3 GB disk and run within ~12 GB RAM. Publication needs an HF write token already stored in the local Hub configuration. Verified scope today is GGUF text-generation on CPU; every other target or platform is planned, not verified.
metadata:
  version: "0.1.0"
  author: rajivmehtaflex
  verified_targets: "gguf (text-generation, linux-x86_64 CPU)"
  planned_targets: "onnx, litert-lm — see references/compatibility.md; never execute as supported"
---

# Hugging Face Generative Model Converter

Convert pinned Hugging Face models to a local runtime format, prove the converted model actually
works, and — only then — package and publish it. Every claim in your final report must map to recorded
evidence; a step that did not run is `pending`, never `passed`.

## Inputs to capture first

1. Source model ID and optional revision (resolve to an immutable commit; never silently change the
   requested model, revision, target, precision, or workload).
2. Target format: `gguf` | `onnx` | `litert-lm` (normalize `litert`/`litertlm` to `litert-lm`;
   treat "llama.cpp format" as `gguf`).
3. Destination (optional): Hub repo id and visibility for publication.
4. Deployment backend/profile if the user names one; otherwise use the recipe's documented default.

Ask only for what is missing and material. Reuse authorization and answers already given for the same
operation; never re-prompt for an existing credential.

## Phase order (report a per-phase result at the end)

Run phases in order. A phase that fails blocks everything after it — report the failure and stop
rather than working around it.

| # | Phase | Governing reference |
|---|---|---|
| 1 | Route check: is (model, target, task, platform) supported/documented/blocked? | [references/compatibility.md](references/compatibility.md) |
| 2 | Preflight: host, resources, toolchain, workspace layout | [references/source-builds.md](references/source-builds.md) |
| 3 | Access & license gates: source readability, license status, custom-code decision | [references/compatibility.md](references/compatibility.md) + [references/huggingface-upload.md](references/huggingface-upload.md) |
| 4 | Source build of the target toolchain (build key, ready marker, no prebuilt substitution) | [references/source-builds.md](references/source-builds.md) + target recipe |
| 5 | Model acquisition: download the pinned revision, verify completeness | target recipe |
| 6 | Conversion with the recorded profile | target recipe |
| 7 | Validation: frozen fixtures, reference comparison, staged reload | [references/validation.md](references/validation.md) |
| 8 | Packaging: stage allowlist + manifest build/verify | [references/validation.md](references/validation.md) §Packaging |
| 9 | Publication (optional): guarded Hub upload + remote verification + receipt | [references/huggingface-upload.md](references/huggingface-upload.md) |
| 10 | Report: phase-result table with evidence states | this page §Reporting |

## Target recipes

- **GGUF** (verified route): [references/gguf.md](references/gguf.md)
- ONNX, LiteRT-LM: no recipe exists yet. If the user asks for them, state plainly that this skill has
  not verified those targets, point to [references/compatibility.md](references/compatibility.md), and
  do not execute any conversion under this skill's name.

## Non-negotiable rules

1. **Pins.** Resolve model and tool revisions to immutable commits before any download or build.
2. **No silent prebuilt binaries.** Converter/runtime native components are built from source. If a
   dependency arrives prebuilt through pip/CMake/a container/LFS, name it, stop the route, and require
   an explicit component-level exception before substituting anything. Record any authorized exception
   in the recipe record.
3. **Profiles.** Record the resolved profile (precision, context, batch, sampling, template mode)
   before converting. Use the documented default unless the user's deployment need overrides it; ask
   only about unresolved material choices.
4. **Adapters and variants.** Reject adapter/PEFT sources explicitly (no opportunistic merging). If a
   repo has several viable variants, require an explicit selection; a model ID is not an instruction to
   enable arbitrary remote code.
5. **Validation before publication.** Conversion output alone proves nothing. Bounded target-side
   inference against a frozen fixture set must pass before staging, and the staged package must reload
   with source weights unavailable before publication.
6. **Failures stay honest.** A failed source build never becomes a prebuilt substitution; a failed
   inference never publishes; missing credentials or hardware leaves the item `pending`.
7. **Secrets.** Tokens come exclusively from the local Hub configuration; never echo, log, or store
   them in manifests, receipts, cards, or reports.
8. **Licenses.** Record source terms and notices. Publication requires license status `clear` or an
   applicable recorded permission; "the user said proceed" does not resolve a redistribution
   restriction.

## Positive worked invocation (GGUF, verified route)

```text
User: Convert Qwen/Qwen3-0.6B to GGUF so llama.cpp can run it, then publish to my HF repo.
Agent:
  Phase 1  Route: Qwen3-0.6B (decoder-only, text-generation) × gguf × linux-x86_64 CPU
           → recipe gguf-qwen3-0.6b-linux-x64-cpu exists in assets/recipes.json [pending→execute].
  Phase 2  Preflight per references/source-builds.md: record CPU/RAM/disk/toolchain;
           build key reused from .hf-converter/builds/<key>/READY when it matches.
  Phase 3  Access: source public (not gated); license Apache-2.0 → clear, recorded.
  Phase 4  Build llama.cpp at the pinned revision if no healthy build key matches
           (references/gguf.md §Build). A build failure stops here — no substitution.
  Phase 5  Download the pinned revision; check file index before load (references/gguf.md §Acquire).
  Phase 6  Convert with the recorded profile (references/gguf.md §Convert).
  Phase 7  Validate per references/validation.md: frozen fixtures, reference comparison,
           then reload the staged package with source weights unavailable.
  Phase 8  Stage allowlisted files; scripts/artifact_manifest.py build → verify.
  Phase 9  Publication only after 7–8 pass: references/huggingface-upload.md rules +
           scripts/hub_publish.py; confirm destination/visibility first; keep the receipt.
  Phase 10 Report: one line per phase with evidence state (passed/failed/pending/blocked + why).
```

All commands run relative to the installed skill directory; reference paths above resolve from there.

## Out of scope (refuse explicitly, suggest the boundary)

Fine-tuning or adapter training/merging; new model architectures (converter code changes); image,
audio, or video generation; embedding/classifier tasks; quantization sweeps; performance benchmarking;
and any target/platform pair not marked verified in [references/compatibility.md](references/compatibility.md).
Offer the nearest supported route when one exists.

## Reporting

End every run with a phase-result table: phase, state (`passed`/`failed`/`pending`/`blocked`),
and one-line evidence (command/artifact/reason). Distinguish "tool ran" from "result verified".
Never upgrade a state without evidence recorded under the run directory.
