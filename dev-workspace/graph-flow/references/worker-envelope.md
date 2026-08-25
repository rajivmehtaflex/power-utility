# Worker Envelope Contract

`tick` emits reducer-owned envelopes. The coordinator wraps only `action: "dispatch"` envelopes for executable non-human nodes in an immutable, host-neutral worker envelope and sends one to its assigned native task. `await_input`, `await_graph_approval`, and `await_approval` are coordinator/human interactions, so they render a request or approval gate and receive no worker prompt.

## Required prompt envelope

```json
{
  "dispatch": {
    "run_id": "jwt-refresh",
    "node": "implement-refresh",
    "kind": "implementation",
    "attempt": 1,
    "allowed_outcomes": ["done", "failed"],
    "depends_on": [{"node":"inspect-storage","outcome":"done"}],
    "depends_on_any": [],
    "input_results": {"inspect-storage":{"outcome":"done","evidence":{}}},
    "feedback": [],
    "prompt": "Preserve existing token compatibility.",
    "state_path": "/absolute/path/state.json"
  },
  "role": "worker",
  "objective": "Add refresh rotation to the API.",
  "repository": "/absolute/project-root",
  "worktree": "/absolute/assigned-worktree",
  "paths": ["src/auth/refresh.py", "tests/auth/test_refresh.py"],
  "exclusive_ownership": {"access":"write","resources":["src/auth"],"paths":["src/auth/refresh.py", "tests/auth/test_refresh.py"]},
  "prohibited_scope": ["other declared resources", "graph state mutation or recursive dispatch"],
  "acceptance_criteria": ["Rotation behavior is covered by tests."],
  "verification_commands": ["pytest -q"],
  "result_contract": "Return the JSON object below as the whole result."
}
```

The coordinator takes `dispatch` directly from `tick` and fills role, objective, criteria, and resources from the approved definition. It copies `paths` and `verification_commands` verbatim from that node's persisted non-empty lists, then supplies the exact repository/worktree, exclusive ownership, non-owned scope, upstream `input_results`, accumulated `feedback`, allowed outcomes, and result format. It derives neither field from `resources`, acceptance criteria, or repository inspection. This envelope is immutable for the attempt: a worker reports facts and its allowed outcome; the coordinator reduces those facts and determines any next node.

`prohibited_scope` records a positive boundary for the worker: a mutating `worker` or `default` node receives `exclusive_ownership.access: "write"` for its assigned paths/resources, while an `explorer` or `reviewer` receives the same declared artifacts with `access: "read"` and returns findings or verification evidence. State/dispatch authority stays with the coordinator. Each worker returns its result to that coordinator rather than creating nested work; a reviewer receives the implementation artifact, diff/commit, criteria, and commands with evaluation responsibility rather than implementation ownership.

## Result envelope

Every worker returns one JSON object:

```json
{
  "outcome": "done",
  "evidence": {
    "command": "pytest -q",
    "exit_code": 0,
    "observed": "42 passed"
  },
  "artifacts": {
    "commit": "abc123",
    "changed_paths": ["src/auth/refresh.py", "tests/test_refresh.py"]
  }
}
```

`outcome` is one of the dispatched `allowed_outcomes`. Use objects for `evidence` and `artifacts`. Verification and human outcomes include non-empty `evidence`; a rejected verifier result includes the actual failed command/output facts so the reducer can retain and pass them to repair. Keep large logs and secrets outside state; put a stable path or artifact identifier in the envelope.

The coordinator writes the object to a result file and invokes:

```bash
python3 scripts/graph_state.py complete --repo <project-root> --run-id <run-id> \
  --node <node-id> --task-id <native-handle> --result <result.json>
```

## Runtime input

A worker that needs a consequential answer asks the coordinator for a typed node-scoped request. The coordinator calls:

```bash
python3 scripts/graph_state.py request --repo <project-root> --run-id <run-id> \
  --node <node-id> --task-id <native-handle> --request '<request-json>'
```

That exact handle is released, the node enters `awaiting_input`, and `respond` appends the immutable answer to its `feedback` before requeueing the node. Its redispatch uses the next attempt number and includes the preserved feedback.
