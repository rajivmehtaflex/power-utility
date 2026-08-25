---
name: workflow-contract-gap-analysis
description: Use when comparing setup and downstream pipeline workflows.
license: MIT
metadata:
  author: Hermes Agent
  hermes_related_skills: remote-gpu-model-specialization, pi-model-specialization-orchestration, project-feature-maintenance, cli-tool-installation
  hermes_tags: workflow, gap-analysis, environment, GPU, distillation, Modal, SSH, gates, reproducibility
  platforms: linux, macos, windows
  version: 1.0.0
---

# Workflow Contract Gap Analysis

Use this skill when one document or phase is supposed to prepare the environment for another phase, especially for GPU training, distillation, evaluation, serving, or remote execution workflows.

The central rule is: **an environment phase is complete only when every downstream executable requirement is installed, verified, persisted, and reachable through an explicit handoff gate.** A package list and a successful `import` are not sufficient evidence.

## 1. Compare downstream requirements before editing or executing

Read the setup phase and every downstream phase first, then inventory requirements from the downstream commands rather than inferring them from the setup title.

Extract, at minimum:

- executable commands and shell utilities;
- imported Python packages, CLI entry points, and version constraints;
- compiler, CUDA toolkit, driver, and binary requirements;
- model IDs, revisions, filenames, caches, and disk footprints;
- credentials, repository permissions, and remote URLs;
- filesystem paths, persistent volumes, temporary directories, and artifact locations;
- network listeners, tunnels, authentication, and local-client access;
- phase boundaries, process cleanup, job IDs, cost data, and resume metadata;
- source files, generated inputs, expected outputs, schemas, and gate thresholds.

Create a matrix with these columns:

```text
requirement | downstream phase | setup status | verification evidence | persistence | failure impact | required fix
```

Use these statuses precisely:

```text
installed | verified | persisted | generated-earlier | unspecified | blocked
```

Do not call an item “covered” because a related tool is present; record the exact executable, version, path, and smoke test.

## 2. Classify blockers and fix the earliest phase

Mark a gap as **blocking** when it can cause any of the following:

- failure after GPU time or cloud cost has already been spent;
- loss of artifacts when a VM or session ends;
- unsafe execution of generated shell commands;
- inability to reproduce a model or dataset because revisions are floating;
- unavailable model endpoint or unreachable local-client integration;
- unmeasured runtime, GPU-seconds, or provider cost;
- impossible data-volume gates after deduplication, filtering, or holdout allocation;
- coexistence of teacher and student processes when the workflow requires one model in VRAM;
- source or CLI files missing at the point where the next phase begins.

Move each blocking check to the earliest phase that can verify it. Do not defer storage, RAM, compiler, authentication, source-contract, or endpoint checks until a training or serving phase.

Keep an explicit distinction between:

- **source prerequisites**, such as generator, verifier, split, trainer, merge, or reward files that must exist before execution; and
- **runtime artifacts**, such as prompts, synthetic rows, checkpoints, evaluation reports, and merged weights that a phase is responsible for generating.

A preflight must not require a runtime-generated artifact before the phase that creates it, but it must gate the next phase on that artifact afterward.

## 3. Build a complete remote GPU environment contract

For a 27B quantized teacher plus 9B training/serving workflow, verify:

- Linux x86_64 and Bash/GNU userland;
- at least 8 CPU cores and 32 GiB RAM, with 64 GiB preferred for full merge/checkpoint workflows;
- at least 24 GiB GPU VRAM and a visible NVIDIA driver;
- CUDA toolkit/compiler availability when compiling CUDA-dependent binaries;
- persistent storage, not merely free space on an ephemeral root filesystem;
- at least 100 GiB free for the complete workflow, with 120 GiB preferred;
- model and dataset caches located on the persistent volume;
- `git`, `git-lfs`, `curl`, `jq`, `rsync`, `tmux`, `cmake`, `ninja`, `gh`, `uv`, and the exact model server binary;
- training, data-audit, serving, and provider-client package entry points.

Install tools idempotently, but verify them separately with `command -v` and a version or help command. If a required package is unavailable from the base image, stop with the precise missing prerequisite instead of silently substituting an untested tool.

Keep vLLM, training libraries, and teacher serving in separate environments when pins conflict; otherwise prove the combined lockfile works with actual imports and runtime smoke tests.

## 4. Test runtime capability, not just imports

A valid GPU gate should include:

1. PyTorch CUDA availability and a real CUDA matmul.
2. The precision modes the training phase will use, usually BF16 or FP16.
3. bitsandbytes import plus a CUDA-relevant operation or diagnostic.
4. vLLM CLI/version and a minimal load or server smoke where feasible.
5. llama.cpp or `llama-server` version, immutable revision, and CUDA offload capability.
6. GPU-process inspection before and after every model-residency transition.

