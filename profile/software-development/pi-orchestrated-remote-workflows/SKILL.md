---
name: pi-orchestrated-remote-workflows
description: Use for Pi extensions coordinating resumable remote phases.
license: MIT
metadata:
  author: Hermes Agent
  hermes_related_skills: pi-extension-authoring, test-driven-development, project-feature-maintenance, modal-deploy
  hermes_tags: Pi, orchestration, remote-jobs, resumability, checkpoints, Git-LFS, TUI, dry-run
  platforms: linux, macos, windows
  version: 1.0.0
---

# Pi-Orchestrated Remote Workflows

Use this skill when a Pi extension is the control plane for a multi-phase workflow involving remote GPUs, teacher/model endpoints, disposable machines, generated artifacts, training jobs, deployment, or a live phase dashboard.

## Core architecture

Keep the Pi extension as the control plane, not a monolithic implementation:

```text
Pi tools/dashboard
  -> typed phase state machine
  -> durable ledger + artifact manifest
  -> injected teacher/remote/Git adapters
  -> deterministic workers and gates
  -> checkpoint commit/push
```

`src/index.ts` should register tools and delegate to focused modules. Deterministic workers, model clients, remote job adapters, and renderers must be independently testable.

## Phase state and resume contract

Persist a versioned ledger with at least:

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
  commit?: string;
  nextAction?: string;
  error?: string;
}
```

At repository level also store workflow name, remote URL, branch, target dialect, mode, and update time. Use atomic writes (`temp file -> rename`) and reject corrupted ledgers.

On a new disposable worker:

1. Clone/pull the remote repository with fast-forward-only semantics.
2. Read and validate the phase ledger.
3. Verify artifact hashes from the manifest.
4. Poll any saved remote job IDs.
5. Convert stale `working` records to `interrupted` instead of silently rerunning.
6. Skip `done` phases.
7. Resume a batch phase from `inputCursor`/`lastCheckpoint`, deduplicating deterministic IDs.

Never claim a phase is durable until its ledger/manifest and artifacts have been pushed.

## Mandatory checkpoint lifecycle

Use four checkpoint classes:

1. **Before launch:** persist `working` and phase attempt; commit/push.
2. **After remote launch:** persist remote job ID and initial cursor; commit/push.
3. **After each durable batch:** atomically write output, hash it, update cursor/checkpoint; commit/push.
4. **After gate:** persist `done`, artifact hashes, cost, commit/revision, and next action; commit/push.

If a push fails, leave the phase failed or unsynchronized and report the error. Do not claim success based only on local files.

## Dry-run first

Implement explicit `dry-run` and `live` modes. Dry-run must inject fake:

- teacher/model client
- verifier
- remote job executor
- Git/Hugging Face sync

The dry run should exercise one simple prompt through the whole phase graph and prove:

```text
network calls = 0
gpu calls = 0
model calls = 0
remote pushes = 0
```

Mark simulated jobs/artifacts with `simulation: true`; never present a simulated trained model as a live result. Use dry-run thresholds separate from production gates.

## Remote model/job adapters

Define provider-neutral interfaces and inject them into orchestration code:

```ts
interface TeacherClient {
  generate(prompt: string, options?: GenerationOptions): Promise<{ text: string; requestId?: string }>;
}

interface RemoteExecutor {
  launch(spec: JobSpec): Promise<RemoteJob>;
  status(jobId: string): Promise<RemoteJob>;
  cancel(jobId: string): Promise<void>;
  logs(jobId: string): Promise<string>;
}
```

Use the configured OpenAI-compatible llama.cpp endpoint for teacher inference when that is the selected transport. Do not silently fall back to a local provider during tests or remote phases. Mock `fetch` in client tests; never call Ollama or another live model in local verification unless explicitly requested.

Store request IDs, model, decoding settings, retry attempt, job ID, GPU seconds, estimated/actual cost, remote artifact paths, and next action in the ledger.

## Artifact and repository policy

For a single Hugging Face Git repository containing workflow code, data, state, reports, and model revisions:

- ordinary Git: TypeScript/Python code, JSON/JSONL, reports, ledger, manifests
- Git LFS/HF revisions: safetensors, adapters, tokenizer binaries, other large weights
- never commit API keys, `.env`, Modal/HF credentials, caches, build output, or arbitrary model-supplied paths

Use an allowlisted path policy and hash every durable artifact. Record HF revision/tag and commit ID for model releases.

## Pi phase dashboard

Read a real sibling Pi dashboard/table implementation before using UI APIs. Keep the dashboard a pure ledger renderer; it must not own phase business logic. Stable columns should include:

```text
Phase | Name | Status | Cursor | Job ID | GPU sec | Cost | HF commit/revision | Artifacts | Next action
```

Show `pending`, `working`, and `done`; distinguish `failed`, `blocked`, and `interrupted`. Provide a headless text fallback. Verify interactive behavior in a live Pi TTY, not only with `-p`.

## TDD workflow

For every new orchestrator slice:

1. Write a focused failing test.
2. Run the focused test and confirm the expected failure.
3. Implement the smallest behavior.
4. Run the focused test and then the existing suite.
5. Add failure/recovery tests before refactoring.

Use fake adapters for remote/model/Git operations. Test lost jobs, push rejection, corrupted state, stale working phases, duplicate batches, cost overruns, and forbidden paths.

## Verification gates

Before a live phase:

- `npm test` has real tests and passes.
- `npm run build` passes.
- dry-run completes without side effects.
- remote URL/branch/auth are verified.
- Git LFS is available and patterns are configured.
- phase prerequisites and artifact hashes pass.
- user explicitly authorizes the live teacher/GPU/push operation.

A phase gate must report PASS/FAIL, actual versus estimated cost, artifacts, commit/revision, and next action.

## Supporting reference

See `references/phase-orchestrator-checkpoints.md` for the reusable ledger example, checkpoint timeline, and GPU-loss recovery matrix.
