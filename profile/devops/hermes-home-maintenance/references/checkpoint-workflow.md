# Hermes Checkpoint Workflow

Use this reference when a user asks how to inspect, force, create, restore, or distinguish Hermes snapshots and filesystem checkpoints.

## Two different snapshot systems

### Filesystem checkpoints

Filesystem checkpoints are transparent shadow-Git snapshots stored under:

```text
$HERMES_HOME/checkpoints/
```

They protect a working directory before a file-mutating tool runs. They are separate from Hermes config/state snapshots and are the records shown by:

```bash
hermes checkpoints status
hermes checkpoints list
```

Inside an interactive CLI/TUI session, `/rollback` lists available checkpoints and `/rollback N` restores one.

### Hermes config/state snapshots

The in-session `/snapshot` command creates or restores Hermes configuration/state snapshots. Those snapshots do **not** appear in `hermes checkpoints list` and cannot be injected into the filesystem checkpoint store through the supported CLI.

## Enabling filesystem checkpoints

Set the persistent configuration through the CLI:

```bash
hermes config set checkpoints.enabled true
hermes config get checkpoints.enabled
```

For a single explicit session, use:

```bash
hermes chat --checkpoints
```

A new Hermes session may be required after changing the persistent setting because the agent constructs its checkpoint manager when the session starts. The command-line flag is the unambiguous per-session override.

## How checkpoints are created

There is no supported `hermes checkpoints create` or `hermes checkpoints import` command. The supported trigger is an actual file-mutating operation. Hermes takes the snapshot immediately before:

- `write_file`
- `patch`
- destructive `terminal` commands

The manager deduplicates to at most one snapshot per working directory per conversation turn. The checkpoint captures the pre-operation state, so it is available for rollback after the operation begins.

To deliberately create a checkpoint for a project, start a checkpoint-enabled session and perform a small, intentional edit in that project. Avoid relying on a no-op patch: the file tool may reject a no-op even though checkpoint preflight occurs first. Do not create a dummy edit in a production project without user approval; use a disposable project or a meaningful requested change when possible.

## Inspecting and maintaining the store

```bash
hermes checkpoints status   # size, project count, per-project breakdown
hermes checkpoints list     # alias for status
hermes checkpoints prune    # remove stale/orphan checkpoints and GC the store
hermes checkpoints clear    # permanently remove all rollback history; prompts first
hermes checkpoints clear-legacy
```

Never present a zero-size status as a failure by itself: it simply means no qualifying mutation has occurred in a checkpoint-enabled session, or the store has been pruned/cleared.