Record the selected precision and exact binary/model revisions in non-secret metadata. Do not rely on `nvidia-smi` alone to prove that the training stack can execute.

## 5. Make shell verification fail honestly

Use a common shell preamble for executable bootstrap blocks:

```bash
set -Eeuo pipefail
IFS=$'\n\t'
umask 077
trap 'printf "FAIL line %s: %s\\n" "$LINENO" "$BASH_COMMAND" >&2' ERR
```

Avoid verification patterns that hide failures:

- do not pipe package installation into `tail` without `pipefail`;
- do not use `|| true` around initialization unless the code distinguishes “already exists” from a real error;
- do not use `git add -A` when large caches, checkpoints, or weights may exist;
- do not put tokens in HTTPS remotes, command output, logs, or generated metadata;
- do not treat a successful `tee` or final pipeline command as proof that an earlier command succeeded;
- do not use broad process-kill commands when a clean ownership check is possible.

Every gate should produce a clear PASS or stop with the actual missing value, path, version, or resource measurement.

## 6. Pin models, repositories, and credential boundaries

Require immutable teacher and student revisions, identify the exact GGUF file rather than downloading an ambiguous glob, verify read access before inference, and create or verify the target model repository before training.

Authenticate through provider CLIs or runtime secret injection. Verify the expected account and repository permissions without printing secrets. Configure Git credential helpers where needed, but keep remotes token-free and commit only an explicit allowlist of source, report, and metadata files.

Keep model weights and large generated outputs on persistent storage or Hugging Face revisions; keep source code, tests, gate reports, and manifests in GitHub.

## 7. Validate data contracts and threshold margins

For generators, verifiers, splitters, trainers, mergers, and reward functions, require:

- a stable JSONL/schema contract;
- deterministic IDs and reproducible synthesis where intended;
- `--help` or equivalent CLI contract checks;
- self-tests before real model calls;
- sandbox timeouts, resource limits, isolated temporary repositories, and controlled network access for generated shell execution;
- a defined callable interface before using a verifier as a GRPO reward;
- baseline evaluation output before claiming student improvement.

Calculate the minimum upstream yield against every downstream requirement before approving a gate. For example, if verified teacher rows at the minimum success rate plus synthetic rows equal exactly the required train-plus-eval count, any deduplication or filtering causes inevitable failure; increase the target or change the gate.

## 8. Design phase lifecycle, cost, and recovery gates

Every remote phase should record:

```text
phase status
provider/modal run ID
process/job ID
attempt number
start/end time
gpu-seconds and estimated/actual cost
input cursor and checkpoint ID
artifact paths and SHA-256 hashes
model/repository revision
next action and error details
```

Before a GPU phase, verify the required persistent volume, clean GPU ownership, model input, and cost budget. After a phase, verify artifacts and gates before marking it done, unload or stop the model server, update the ledger atomically, hash outputs, and push the recoverable state before continuing.

Do not claim that a provider cost guardrail is enforced from inside the VM unless authoritative provider runtime data is actually available. If the provider launcher owns the billing data, require it to write or return the phase metadata.

## 9. Handle local-client handoffs explicitly

If a remote serving phase is consumed by a local Mac or another network boundary, define the host binding, tunnel or public route, authentication, TLS policy, port lifetime, and smoke test. A server command with a port is not an end-to-end connectivity plan.

Verify the final client behavior in the real client environment, not only with a local curl against the server process.

## Required deliverable from a gap analysis

Report:

1. whether the setup phase truly satisfies the downstream contract;
2. a table of blockers, risks, and covered requirements with source line references;
3. the earliest phase where each fix belongs;
4. revised gates and required inputs;
5. remaining source-code or provider-owned work that the environment phase cannot fabricate.

Use `references/downstream-phase-gap-analysis.md` for the reusable review matrix, concrete shell checks, and the distillation-specific checklist.

## Pitfalls

- Treating a generic Python environment as the complete training stack.
- Checking only GPU visibility while omitting RAM, persistent volume, CUDA toolkit, or model-server capability.
- Requiring runtime-generated data before the phase that creates it.
- Assuming a downstream document’s referenced source files exist without checking the repository.
- Accepting zero-margin dataset thresholds.
- Measuring local process time instead of authoritative provider GPU-seconds.
- Leaving the teacher server resident while starting student training.
- Using token-bearing Git remotes for convenience.
- Calling a phase complete because the process exited zero without verifying artifacts, metrics, hashes, and recovery state.
