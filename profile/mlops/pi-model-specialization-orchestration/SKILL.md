---
name: pi-model-specialization-orchestration
description: Use when orchestrating staged local-model specialization.
license: MIT
metadata:
  author: Rajiv Mehta, Hermes Agent
  hermes_related_skills: pi-extension-authoring, project-feature-maintenance, modal-deploy
  hermes_tags: Pi, model-specialization, distillation, GRPO, orchestration, resumability
  platforms: linux, macos
  version: 0.1.0
---

# Pi Model Specialization Orchestration Skill

Use this skill when a Pi extension must orchestrate a staged local-model specialization workflow: measure a student model, turn confirmed weaknesses into targeted data, submit prompts to a teacher, verify teacher outputs, prepare a dataset, launch remote SFT/GRPO jobs, evaluate checkpoints, and resume safely after disposable compute disappears.

Pi is the control plane; deterministic workers and remote adapters are the data/training plane. Do not make `src/index.ts` a monolith, and do not treat a benchmark package as if it already implements training.

## When to Use

- A Pi extension must manage multi-phase model specialization.
- Weakness evidence should drive teacher-question generation.
- Teacher inference runs through a remote OpenAI-compatible endpoint such as llama.cpp.
- SFT, evaluation, GRPO, or serving runs on Modal or another disposable worker.
- The user needs phase status, cost gates, Git/HF checkpoints, and resume after VM loss.
- A benchmark must become an orchestrator rather than remaining a one-shot evaluator.

Do not use this skill for a single offline benchmark, ordinary model serving, or a one-off fine-tune with no phase ledger or resume requirement.

## Prerequisites

- A Pi extension package with a testable registration entry point.
- A canonical target dialect (for shell work, explicitly choose Linux Bash/GNU or macOS Bash/BSD; never silently mix them).
- A structured weakness profile, not only a prose report.
- A remote repository that can persist code, state, text artifacts, and model revisions. For a Hugging Face model repo, verify Git/LFS and authenticated access before the first live push.
- Injected interfaces for teacher, remote jobs, verifier, and Git synchronization so dry-run tests never call the network or GPU.
- Secrets supplied through runtime secret storage; never write tokens to the ledger or repository.

## Phase model

Use explicit phase IDs and gates. A typical shell-specialization graph is:

```text
P0    baseline student evaluation → weakness profile
P2.0  weakness-conditioned question/scenario generation
P2.1  teacher inference and verified answers
P2.2  audit, deduplication, and train/eval/holdout split
P2.3  remote SFT/QLoRA
P2.4  merge and publish v0.1
P2.5  held-out student evaluation
P2.6  GRPO sharpening with unaided rollouts
P2.6b merge and publish v0.2
P2.7  64K serving smoke test
P2.8  Pi provider/final release
```

Every phase has a typed status: `pending`, `working`, `done`, `failed`, `blocked`, or `interrupted`. A phase is not `done` merely because a remote job was launched.

## Control-plane architecture

Keep business logic in modules and expose small Pi tools:

```text
src/orchestrator/
  phase-types.ts       # ledger/job/artifact contracts
  phase-ledger.ts      # atomic state and resume decisions
  phase-gates.ts       # prerequisites and acceptance checks
  artifact-manifest.ts # hashes, storage, revisions
  teacher-client.ts    # OpenAI-compatible teacher adapter
  question-generator.ts
  remote-executor.ts   # injected Modal/job interface
  git-sync.ts          # allowlisted HF Git/LFS commits
  orchestrator.ts      # phase transitions
src/tui/phase-dashboard.ts
```

Recommended tool families:

```text
specialization_status
specialization_start_phase
specialization_resume
specialization_generate_questions
specialization_submit_teacher
specialization_verify_teacher_data
specialization_build_dataset
specialization_launch_sft
specialization_evaluate
specialization_launch_grpo
specialization_serve
specialization_sync_remote
specialization_stop_job
specialization_artifacts
```

Read-only status/artifact tools should work in headless mode. Expensive or mutating tools must return the phase, execution mode, job ID, ledger path, and next action.

## Procedure

### 1. Lock the target before generating data

Record the target domain, dialect, student checkpoint, teacher checkpoint/endpoint, deployment harness, and holdout policy in the workflow manifest. If the benchmark says macOS but Modal workers run Linux, stop and resolve the dialect mismatch before generating training data.

### 2. Measure the student first

Run the diagnostic benchmark externally in an isolated environment. Use independent contexts, hidden verification, and a fixed question order. Separate:

- capability failures: syntax, runtime, functional, safety, portability;
- protocol failures: refusal, missing/ambiguous fence, malformed response;
- evaluator failures: unavailable sandbox, fixture failure, verifier failure.

Only repeated machine-verified capability failures should drive teacher-data generation.

### 3. Convert evidence into a structured weakness profile

The profile should include category, labels, pass@1/pass@N, difficulty breakdown, affected case IDs, confidence, curriculum mix, and optional student/control gap. Keep JSON as the orchestrator input and Markdown as the human report.

### 4. Run a dry-run before live operations

Use `mode: "dry-run"` and fake adapters. Exercise one simple prompt end-to-end:

```text
The file name is stored in $INPUT_FILE and contains a space. Copy that file to $TEST_ROOT/copied.txt while preserving the filename correctly. Return exactly one Bash code block and no explanation.
```

The dry run must produce simulated ledger/artifact/job records while guaranteeing:

```text
network calls = 0
GPU calls = 0
teacher calls = 0
remote pushes = 0
```

Never label a simulated training result as a real model result.

### 5. Generate weakness-conditioned tasks

