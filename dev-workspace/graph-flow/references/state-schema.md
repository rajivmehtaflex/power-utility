# State, Lifecycle, and Envelope Schema

`graph_state.py` is a deterministic, portable reducer. It accepts JSON files for
the legacy `init`, `approve --node`, and `complete` commands. Lifecycle commands
accept inline JSON in the arguments documented below. The coordinator is the only
supported state writer.

## Run discovery and storage

Git worktrees share `<git-common-dir>/graph-flow/<run-id>/state.json`.
Non-Git projects use `<repo>/.agent-skills/graph-flow/<run-id>/state.json`.
Run IDs are portable relative identifiers using `/` separators. Absolute POSIX
paths, Windows drives, rooted/anchored paths, UNC paths, backslashes, empty path
segments, `.`, and `..` are rejected. The resolved state path is verified to
remain beneath the resolved graph-flow control root before any lock or state write.

```bash
graph_state.py runs --repo <path>
```

`runs` returns records sorted by `run_id`, each containing `run_id`, `status`,
`updated_at`, and the absolute `state_path`.

## Unified intake and requirements

`start --repo <path> --run-id <id> --request '<json>'` creates a run without a
graph. The initial request is an open-ended object, but `goal` must be a non-empty
string. If `repository` is absent, it is set to the absolute `--repo` path. The
run starts in `collecting_requirements`; progress is unavailable until a graph is
planned.

`plan --definition '<json>' --requirements '<json>'` accepts exactly these
requirements fields:

```json
{
  "goal": "Required non-empty string",
  "success_criteria": ["At least one non-empty string"],
  "scope": {
    "included": ["Zero or more non-empty strings"],
    "excluded": ["Zero or more non-empty strings"]
  },
  "constraints": ["Zero or more non-empty strings"],
  "verification": ["At least one non-empty string"],
  "approval_boundaries": ["Zero or more non-empty strings"],
  "assumptions": ["Zero or more non-empty strings"]
}
```

The definition must satisfy the planned graph schema below. Each successful plan
or pre-approval revision replaces the unapproved definition, recreates its node
records, increments `plan_revision`, and enters `awaiting_graph_approval`.
Revision is rejected after `approve` changes the run to `running`.

## Planned graph definition

Definitions use version 1 inside state schema v2:

```json
{
  "version": 1,
  "workstreams": [
    {
      "id": "engine",
      "title": "State engine",
      "objective": "Implement deterministic lifecycle behavior."
    }
  ],
  "max_concurrency": 2,
  "limits": {"max_attempts_per_node": 3, "max_transitions": 100},
  "nodes": [
    {
      "id": "implement",
      "kind": "decision | implementation | verification | integration | human",
      "workstream": "engine",
      "objective": "Implement the lifecycle.",
      "assigned_role": "explorer | default | worker | reviewer | human",
      "priority": "critical | high | normal | low",
      "acceptance_criteria": ["Required for non-human nodes"],
      "paths": ["Required non-empty strings for non-human nodes"],
      "verification_commands": ["Required non-empty strings for non-human nodes"],
      "outcomes": ["done"],
      "depends_on": [{"node": "source", "outcome": "done"}],
      "depends_on_any": [{"node": "alternative", "outcome": "done"}],
      "transitions": {"rejected": "repair-target"},
      "failure_outcomes": ["failed"],
      "resources": ["canonical/logical/resource"],
      "prompt": "Optional task-local instruction"
    }
  ]
}
```

Planned nodes must reference a declared workstream and use an allowed role and
priority. Each non-human node requires non-empty string lists for
`acceptance_criteria`, `paths`, and `verification_commands`. `paths` records the
exact repository artifacts the planned worker will read or own; each
`verification_commands` entry is a complete command for that node. These fields
persist in the approved definition and the coordinator copies them verbatim into
the generated worker envelope. Human nodes must use role `human`; they may omit
all three execution fields, or provide non-empty `acceptance_criteria` when useful.
Static dependency edges must be acyclic; runtime `transitions` may loop. Scheduler
order is priority, then number of immediately downstream nodes unlocked, then
definition order. Legacy definitions passed to `init` remain valid and retain
definition order.

`depends_on` is AND, `depends_on_any` is OR, and an unreachable dependency skips
the dependent node. `failure_outcomes` block the run. Resource keys are exclusive;
definitions reject different keys that normalize to the same path or have a
path-segment prefix relationship.

