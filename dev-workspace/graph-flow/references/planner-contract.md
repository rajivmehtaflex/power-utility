# Planner Contract

The planner converts a goal and repository facts into a requirements object and a definition that `graph_state.py plan` accepts. It makes assumptions visible, creates a bounded executable graph, and presents that graph for approval before dispatch.

## Requirements record

`plan --requirements` accepts exactly:

```json
{
  "goal": "non-empty string",
  "success_criteria": ["non-empty string"],
  "scope": {"included": [], "excluded": []},
  "constraints": [],
  "verification": ["non-empty string"],
  "approval_boundaries": [],
  "assumptions": []
}
```

Start from the supplied goal and inspect repository instructions, source, tests, configuration, and version control facts. Capture discovered facts in the relevant requirements field. A missing answer deserves a typed `request` when it materially changes the plan, external effect, security posture, or acceptance. A non-consequential gap becomes a stated assumption.

## Planned definition

```json
{
  "version": 1,
  "workstreams": [{"id":"api","title":"API refresh","objective":"Ship JWT refresh safely."}],
  "max_concurrency": 2,
  "limits": {"max_attempts_per_node": 3, "max_transitions": 100},
  "nodes": [
    {
      "id":"inspect-storage",
      "kind":"decision",
      "workstream":"api",
      "objective":"Identify the existing refresh-token storage policy.",
      "assigned_role":"explorer",
      "priority":"high",
      "acceptance_criteria":["Report the current storage policy and compatibility constraints."],
      "paths":["src/auth/refresh_store.py"],
      "verification_commands":["pytest -q tests/auth/test_refresh_store.py"],
      "outcomes":["done","failed"],
      "transitions":{},
      "failure_outcomes":["failed"],
      "resources":["auth-policy"],
      "prompt":"Inspect only; report sources and findings."
    },
    {
      "id":"implement-refresh",
      "kind":"implementation",
      "workstream":"api",
      "objective":"Add refresh rotation to the API.",
      "assigned_role":"worker",
      "priority":"critical",
      "acceptance_criteria":["Rotation behavior is covered by tests."],
      "paths":["src/auth/refresh.py","tests/auth/test_refresh.py"],
      "verification_commands":["pytest -q tests/auth/test_refresh.py"],
      "outcomes":["done","failed"],
      "depends_on":[{"node":"inspect-storage","outcome":"done"}],
      "transitions":{},
      "failure_outcomes":["failed"],
      "resources":["src/auth"],
      "prompt":"Preserve existing token compatibility."
    }
  ]
}
```

`workstreams` organize the plan; nodes are the dispatchable units. A planned node uses one declared workstream and one `assigned_role` from `explorer`, `default`, `worker`, `reviewer`, or `human`. `priority` is `critical`, `high`, `normal`, or `low`. Non-human nodes carry one or more acceptance criteria, a non-empty `paths` string list, and a non-empty `verification_commands` string list; a human node uses role `human` and may omit those execution fields. `paths` names the exact owned/read artifact locations and `verification_commands` names the exact commands for that node. They are persisted in the approved definition and are copied into the worker envelope; an adapter does not infer either from `resources`, acceptance criteria, or repository context. `kind` is `decision`, `implementation`, `verification`, `integration`, or `human`. Omit `depends_on_any` when no OR prerequisite exists; an explicit empty array is invalid.

## Graph rules

| Concern | Planning contract |
| --- | --- |
| Decisions and contracts | Place their node before every consumer and name the expected source outcome in `depends_on`. |
| Parallel implementations | Use separate nodes only when dependencies are complete and resources are disjoint. Every mutable file set or side effect receives one canonical logical resource key. |
| Paths and verification | Persist each executable node's exact non-empty `paths` and `verification_commands`; generated worker prompts copy them verbatim. |
| Integration and verification | Place integration after parallel implementation slices; place independent verification after integration. Give the verifier evidence sources and criteria, not implementation ownership. |
| Conditional work | `depends_on` is AND; `depends_on_any` is OR. An unmet selected outcome skips its dependent. Use `transitions` to route a recorded runtime outcome. |
| Repair | Route a verifier's `rejected` outcome to the bounded repair node, preserve its feedback, and configure attempts/transitions limits. |
| Failure | Put terminal negative outcomes in `failure_outcomes`; the reducer records `blocked` rather than treating them as success. |
| Scheduling | The reducer considers ready human/input work, then priority, direct downstream unlock count, then declaration order. Dependencies, resources, and `max_concurrency` remain binding. |

Static dependency edges must form an acyclic graph. Runtime transitions may revisit repair work within `limits.max_attempts_per_node` and `limits.max_transitions`. Resource keys act as exclusive locks; use one key for overlapping path-like resources rather than sibling/prefix variants.

## Review before approval

The plan view names the goal, requirements/assumptions, workstreams, each node's role/objective/criteria, dependency outcomes, priority, resources, tests, transitions, and approval boundaries. Send it through:

```bash
python3 scripts/graph_state.py plan --repo <project-root> --run-id <run-id> \
  --definition '<definition-json>' --requirements '<requirements-json>'
python3 scripts/graph_state.py validate --repo <project-root> --run-id <run-id>
```

At `awaiting_graph_approval`, present the reviewed graph. A no-node `approve` records graph approval and opens scheduling. A ready runtime human node is a different gate and uses `approve --node <node-id> --result <result.json>`.
