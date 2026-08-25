# Portable Coordinator Driver Contract

The adapter provides execution; `scripts/graph_state.py` provides the deterministic control plane. A coordinator is the sole reducer client and preserves the returned state as the authority for selection, recovery, and reporting.

## Adapter interface

| Operation | Coordinator input | Adapter result |
| --- | --- | --- |
| `dispatch(envelope, worker_prompt)` | Immutable envelope and generated worker prompt | Native durable handle, or a launch result after a prior claim |
| `inspect(handle)` | Persisted native handle | `running`, completed result, or `unavailable` with cause |
| `wait(handles)` | Known active handles | Completed handle(s) and their result envelope(s) |
| `deliver_steer(handle, message)` | Persisted steering directive | Evidence with `status: delivered` or `failed` |
| `stop(handle)` | Handle included in stop snapshot | Terminal handle state for `stop-confirm` |

The native handle is opaque to the reducer. It is stable enough for the adapter to inspect, wait, steer, or stop it within the capability tier it declares.

## Handle lifecycle

Use the registration path when a host can create a handle before execution:

```text
tick dispatch -> create paused native task -> register --node --task-id -> start task
```

Use the claim path when the host returns a handle only as it launches:

```text
tick dispatch -> claim --node --claim-id -> launch -> attach --node --claim-id --task-id
```

For each native completion, persist a result JSON file and reduce exactly that registered handle:

```bash
python3 scripts/graph_state.py complete --repo <project-root> --run-id <run-id> \
  --node <node-id> --task-id <native-handle> --result <result.json>
```

`register` and `claim` change a ready node to running; `attach` replaces only the matching `claim:<claim-id>` identity. `complete` accepts only the exact running handle. The coordinator calls `tick` after every reduction, including an out-of-order completion.

## Tick action contract

`tick` returns an `action` plus `nodes`. In every action, `nodes` contains node IDs, never native task IDs. The adapter retains the durable node-to-task-ID mapping from `register`/`attach`; `reconcile` returns the same mapping as `active_tasks`, and `status --format json` exposes it as `active_handles`.

| `tick` action | Reducer status / fields | Coordinator behavior |
| --- | --- | --- |
| `collect_requirements` | `collecting_requirements`; no nodes | Inspect, request consequential input, or call `plan`. |
| `await_input` | `awaiting_input`; no nodes | Render the one persisted typed request and call `respond`. |
| `await_graph_approval` | `awaiting_graph_approval`; no nodes | Present the immutable pre-run graph and use no-node `approve` after approval. |
| `await_approval` | `awaiting_approval`. The first runtime human selection returns `nodes: [<human-node>]`, its envelope, and persists `driver.approval_node`. A later tick in that status returns `nodes: []`. Legacy `init` graph approval also returns `nodes: []` and has no `driver.approval_node`. | Inspect persisted `driver.approval_node`: when present, render that human gate and call `approve --node <id> --result <file>`; when absent, render legacy initial graph approval and call no-node `approve`. |
| `dispatch` | `running`; `nodes` identifies executable non-human work and `envelopes` supplies each dispatch | Create/register or claim/attach one native task for each selected node. |
| `wait` | `running`; `nodes` identifies active nodes | Wait through the durable node-to-task-ID mapping, reduce each completed result, then `tick`. |
| `drain` | `pause_requested`; `nodes` is the sorted set of active **node IDs** | Wait for those mapped task IDs to complete; reduce results and continue `tick` without new registration or claim. |
| `paused` | `paused`; no nodes | Hold the run until `resume` changes it to `running`. |
| `stop` | `stop_requested`; `nodes` is the sorted set of currently active **node IDs** | Stop/inspect their mapped task IDs. Use the `stop-request` snapshot to supply terminal evidence for every original handle to `stop-confirm`. |
| `stopped` | `stopped`; no nodes | Terminal state: report it and create no additional work. |
| `blocked` | `blocked`; `reason` | Report the durable reason and stop dispatching. |
| `complete` | `completed`; no nodes | Terminal success: report final state and stop dispatching. |

## Required driver loop

1. During intake, `start`, inspect, ask consequential typed requests with `request`, and collect answers with `respond`.
2. Build requirements and the planned definition, call `plan`, present the graph, and use no-node `approve` only after graph approval.
3. Call `tick`. For `dispatch`, create one native task per returned executable non-human envelope using the handle lifecycle above. `await_input`, `await_graph_approval`, and `await_approval` render persisted interaction; they create no native agent task. For `await_approval`, load persisted `driver.approval_node` before choosing the no-node or `--node` approval command.
4. For `wait`, await known handles. For each completion, write its JSON result, invoke `complete`, and return to `tick`.
5. For `collect_requirements`, inspect and either issue one consequential typed request or build the plan. For `await_input`, render the persisted request and reduce its typed answer with `respond`. For `await_graph_approval`, present the planned graph and request no-node approval. For `await_approval`, inspect persisted `driver.approval_node`: a present ID identifies a runtime human node and uses `approve --node <id> --result <result.json>`; an absent ID is legacy `init` graph approval and uses no-node `approve`.
6. For `drain`, map the returned node IDs to their durable task IDs, wait, reduce results, and continue `tick` until `pause_requested` advances to `paused`. For `stop`, map its current node IDs to task IDs and request their termination; use the original `stop-request` snapshot to provide terminal evidence for every handle to `stop-confirm`. For `paused`, `stopped`, `blocked`, or `complete`, follow the terminal/hold behavior in the tick-action table.

Use controls with their reducer lifecycle in [state-schema.md](state-schema.md): `pause` is valid from `running` and records `pause_requested`; `tick` returns `drain` while handles remain and changes the run to `paused` once they drain; `resume` is valid only from `paused` and returns it to `running`. `stop-request` snapshots every active handle and records `stop_requested`; `tick` returns `stop`. `stop-confirm --evidence '<json>'` reaches `stopped` only when every snapshotted handle has a terminal `completed`, `cancelled`, `failed`, or `not_found` status. Incomplete terminal evidence leaves the reducer in `stop_requested`; an adapter that cannot establish a safe terminal state records a specific `block` reason rather than continuing or redispatching. The adapter writes steering delivery evidence through `steer-ack`.

## Restart recovery

On a new coordinator context, run:

```bash
python3 scripts/graph_state.py reconcile --repo <project-root> --run-id <run-id>
```

For every returned `active_tasks` handle, inspect it using the adapter. Reduce a completed known result; retain and wait for known running work; call `block --reason <specific-handle-and-cause>` for unavailable work. For an entry listed in `unattached_claims`, inspection establishes whether its external launch can exist. A confirmed absent launch is released with `unclaim --node <id> --claim-id <id>`; an uncertain launch remains blocked for explicit recovery. Then call `tick`.

## Capability and headless tiers

| Tier | Handles and isolation | Recovery contract | Headless contract |
| --- | --- | --- | --- |
| Full | Durable handles, isolated workers, inspect/wait/steer/stop | Reconcile each handle and resume known work | Emit reducer JSON and accept typed JSON answers/results |
| Managed | Child tasks with handles inspectable only while live | Run live tasks normally; block unresolved work after an uninspectable restart | Same commands, with a visible unavailable-handle reason |
| Sequential | One coordinator execution at a time | After interruption, inspect a claimed/running handle when the host can; otherwise block it rather than redispatching | Invoke one envelope, write one result JSON, then `complete` and `tick` |

`max_concurrency` is an upper bound. Resource keys, dependency outcomes, capacity, and approval/input states determine when a host dispatches. The adapter may lower concurrency to match its tier.
