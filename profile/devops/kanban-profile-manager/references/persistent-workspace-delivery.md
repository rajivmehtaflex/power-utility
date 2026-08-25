# Persistent Workspace Delivery for Kanban Tasks

Use this pattern whenever a Kanban task must leave behind a durable artifact such as:

- SQLite databases
- generated source files
- exported reports/docs
- notebooks, archives, or build outputs

## Key rule

A Kanban worker's **scratch workspace is ephemeral**. If the task must persist, the card must explicitly target a persistent workspace, such as:

- `--workspace dir:/absolute/path/to/project`
- `--workspace worktree` / `worktree:/path` when a git worktree is preferred

## Task body should always say

- the **final artifact path**
- whether the worker should **verify the path exists** before completion
- any **post-write validation** required (row counts, checksums, schema checks, etc.)

## Good task wording

> Build the SQLite database and write the final file to `/abs/project/data/student_activity.db`. Verify the file exists at that path and confirm row counts after population.

## Bad task wording

> Build the SQLite database.

That leaves the worker free to complete in scratch space only.

## Handoff checklist

1. The card uses a persistent workspace, not scratch.
2. The final output path is named in the body.
3. The worker verifies the artifact at that exact path.
4. The completion summary includes the final path and validation evidence.