When a runtime transition requeues a repair target, every completed or skipped
node in that target's full transitive static downstream closure is reset to
`pending`. This includes intermediate integration nodes and the rejecting
verifier itself. Nodes outside that dependency closure keep their status, result,
attempt count, and task identity.

Before any repair mutation, the reducer checks both the target and that closure
for active handles. If the target or any descendant is still running, the run
becomes `blocked`; target/downstream records are not reopened, and every active
record and handle is preserved. The reason lists ordered `node=task-id` pairs.
The blocked event includes nullable
`active_target: {"node":"...","task_id":"..."}` plus ordered
`active_descendants: [{"node":"...","task_id":"..."}]`. A later `tick` returns
blocked and cannot redispatch the target or report completion.

## Human request and response schema

Only one request may have `status: "open"` in a run. Open a preflight request:

```bash
graph_state.py request --repo <path> --run-id <id> --request '<json>'
```

Open a runtime request and relinquish the exact running handle:

```bash
graph_state.py request --repo <path> --run-id <id> \
  --node implement --task-id worker-123 --request '<json>'
```

The request JSON has this exact shape:

```json
{
  "kind": "input | approval",
  "answer_type": "single_select | multi_select | confirm | text",
  "prompt": "Required non-empty string",
  "rationale": "Required non-empty string",
  "options": ["required", "for select types only"]
}
```

Select requests require at least two unique, non-empty options. Other answer types
must omit `options`. Persisted records add `id`, `scope` (`preflight` or `node`),
`node`, `task_id`, `status`, timestamps, and the eventual answer.

Answer with inline JSON:

```bash
graph_state.py respond --repo <path> --run-id <id> \
  --request-id request-1 --answer '"selected-option"'
```

- `single_select`: a string equal to one declared option.
- `multi_select`: a non-empty, unique JSON list drawn from the options.
- `confirm`: JSON `true` or `false`.
- `text`: a non-empty JSON string.

Preflight responses enter `collecting_requirements`. Runtime responses append an
immutable request/answer snapshot to node `feedback`, change the node from
`awaiting_input` to `pending`, and return the run to `running`. The prior attempt
is not refunded; redispatch therefore has the next attempt number. Duplicate,
unknown, or otherwise stale responses are rejected.

`respond` is valid only while the run itself is `awaiting_input`; a still-open
request cannot revive a later `blocked` or `stopped` run. If a node is already at
`max_attempts_per_node`, its accepted answer and feedback are retained, but the
node and run become `blocked` instead of creating pending work that cannot be
claimed.

## Lifecycle and controls

State schema v2 permits these run statuses:

`collecting_requirements`, `awaiting_input`, `awaiting_graph_approval`, `running`,
`awaiting_approval`, `pause_requested`, `paused`, `stop_requested`, `stopped`,
`blocked`, and `completed`.

The lifecycle is:

```text
start -> collecting_requirements -> plan -> awaiting_graph_approval
      -> approve -> running -> completed | blocked
running -> awaiting_input -> respond -> running
running -> awaiting_approval -> approve --node -> running
running -> pause_requested -> tick after drain -> paused -> resume -> running
any nonterminal run -> stop_requested -> stop-confirm -> stopped
```

`pause` always enters `pause_requested` and prevents new claims or registrations.
`tick` returns `action: "drain"` while handles remain and changes the run to
`paused` after they drain. `resume` is valid only from `paused`.

No-node `approve` is graph approval only. Once `tick` exposes a ready runtime
human gate, approval provenance is recorded and the coordinator must use
`approve --node <id> --result <file>`; omitting `--node` is rejected.
The supplied node ID must exactly equal persisted `driver.approval_node`; another
ready human node cannot bypass the gate selected by `tick`.

For a runtime human gate, `approve --node <id>` requires exactly one result
source: existing `--result <file>` or inline `--result-json '<json>'`. Supplying
both or neither is rejected before state mutation. The inline UI form is:

```json
{
  "outcome": "approved",
  "evidence": {"source": "graph-flow-ui", "answer": "approved"}
}
```

No-node graph approval accepts neither result source and retains its existing
`approve --repo <path> --run-id <id>` command.

`steer-request --node <id> --message <text>` requires an active running node and
persists `{id,node,task_id,message,status,requested_at,...}`. It does not change
node execution. `steer-ack --steer-id <id> --evidence '<json>'` accepts evidence
whose `status` is `delivered` or `failed`, closes the directive, and likewise does
not change execution.

