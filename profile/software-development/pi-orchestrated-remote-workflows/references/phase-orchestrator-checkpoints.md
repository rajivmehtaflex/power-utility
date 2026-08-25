# Phase Orchestrator Checkpoints

## Durable ledger fields

Keep `mode` (`dry-run` or `live`), phase status, attempt, remote job ID, input cursor, total inputs, last checkpoint, artifact paths, SHA-256 hashes, commit/revision, cost, and next action in a versioned ledger.

## Four checkpoints

1. Before launch: write `working`, then commit/push.
2. After remote launch: write job ID and cursor, then commit/push.
3. After each durable batch: write output atomically, hash it, update cursor/checkpoint, then commit/push.
4. After the gate: write `done`, hashes, cost, revision, and next action, then commit/push.

## New-worker recovery

```text
git pull --ff-only
read ledger
verify artifact hashes
poll saved job IDs
mark stale working-without-job interrupted
skip done phases
resume from cursor/last checkpoint
```

A local file is not durable until its checkpoint commit is pushed. For a Hugging Face repository, keep code/state/text in Git and large weights/adapters in Git LFS/HF revisions. Never commit secrets or credentials.

## Dry-run contract

Use fake model, verifier, remote-job, and Git/HF adapters. Assert zero network calls, zero GPU calls, zero model calls, and zero pushes. Mark all simulated outputs with `simulation: true` and keep smoke thresholds separate from production gates.