Give the LLM the confirmed weakness labels, curriculum weights, target dialect, safety rules, and a strict task schema. Ask for new variants, not copies of the failed diagnostic prompts. Keep private fixtures, expected outputs, verifier commands, and failure labels out of the public model prompt.

The generator proposes tasks; a deterministic schema/scenario verifier decides whether a task is valid.

### 6. Submit tasks to the teacher and verify answers

Use an injected OpenAI-compatible client for the remote llama.cpp server. Record model, request ID, attempt, decoding settings, latency, and prompt ID. Re-ask a failed answer at most twice, then drop or use a deterministic fallback.

Teacher output is raw until it passes the same hidden verifier. Never train on an unverified teacher answer.

### 7. Audit and split without leakage

Deduplicate, enforce length limits, reject verifier leakage, preserve category/difficulty balance, and create a deterministic train/eval/holdout split. Holdout IDs must be stored in the ledger and never appear in training rows.

### 8. Launch remote SFT/evaluation/GRPO through adapters

The Pi extension launches remote jobs through an injected `RemoteExecutor`. Store the job ID before returning. Enforce one-model-in-VRAM rules and GPU cost gates. If actual GPU seconds exceed twice the estimate, stop/cancel safely and mark the phase blocked.

GRPO must score unaided student rollouts in the sandbox. Do not let the student call the teacher as a live co-pilot; that reinforces delegation and collapses the reward signal.

### 9. Publish model revisions separately from workflow state

Use normal Git for code, JSON/JSONL, reports, manifests, and state. Use Git LFS/Hugging Face revisions for large weights/adapters. Record model revision, commit, hashes, and artifact paths in the manifest. A model upload is not a phase completion until the revision can be downloaded and verified.

### 10. Resume from the durable remote state

On a new VM:

```text
git clone/pull remote repository
verify branch, remote, and Git-LFS
read phase-ledger.json
verify artifact hashes
poll saved remote job IDs
mark stale working-without-job as interrupted
skip done phases
resume from inputCursor/lastCheckpoint
```

See `references/hf-resume-checkpointing.md` for the checkpoint transaction and recovery cases.

## Phase ledger contract

At minimum, each ledger must record:

```ts
interface PhaseRecord {
  id: string;
  name: string;
  status: "pending" | "working" | "done" | "failed" | "blocked" | "interrupted";
  executionMode: "dry-run" | "live";
  attempt: number;
  jobId?: string;
  inputCursor?: number;
  totalInputs?: number;
  lastCheckpoint?: string;
  artifacts: string[];
  artifactHashes: Record<string, string>;
  gpuSeconds?: number;
  estimatedCostUsd?: number;
  actualCostUsd?: number;
  commit?: string;
  error?: string;
  nextAction?: string;
}
```

Use atomic writes. Mark `working` before launch, checkpoint after remote-job registration, checkpoint after durable batches, and mark `done` only after gate validation plus remote push confirmation.

## TUI requirements

For an in-process Pi dashboard, render a stable table from the ledger rather than putting orchestration logic in the UI:

```text
Phase | Name | Status | Cursor | GPU sec | Cost | HF commit | Job | Next action
```

Show `dry-run` versus `live`, last pushed checkpoint, artifact count, and resume action. Keep row widths stable. Read and port the existing Pi dashboard/tree-grid pattern instead of inventing unsupported UI APIs. Test the pure table renderer separately, then verify it in a real interactive Pi session; headless output cannot prove TUI rendering.

## Remote checkpoint policy

For a remote Git/LFS repository, checkpoint at four boundaries:

1. **Before launch:** ledger `working`, job ID empty; commit and push.
2. **After launch:** save the remote job ID and cursor; commit and push.
3. **After each durable batch:** append artifacts atomically, hash, update cursor/lastCheckpoint, commit and push.
4. **After the gate:** ledger `done`, hashes/revision/next action recorded; commit and push.

No unpushed state is recoverable after machine loss. Never wait until an entire long phase completes before pushing.

## Pitfalls

- Treating the benchmark as the entire training pipeline; it is the measurement foundation unless later phase modules are added.
- Calling the teacher a live GRPO co-pilot; use it offline for data/reference/judging, not to solve student rollouts.
- Treating a single failed response as a confirmed weakness; require repeated machine-verified evidence.
- Training on the diagnostic or final holdout set.
- Exposing hidden fixtures/verifiers to the question-generation or student prompt.
- Marking a phase done after job launch instead of after artifacts, gates, hashes, and push confirmation.
- Relying on VM-local files or a remote job ID that was never persisted.
- Regenerating completed teacher rows after a restart; use deterministic IDs, batch cursors, and deduplication.
- Mixing Bash/GNU and Bash/BSD semantics without a dialect field.
- Committing secrets or unmanaged large weights; use runtime secrets and Git LFS/HF revisions.
- Confusing `dry-run` success with a real model improvement.
- Creating a separate Hermes ambient widget when the requested surface is an in-process Pi dashboard.

## Verification

Before live P2.0:

1. Unit tests cover ledger transitions, fake adapters, schema validation, gates, TUI rendering, and HF sync allowlists.
2. Dry-run reaches every phase with one prompt and makes zero network/GPU/teacher/push calls.
3. Build passes and the Pi extension registers all orchestration tools.
4. Public prompts contain no fixtures or verifiers.
5. Fake Git tests prove start/job/batch/done checkpoints and push-failure recovery.
6. A synthetic new-VM resume test polls a saved job ID and resumes from a saved cursor.
7. HF remote/LFS preflight passes before any live push.
8. The live dashboard is verified interactively in Pi.

Do not claim the specialization works until a real held-out evaluation shows the trained student improves over the base student without unacceptable regression.