`stop-request` snapshots and returns every active `{node,task_id}` and enters
`stop_requested`. Confirm with evidence keyed by every snapshotted task handle:

```json
{
  "handles": {
    "worker-123": "completed | cancelled | failed | not_found"
  }
}
```

`stop-confirm --evidence '<json>'` enters `stopped` only when every requested
handle has an allowed terminal status. Missing or nonterminal evidence rejects
the mutation and leaves the run safely in `stop_requested`.
`complete`/node result reduction rejects all late results once run status is
`stopped` or `completed`, before inspecting or changing the node record.

## Coordinator milestones and events

`milestone --event '<json>'` accepts coordinator metadata only:

```json
{
  "name": "tests-green",
  "message": "The portable suite passes.",
  "evidence": {"command": "python -m unittest", "exit_code": 0}
}
```

`name` and `message` are required; optional `evidence` must be an object. Node or
task fields are rejected so milestones cannot impersonate reducer-owned events.
Every persisted event has monotonically increasing `seq`, an `at` timestamp, and
an `event` name. State retains the latest 500 events.

## Cockpit projection

`status --format json` returns projection version 1, not raw state:

```json
{
  "cockpit_version": 1,
  "run_id": "billing-v2",
  "status": "running",
  "phase": "wait",
  "updated_at": "2026-08-23T12:00:00Z",
  "goal": "Ship billing v2",
  "requirements": {
    "goal": "Ship billing v2",
    "success_criteria": ["All acceptance tests pass"],
    "scope": {"included": ["engine"], "excluded": []},
    "constraints": [],
    "verification": ["Run the full suite"],
    "approval_boundaries": ["Approve the graph before dispatch"],
    "assumptions": []
  },
  "max_concurrency": 2,
  "limits": {"max_attempts_per_node": 3, "max_transitions": 100},
  "plan_revision": 2,
  "progress": {"completed": 1, "skipped": 1, "total": 4, "ratio": 0.5},
  "node_counts": {"completed": 1, "pending": 2, "skipped": 1},
  "active_handles": [],
  "open_request": {
    "id": "request-2",
    "kind": "input",
    "answer_type": "single_select",
    "prompt": "Choose a provider",
    "rationale": "Verification depends on the provider",
    "options": ["stripe", "adyen"],
    "scope": "preflight",
    "node": null
  },
  "pending_approval": null,
  "reason": null,
  "workstreams": [
    {
      "id": "engine",
      "title": "Engine",
      "objective": "Ship lifecycle",
      "status": "active",
      "node_counts": {"completed": 1, "running": 1}
    }
  ],
  "nodes": [
    {
      "id": "implement",
      "workstream": "engine",
      "kind": "implementation",
      "status": "completed",
      "objective": "Implement the lifecycle",
      "assigned_role": "worker",
      "priority": "high",
      "resources": ["state-engine"],
      "outcomes": ["done"],
      "transitions": {},
      "failure_outcomes": [],
      "prompt": "Implement the approved lifecycle.",
      "paths": ["scripts/graph_state.py"],
      "verification_commands": ["python3 -m unittest discover -s tests"],
      "depends_on": [],
      "depends_on_any": [],
      "attempts": 1,
      "task_id": "worker-123",
      "acceptance_criteria": ["Lifecycle tests pass"],
      "evidence": {"command": "python3 -m unittest", "exit_code": 0},
      "artifacts": {"changed_paths": ["scripts/graph_state.py"]}
    }
  ],
  "recent_events": [
    {"seq": 12, "at": "2026-08-23T12:00:00Z", "event": "completed_node", "node": "implement"}
  ],
  "state_path": "/absolute/control-plane/billing-v2/state.json"
}
```

`phase` is the real `driver.phase`, not an alias for run `status`. Workstreams and
nodes retain definition order. Each workstream retains static `id`, `title`, and
`objective`, and derives `node_counts` from its member node records. Its status is
`blocked` when any member is blocked or failed; otherwise `active` when any member
is running or awaiting input; otherwise `completed` when it has at least one member
and all are completed or skipped; otherwise `pending`. `requirements` exposes the
complete approved requirements object, including approval boundaries, or `null`
during graphless intake. `max_concurrency` and `limits` expose the effective
immutable execution settings, expanding omitted definition values to reducer
defaults (`1`, `3`, and `100`); both are `null` before planning. Each node merges immutable planned metadata—including
resources, allowed outcomes, transitions, paths, acceptance criteria, and
verification commands, failure outcomes, and task-local prompt—with
its runtime status, attempts, task handle, and the latest result's `evidence` and
`artifacts` (or `null` when absent). `recent_events` is the latest 20 complete,
sequenced public event records in ascending sequence order. An open request
includes its rationale and select options when applicable.

