# Profile-Resolution Decision Flowchart

Visual companion to SKILL.md §"Profile-resolution procedure" and §"Task-driven profile resolution".
Follow top-to-bottom for each requested role.

## Two entry points

The flowchart has two entry points depending on how the request arrives:

1. **Task-driven** (v2.1+): User provides a plain-language task description. The agent analyzes it against the role catalog to infer which roles are needed.
2. **Role-driven** (v1.0+): Roles are already known (from orchestrator decomposition, explicit request, or registry check).

## Main decision tree

```
 ENTRY A: Task-driven                    ENTRY B: Role-driven
 ┌──────────────────────────┐            ┌─────────────────────────┐
 │ User provides task text   │            │ Roles already known     │
 │ "Build monthly report..." │            │ (orchestrator, manual)  │
 └─────────────┬────────────┘            └────────────┬────────────┘
               │                                       │
 ┌─────────────▼─────────────┐                        │
 │ Run: --task "<task text>" │                        │
 │ Script prints role        │                        │
 │ catalog with capabilities │                        │
 └─────────────┬────────────┘                        │
               │                                       │
 ┌─────────────▼─────────────┐                        │
 │ AGENT INFERS ROLES        │                        │
 │ Match task capabilities   │                        │
 │ to role capabilities in   │                        │
 │ the catalog               │                        │
 └─────────────┬────────────┘                        │
               │                                       │
               └───────────────┬───────────────────────┘
                               │
                    ┌──────────▼───────────┐
                    │ Step 1: Discover     │
                    │   hermes profile list│
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │ Step 2: Normalize    │
                    │ (map to registry key)│
                    └──────────┬───────────┘
                               │
                        ┌──────▼──────┐
                        │ Role in     │
                        │ registry?   │
                        └──┬───────┬──┘
                         NO│       │ YES
                   ┌───────▼───┐ ┌─▼───────────────┐
                   │ → BLOCKED │ │ Profile exists? │
                   └───────────┘ └──┬──────────┬───┘
                              YES │          │ NO
                         ┌────────▼─┐ ┌──────▼──────────┐
                         │ VERIFY   │ │ Check mode:     │
                         │ readiness│ │ ├ reuse-only    │
                         └──┬────┬──┘ │ │  → BLOCKED    │
                       READY│    │NO  │ ├ approval-req  │
                    ┌───────▼┐ ┌─▼────│ │  → BLOCKED    │
                    │REUSED  │ │NEEDS │ └ provision     │
                    └────────┘ │UPDATE│   -approved?    │
                               └──────┘         │
                                       ┌────────▼────────┐
                                       │ PROVISION:      │
                                       │ create profile  │
                                       └────────┬────────┘
                                                │
                                       ┌────────▼────────┐
                                       │ APPLY CONFIG    │ ← v3.0
                                       │ OVERRIDES       │
                                       │ (deep-merge     │
                                       │  into config)   │
                                       │ SKIP model/keys │
                                       └────────┬────────┘
                                                │
                                       ┌────────▼────────┐
                                       │ VERIFY          │
                                       └────────┬────────┘
                                          ┌─────▼─────┐
                                         YES│         │ NO
                                    ┌───────▼┐ ┌──────▼──┐
                                    │CREATED │ │ FAILED  │
                                    └────────┘ └─────────┘
```

## Output states summary

| State | Meaning | `ready_for_dispatch` | `profile_created` |
|---|---|---|---|
| `reused` | Existing profile found and verified | `true` | `false` |
| `created` | Missing profile provisioned and verified | `true` | `true` |
| `needs_update` | Profile exists but fails verification | `false` | `false` |
| `blocked` | No approved template, policy forbids, or approval needed | `false` | `false` |
| `failed` | Creation or verification operation errored | `false` | `false` |

## Phase 1 boundary contract

Every readiness report MUST include:
- `execution_started: false` — the manager never starts workers
- `phase: "profile-preparation"` — explicit phase marker

If either field is missing or contradicts Phase 1, the output is invalid.
