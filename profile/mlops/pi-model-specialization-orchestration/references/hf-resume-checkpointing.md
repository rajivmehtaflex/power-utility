# HF Resume and Checkpointing for pi-shell-specialization

## Current workflow profile

- Package: `pi-shell-specialization`
- Canonical shell dialect: Linux Bash 5 + GNU userland
- Teacher transport: OpenAI-compatible llama.cpp endpoint on disposable Modal compute
- Dashboard: in-process Pi phase table
- Durable remote: Hugging Face Git/LFS repository `rajivmehtapy/pi-shell-specialization`, branch `main`
- Local tests: one-prompt dry run with fake adapters; no Ollama calls

## Single-repository layout

```text
state/phase-ledger.json
state/artifact-manifest.json
state/resume.json
data/prompts.jsonl
data/teacher_raw.jsonl
data/teacher_verified.jsonl
artifacts/weakness_profile.json
runs/*/job.json
model revisions and weights via Git LFS/HF revisions
```

## Four durable checkpoints

1. Before a phase launch: write `working`, empty job ID, and push.
2. After remote launch: save job ID/cursor and push.
3. After each durable batch: append data atomically, hash it, update `inputCursor`/`lastCheckpoint`, and push.
4. After the gate: write `done`, artifact hashes, revision, and next action, then push.

A phase is not durable until its checkpoint push succeeds. No unpushed state can be recovered after VM loss.

## Recovery

On a new GPU machine, clone/pull the HF repo, verify branch/remote/LFS, read the ledger, verify hashes, poll saved Modal job IDs, mark stale working-without-job phases `interrupted`, skip `done` phases, and resume from the saved cursor/checkpoint. Deterministic task IDs and deduplication prevent regenerating completed teacher rows.

## Dry-run rule

Use `mode: dry-run` with fake teacher, verifier, remote-job, and HF sync adapters before live work. The dry run must use one simple prompt and guarantee zero network calls, zero GPU calls, zero teacher calls, and zero pushes; simulated artifacts/jobs must be marked `simulation: true`.