`pending_approval` is separate from `open_request` and is `null` outside an
approval gate. It has this exact shape:

```json
{
  "scope": "graph | node",
  "node": "nullable-node-id",
  "prompt": "Required display prompt",
  "objective": "Nullable graph goal or node objective",
  "allowed_outcomes": ["approved"],
  "kind": "approval",
  "evidence_required": true
}
```

At `awaiting_graph_approval` (and legacy initial graph approval), `scope` is
`graph`, `node` is `null`, the objective is the run goal, and allowed outcomes is
`["approved"]`. At a ready planned `kind: "human"` node, `scope` is `node`, and
prompt, objective, and allowed outcomes come from that node's approved definition.
If its prompt is absent, projection falls back to the node objective and then a
stable `Approve <node-id>.` prompt. Both forms set `evidence_required: true`.

During graphless intake, `workstreams` and `nodes` are empty arrays, while
`progress` and `node_counts` are `null`; phase and recent intake events remain
available. Graph progress is always `(completed + skipped) / total nodes`; a
repair transition that reopens completed work may reduce it.

`status --format text` remains the stable reduced headless view: cockpit version,
run, status, update time, goal, progress, node counts, plan revision, active
handles, open-request prompt, reason, and state path. Expanded phase, graph, result,
and event details are additive to JSON for cockpit consumers and do not alter the
line-oriented text format.

## Dispatch and result envelopes

`tick` returns a dispatch envelope for every selected node:

```json
{
  "run_id": "billing-v2",
  "node": "implement",
  "kind": "implementation",
  "attempt": 2,
  "allowed_outcomes": ["done"],
  "depends_on": [{"node": "inspect", "outcome": "modern"}],
  "depends_on_any": [],
  "input_results": {"inspect": {"outcome": "modern", "evidence": {"detected": "v2"}}},
  "feedback": [{"request_id": "request-2", "request": {}, "answer": "Preserve v1."}],
  "prompt": "Implement the modern integration.",
  "state_path": "/absolute/control-plane/billing-v2/state.json"
}
```

Workers return an allowed outcome. For every node kind, any present `evidence`
must be a non-empty JSON object; decision, implementation, and integration nodes
may omit it. Verification and human results require it. When `artifacts` is
present for any node kind, it must be a JSON object (an empty object is allowed):

```json
{
  "outcome": "passed",
  "evidence": {"command": "python -m unittest", "exit_code": 0},
  "artifacts": {"commit": "abc123", "changed_paths": ["scripts/graph_state.py"]}
}
```

`register` atomically records a durable handle. Alternatively, `claim` records a
pre-launch claim and `attach` replaces it with the external handle. `unclaim`
releases only the exact unattached claim. `complete` accepts only the exact handle
on a running node, preventing stale or duplicate completion from overwriting state.
After `stop-request` snapshots a claim identity, `attach` is rejected so the stop
snapshot cannot lose track of a newly substituted live handle.
If an unrelated failure blocks the graph after a claimed worker has already
launched, `attach` may still replace that exact matching `claim:<id>` with its real
handle. The run remains `blocked`, dispatch stays disabled, and a later
`stop-request` snapshots the real handle. Unrelated claims and stopped runs remain
rejected.

## State v2 and migration

State v2 persists run identity and paths; status and reason; intake and validated
requirements; definition, revision, and approval time; node records; typed request
history; control records; driver phase and active handles; transition count;
sequenced events; and creation/update timestamps.

The loader upgrades schema v1 in memory. It preserves definition, node IDs,
statuses, results, attempts, feedback, revisions, task handles, driver state,
transition count, and prior events. A v1 `awaiting_approval` status maps to
`awaiting_graph_approval`. Every mutating command persists schema v2 and includes
a `state_migrated` event. Read-only `summary`, `status`, `runs`, and `validate`
operate on the in-memory view without rewriting the file.
`validate` reports `graph_planned: false` for valid graphless intake state rather
than treating the absent definition as invalid.

State writes use a short lock and atomic replace. A lock is reclaimed only when
its local PID is provably absent or it is older than 600 seconds.
