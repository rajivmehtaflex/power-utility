# Source-Grounded Plan-Mode / Pi Extension Architecture

Use this reference when planning a new Pi extension that changes agent behavior, tool access, conversation phases, or implementation handoff. It records the reusable method learned from exploring a mature `pi-plan-mode` implementation with CodeGraph MCP; it is not a copy of that package.

## Exploration sequence

1. Confirm the repository path and run `codegraph status -j`.
2. Inspect the package manifest and extension entrypoint.
3. Use CodeGraph MCP queries for the complete runtime path, not only the slash command:
   - extension factory and registrations (`registerCommand`, `registerTool`, `registerFlag`);
   - lifecycle hooks (`session_start`, `before_agent_start`, `tool_call`, `context`, `agent_end`, `agent_settled`, `session_shutdown`);
   - state types, restore/persist functions, and transition helpers;
   - tool classification, active-tool selection, and blocked-command checks;
   - completion/question tool schemas and execution results;
   - same-session and fresh-session implementation handoff;
   - existing tests and their mock Pi/context harness.
4. Cross-check the returned source against on-disk files and tests. Treat truncated MCP output as incomplete; issue a narrower query for omitted symbols.
5. Build a source/evidence table before writing the plan: behavior, file/symbol anchor, invariant, test target.

A useful query shape is:

```text
<package> factory entrypoint command registration lifecycle hooks state transitions
<package> tool policy active tools blocked calls question completion persistence handoff tests
```

## Mind model

Model Plan mode as a policy-controlled state machine, not as a prompt-only feature:

```text
command/flag -> state transition -> effective tools -> enforcement hook -> prompt contract
                                      |                         |
                                      +-> question tool         +-> completion tool -> ready decision
                                                                  |
                                            implement/save/export/exit handoff
```

Keep these concerns separate in the plan:

- **Pure state:** phases, accepted plan, previous tools, active handoff metadata.
- **Policy:** which built-in/custom tools are read-only, limited, opt-in, or blocked.
- **Prompt:** exploration, intent clarification, implementation design, and completion rules.
- **Pi boundary:** registration, lifecycle events, `setActiveTools`, `appendEntry`, UI, and session APIs.
- **Handoff:** restore normal authority before implementation and preserve the plan on failure.

The prompt is guidance. Active-tool filtering is convenience. The `tool_call` hook is the enforcement boundary.

## Safe incremental roadmap

Recommend an isolated sibling package or temporary command while learning. Never have a new package and an existing stable package register the same `/plan` command at once.

Build vertical slices in this order:

1. package entrypoint and registration test;
2. pure state transition tests;
3. exact tool snapshot/restore, including an intentionally empty tool list;
4. blocked-tool `tool_call` tests;
5. short Plan system prompt and `/plan` command routes;
6. structured `plan_mode_complete` with validation, bounded size, structured details, and termination;
7. ready presentation after agent settlement, guarded against duplicates/stale sessions;
8. same-session implementation handoff and rollback on send failure;
9. persistence/resume from the active session branch, failing closed on malformed state;
10. lazy UI, settings, export, limited Bash, and fresh-session handoff only after the core is reliable.

Do not include limited Bash in the MVP unless its parser is fail-closed and backed by mutation/expansion/redirect regression tests. Prefer omitting Bash over shipping a permissive shell filter.

## Plan invariants to require

- planning cannot mutate files or run unsafe commands;
- completion is explicit, non-empty, normalized, bounded, and accepted only in planning;
- duplicate completion/settlement events present readiness once;
- exit restores the exact pre-plan tool list and thinking ownership;
- failed implementation delivery restores the ready plan;
- state restoration uses only the active session branch and validates every field;
- every asynchronous UI/question/handoff continuation checks session/workflow freshness after `await`;
- non-interactive modes return an observable result or error instead of waiting for UI.

## Test matrix

Require tests for registration, command routing, state transitions, tool policy, completion/question validation, active-tool restoration, settlement idempotence, handoff rollback, malformed resume state, shutdown cancellation, and non-interactive behavior. Add safe-shell and fresh-session tests only when those features are enabled.

Use the repository's actual mock harness and test runner. Do not claim a plan is source-grounded from a compile check alone; the plan should name the lifecycle and failure-path tests that prove the mode's authority boundaries.
