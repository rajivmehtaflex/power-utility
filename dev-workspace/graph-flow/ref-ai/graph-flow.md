# Create `graph-flow`: a Code-Backed Stateful Graph Skill for Codex

## Summary

Create a user-level Codex skill at `~/.codex/skills/graph-flow` that models implementation work as a **stateful directed graph**, not merely a DAG.

The design will retain Claude Code Dynamic Workflow principles—coded coordination, parallel workers, independent verification, resumable state, and one synthesized result—while implementing them with Codex tasks, worktrees, and a bundled deterministic state helper. [Claude Code workflow architecture](https://code.claude.com/docs/en/workflows) [Codex multi-agent capabilities](https://openai.com/index/introducing-the-codex-app/)

The graph may contain:

- Parallel fan-out and fan-in
- Conditional runtime branches
- Bounded implement–verify–repair cycles
- Human approval and blocked states
- Persisted structured state and event history

## Skill and Runtime Design

- Create `SKILL.md` with this trigger:

  `Use when a repository task spans multiple independently executable units, has runtime-dependent branches, or requires repeated implementation and verification across isolated worktrees.`

- Define this execution lifecycle:

  1. Inspect the repository and acceptance criteria.
  2. Model implementation, decision, verification, and integration nodes.
  3. Define static dependencies and allowed runtime outcomes.
  4. Initialize the structured graph state in `awaiting_approval`.
  5. Present the graph, loops, branches, agent count, owned paths, checks, and risk estimate.
  6. After approval, dispatch ready nodes through isolated Codex tasks/worktrees.
  7. Record structured results and evaluate conditional transitions.
  8. Route failed verification back to the implementation node with verifier evidence.
  9. Stop repair loops after three implementation attempts and mark the run `blocked`.
  10. Fan verified branches into integration and final system-level verification.

- Use a single-writer model:
  - The coordinating Codex task is the only state writer.
  - Worker and verifier agents receive read-only node envelopes.
  - Agents return structured result envelopes.
  - Agents must never edit the shared state file directly.

## Structured State Engine

Bundle `scripts/graph_state.py`, implemented with the Python standard library.

Store run state in the repository’s shared Git directory:

```text
<git-common-dir>/graph-flow/<run-id>/state.json
```

This location is untracked and shared across Git worktrees. For non-Git projects, fall back to:

```text
<project-root>/.codex/graph-flow/<run-id>/state.json
```

Use atomic replacement, a lock file, monotonically increasing `revision`, and an append-only event collection.

### State interface

```json
{
  "schema_version": 1,
  "run_id": "graph-flow-...",
  "task": "Implement the requested feature",
  "acceptance_criteria": [],
  "status": "awaiting_approval",
  "revision": 1,
  "limits": {
    "max_concurrency": 4,
    "max_node_attempts": 3,
    "max_total_transitions": 100
  },
  "nodes": {},
  "events": []
}
```

Each node contains:

```json
{
  "id": "verify-auth",
  "kind": "implementation|decision|verification|integration",
  "status": "pending|ready|running|completed|failed|blocked|skipped",
  "attempt": 0,
  "depends_on": [],
  "owned_paths": [],
  "input_refs": [],
  "allowed_outcomes": ["passed", "failed"],
  "transitions": {
    "passed": ["integrate-auth"],
    "failed": ["implement-auth"]
  },
  "result": null
}
```

### State commands

```text
graph_state.py init --repo <path> --definition <file-or-stdin>
graph_state.py approve --state <path>
graph_state.py ready --state <path>
graph_state.py start --state <path> --node <id>
graph_state.py complete --state <path> --node <id> --result <file>
graph_state.py block --state <path> --node <id> --reason <text>
graph_state.py summary --state <path>
graph_state.py validate --state <path>
```

`ready` returns at most four runnable node envelopes. `complete` validates the result outcome, updates state, evaluates transitions, activates the selected branches, and increments attempts when a loop returns to an implementation node.

## Routing and Self-Correction Rules

- Replace “DAG” terminology with “stateful graph.”
- Keep static dependency edges for artifacts required before execution.
- Use outcome transitions for runtime routing.
- Decision nodes must return one declared outcome, such as `legacy`, `modern`, or `unsupported`.
- Invalid or undeclared outcomes fail the node.
- Verifiers are read-only and use fresh context.
- A verifier result must contain actual evidence: test output, type checks, lint results, benchmark results, or inspected diffs.
- A failed verifier transitions back to its implementation node with failure evidence added to the next node envelope.
- Downstream nodes activate only after the required verifier returns `passed`.
- Repair loops stop after three implementation attempts.
- The entire run stops if it exceeds 100 state transitions.
- Human input is required when a run becomes blocked, changes public APIs, or needs destructive actions.

## Skill Resources and Interface

Create:

```text
graph-flow/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── scripts/
│   └── graph_state.py
└── references/
    ├── state-schema.md
    └── runtime-mapping.md
```

`agents/openai.yaml` will use:

- Display name: `Graph Flow`
- Short description: `Run self-correcting coding graphs`
- Default prompt: `Use $graph-flow to model and execute this repository task as a stateful, verified implementation graph.`

`runtime-mapping.md` will explicitly distinguish:

| Claude Code Dynamic Workflow | `graph-flow` in Codex |
|---|---|
| JavaScript workflow runtime | Python state-transition helper |
| Script variables | Shared JSON state payload |
| `agent()` and `pipeline()` | Codex tasks and isolated worktrees |
| `/workflows` progress view | State summary plus Codex task status |
| Native workflow replay | Persisted state followed by explicit re-inspection |
| Saved workflow command | Reusable `$graph-flow` skill |

The Markdown execution ledger becomes a generated human-readable view of `state.json`; it is no longer the source of truth.

## Validation Plan

- Unit-test the state helper for:
  - Static fan-out and fan-in
  - Conditional `legacy` versus `modern` routing
  - Implement → verify → fail → repair → verify → pass loops
  - Three-attempt repair limit
  - Maximum-transition protection
  - Invalid outcome rejection
  - Dependency blocking
  - Concurrency limiting
  - Atomic concurrent claims
  - Git common-directory and non-Git storage
  - Pause/reload from persisted state

- Pressure-test the skill using RED–GREEN–REFACTOR:
  - Baseline agents incorrectly produce a static DAG.
  - Baseline agents accept self-verification.
  - Baseline agents lose state across worktrees.
  - Baseline agents continue after failed validation.
  - Baseline agents create unbounded repair loops.
  - With `$graph-flow`, each scenario must use structured state, conditional transitions, fresh verification, and bounded cycles.

- Run packaging validation:
  - Scaffold with `init_skill.py`.
  - Test `graph_state.py` in a temporary Git repository with multiple worktrees.
  - Generate `agents/openai.yaml`.
  - Run `quick_validate.py`.
  - Confirm `SKILL.md` makes no unsupported claim of Claude-compatible workflow execution.

## Assumptions

- The target remains Codex, not Claude Code.
- The skill includes a deterministic state helper rather than relying on prompt-only orchestration.
- The coordinating task is the sole state writer.
- Default concurrency is four agents.
- Repair loops permit three implementation attempts.
- Run state is untracked and shared through Git’s common directory.
