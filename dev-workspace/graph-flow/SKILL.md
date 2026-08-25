---
name: graph-flow
description: Use when coordinating a repository implementation from a goal through approved, durable, dependency-aware work across one or more agents, human gates, repair loops, or restart recovery.
compatibility: Python 3.10+; native multi-agent task handles are optional and enable parallel execution and restart inspection.
---

# Graph Flow

Graph Flow turns a repository goal into a reviewed execution graph. The coordinator owns planning, graph state, and dispatch; the reducer (`scripts/graph_state.py`) owns validation, scheduling, and durable lifecycle state; each worker owns one bounded node.

Use it when work has meaningful dependencies, isolated parallel slices, a human decision, independent verification, or a restart/recovery requirement. For a small linear edit, use the host's ordinary implementation workflow.

## Start with the goal, then collect requirements

The user may supply only a goal. Inspect the repository first: its instructions, current architecture, relevant tests, ownership boundaries, and discoverable constraints. Derive what is already knowable. Ask one typed question only when its answer changes scope, design, risk, or acceptance; proceed with stated assumptions when it does not.

Create the graphless intake run, then use the same lifecycle for interactive and headless hosts:

```bash
python3 scripts/graph_state.py start --repo <project-root> --run-id <run-id> \
  --request '{"goal":"<user goal>"}'
python3 scripts/graph_state.py request --repo <project-root> --run-id <run-id> \
  --request '<typed-request-json>'
python3 scripts/graph_state.py respond --repo <project-root> --run-id <run-id> \
  --request-id request-1 --answer '<typed-json-answer>'
```

The exact requirements object, request shape, lifecycle states, and state locations live in [state-schema.md](references/state-schema.md). A run keeps at most one open request. A node that needs input creates a node-scoped request with its exact `--node` and `--task-id`; `respond` records immutable feedback and requeues that node for its next attempt.

## Plan an executable graph

Convert inspected facts and resolved consequential questions into a complete requirements object and a planned definition. Workstreams are readable grouping metadata; nodes are independently executable, bounded units. Every planned definition has top-level `workstreams` objects with `id`, `title`, and `objective`. Every node names its `workstream`, `objective`, `assigned_role`, `priority`, resources, explicit dependency objects, outcomes, transitions, and task-local `prompt`; every executable non-human node also persists acceptance criteria, exact `paths`, and exact `verification_commands`.

Use the rules and full definition shape in [planner-contract.md](references/planner-contract.md). In short:

- Put contracts and decisions before their consumers; use `depends_on` for AND prerequisites and `depends_on_any` for an explicit alternative path.
- Schedule implementations in parallel only after all required dependencies are complete and their declared resources are disjoint. Follow parallel slices with integration, then verification.
- Set priority from impact and urgency: `critical`, `high`, `normal`, or `low`. The reducer resolves otherwise-ready work by priority, direct downstream unlock count, then definition order; dependencies, resource locks, and capacity remain binding.
- Keep static dependencies acyclic. Use bounded runtime `transitions` for a repair loop and configure `limits` for attempts and total transitions.

Submit a reviewed plan and hold the graph at its approval boundary:

```bash
python3 scripts/graph_state.py plan --repo <project-root> --run-id <run-id> \
  --definition '<planned-definition-json>' --requirements '<requirements-json>'
python3 scripts/graph_state.py approve --repo <project-root> --run-id <run-id>
```

`plan` moves the run to `awaiting_graph_approval`. Present the requirements, workstreams, nodes, dependencies, priorities, resource locks, risks, and proposed approval boundaries before the no-node `approve`. The approved definition is immutable during execution; a bounded repair follows its recorded transition and feedback rather than rewriting the graph.

## Dispatch through the durable reducer

After approval, the coordinator follows this control loop:

1. Run `tick` and use only `action: "dispatch"` envelopes for executable non-human work. Render `await_input`, `await_graph_approval`, and `await_approval` as coordinator/human interaction rather than worker dispatch.
2. For every dispatch envelope, either create a durable native handle and `register` it, or `claim` before launch and `attach` the returned handle immediately afterward.
3. Wait for known handles, save each worker's result JSON, and run `complete` with the exact node and handle.
4. Run `tick` immediately after each completion. Handle its `await_input`, `await_graph_approval`, `await_approval`, `drain`, `blocked`, and `complete` actions by their persisted state.

Read [driver-contract.md](references/driver-contract.md) for command-level handle, restart, pause, stop, and recovery rules. Generate the worker prompt from the returned dispatch envelope plus the immutable fields in [worker-envelope.md](references/worker-envelope.md); pass `input_results` and `feedback` through unchanged.

## Runtime selection

Use the host-specific mapping in [runtime-adapters.md](references/runtime-adapters.md). Codex maps planned roles to its built-in explorer, worker, and default threads and shows the durable state in its native panel. Prime Agent dispatches through `rlm()`. Pi core runs one node at a time. `pi-subagents` runs one async invocation per node and persists its run ID/status for wait, resume, steer, stop, and worktree operations. Every host has a JSON/headless path using the same reducer commands and envelopes.

## End-to-end example

User: “Add JWT refresh to this API.” The coordinator inspects the auth code and tests, then starts `jwt-refresh` with that goal. It asks one `single_select` preflight question only if the existing refresh-token storage policy is genuinely ambiguous. Its requirements name token rotation, compatibility, and `pytest -q` as success/verification criteria. It plans workstream `auth-contract` for an `explore-storage` node (`explorer`, `high`) and `auth-implementation` for `implement-refresh` (`worker`, `critical`, depends on `explore-storage:done`, resource `src/auth`) plus `refresh-integration` (`default`, `high`) and `verify-refresh` (`reviewer`, `high`). A separate `approve-token-policy` human node gates an irreversible persistence choice. The implementation and a disjoint client-test node may run together once their inputs are ready; integration follows them and verification follows integration. Each dispatched worker receives its immutable envelope, repository/worktree, exclusive resource ownership, criteria, test command, allowed outcomes, and JSON result contract. The displayed graph is approved with `approve`; only then do Codex threads, Prime `rlm()`, Pi core, or `pi-subagents` execute their adapter path. A verifier’s evidence-bearing `rejected` result follows its bounded transition back to repair.

## Operating boundaries

Workers return concise evidence and artifacts for their assigned node. The coordinator alone calls reducer mutations such as `register`, `claim`, `attach`, `complete`, `approve`, `respond`, and `block`; workers use their envelope to produce a result, while the reducer remains the shared transition authority. Verifiers assess supplied artifacts and criteria independently, and their evidence becomes repair feedback.

Use `summary`, `status --format json`, and `reconcile` after a restart. Inspect every persisted external handle, complete known results, keep known active work, and block an irrecoverably unavailable handle with its specific cause. An unattached claim becomes eligible for `unclaim` only after inspection establishes that the external work never started or cannot exist.
