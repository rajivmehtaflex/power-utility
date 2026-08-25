# Runtime Adapters

This package uses the Agent Skills format: portable Markdown plus a Python standard-library reducer. The adapter is a thin translation layer between a `tick` dispatch envelope and one host-native task. It retains host SDKs, credentials, UI syntax, and worktree mechanics outside this package.

## Common role mapping

| Planned role | Responsibility | Worker prompt emphasis |
| --- | --- | --- |
| `explorer` | Read-only repository discovery, feasibility, and facts | Sources inspected, constraints, and no implementation artifact required |
| `default` | Bounded coordination, integration, or general task | Declared files/resources and integration criteria |
| `worker` | Isolated implementation slice | Exclusive ownership, changed paths, and verification evidence |
| `reviewer` | Independent verification | Artifact/diff, criteria, commands, and evidence-bearing outcome |
| `human` | Consequential decision or approval | Render an Action Center/native approval gate with exact action, impact, rollback, and evidence record; no worker prompt |

The generated prompt contract is shared across hosts in [worker-envelope.md](worker-envelope.md). Planned roles specify responsibility; a host can map several executable roles to one native capability when it preserves the contract. A human node, typed input, graph approval, and runtime approval remain coordinator/UI actions rather than native agent dispatches.

## Headless approval projection

Every headless adapter must render or consume `status --format json` for graph
approval and the full cockpit. That stable projection includes requirements,
`pending_approval`, workstreams, nodes (including declared resources and task
prompts), effective execution limits, and recent events, along with the other
run state needed to review a plan safely. `status --format text` deliberately
contains only a compact operational summary; it is not sufficient to review or
approve a graph.

## Codex

| Contract | Mapping |
| --- | --- |
| Native execution | Use built-in `explorer` threads for discovery; `worker` threads for isolated implementations; `default` threads for integration/review when appropriate. Create them only for executable `action: "dispatch"` envelopes. The coordinator remains the default orchestration thread. |
| Handle | Persist the Codex task/thread ID with `register`, or use `claim`/`attach` when the ID arrives after launch. |
| Worktree | Give concurrently mutating nodes separate worktrees when their resources are disjoint; integration uses the coordinator-selected target worktree. |
| UI/headless | Use the native Codex panel for graph/input/human approval gates when available. The fallback uses complete `status --format json`, request/approval JSON, and result paths, and receives the same typed JSON responses. `status --format text` is summary-only. |
| Recovery | Full tier when the persisted task/thread can be inspected; otherwise managed tier and a precise `block` reason. |

## Prime Agent

| Contract | Mapping |
| --- | --- |
| Native execution | Call `rlm()` once for each executable `action: "dispatch"` envelope and generated worker prompt. Map explorer/worker/reviewer intent into that invocation's role instructions. |
| Handle | Persist the `rlm()` run identifier via the registration or claim/attach lifecycle. |
| Worktree | Pass the planned repository/worktree to each run; use isolated worktrees for disjoint concurrent mutation. |
| UI/headless | A Prime Action Center/native UI renders graph approval, typed requests, and human nodes. Its headless fallback consumes and emits the complete reducer JSON contract; `status --format text` is summary-only. |
| Recovery | Use full tier only when the run identifier supports status/inspection after restart; otherwise use managed tier. |

## Pi core

| Contract | Mapping |
| --- | --- |
| Native execution | Run the coordinator and one executable `action: "dispatch"` node sequentially in the active Pi process. Roles remain prompt responsibilities rather than separate native agent types. |
| Handle | Use a coordinator-owned sequential invocation identifier and reduce its result before the next `tick`. |
| Worktree | Use the active worktree; serialize mutating nodes. |
| UI/headless | Render graph approval, typed requests, and human gates from complete `status --format json` in the terminal. Standard input/output JSON is the complete fallback; `status --format text` is summary-only and cannot approve a graph. |
| Recovery | After an interruption, reconcile first. If Pi core cannot inspect the claimed/running sequential handle, call `block` with its exact handle and cause; it never redispatches that uncertain work. |

## pi-subagents

| Contract | Mapping |
| --- | --- |
| Native execution | Start one async subagent run per selected executable `action: "dispatch"` envelope. Store its run ID and status as the native task handle. |
| Handle | Use run IDs for status inspection, `wait`, `resume`, `steer`, and `stop`; acknowledge persisted steering through `steer-ack`. |
| Worktree | Create/select a worktree per concurrently mutating node and include that exact location in its worker prompt. |
| UI/headless | A Pi extension renders graph approval, typed requests, and human gates in the cockpit/Action Center. The portable fallback is the complete reducer JSON projection, request/approval input, and result envelopes; `status --format text` is summary-only. |
| Recovery | Full tier only when run IDs can be inspected and resumed; a lost/uninspectable run enters managed recovery and is blocked with cause. |

## Adding a host

Choose a capability tier from [driver-contract.md](driver-contract.md), map native agent roles to the common responsibility table, and implement `dispatch`, `wait`, and `inspect` around the reducer commands. The portable graph, state file, prompt envelope, and result envelope remain unchanged across hosts.
