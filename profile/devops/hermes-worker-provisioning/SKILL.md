---
name: hermes-worker-provisioning
description: Use when provisioning Hermes worker profiles.
license: MIT
metadata:
  author: Hermes Agent
  hermes_tags: hermes, kanban, profiles, provisioning, verification, terminal, worker
  platforms: linux, macos, windows
  version: 1.0.0
---

# Hermes Worker Provisioning

Use this skill when a task requires a reusable Hermes worker profile to be created, reused, activated, or verified for a Kanban workflow.

This skill focuses on the lifecycle of **worker profiles**: discovering the live catalog, selecting the correct role, creating only approved profiles, and verifying that the active profile is actually ready to work.

## When to use

Use when:

- A Kanban task needs an existing or newly provisioned worker profile
- You must verify that a profile is CLI-first and terminal-enabled
- A profile exists but its config or toolset readiness is unclear
- You need to confirm a worker profile is ready before handoff
- You are preparing multiple interacting worker roles for a project

Do not use when:

- You are decomposing the task graph itself — use a Kanban orchestrator skill
- You are editing business logic inside the worker project
- You only need a one-off answer and no profile lifecycle work

## Core workflow

### 1) Discover the live catalog first

Always inspect the actual installed profiles before assuming a name exists.

```bash
hermes profile list
```

Use the exact existing profile name when reusing a worker.

### 2) Normalize the requested role

Map plain-language work to a canonical role/profile key, such as:

- `database-architect`
- `data-generation-specialist-documenter`
- `reviewer`
- `data-analyst`

Do not invent arbitrary names from task text.

### 3) Reuse before creating

If an approved profile already exists:

- reuse it exactly
- verify it before handoff
- do not create a duplicate

### 4) Provision only from an approved template

If creation is allowed:

- create the profile from an approved base/template
- apply only declared worker overrides
- keep `model` and provider routing out of profile overrides unless the workflow explicitly manages them elsewhere
- never copy secrets or broad session state by default

### 5) Activate and verify the live profile

A newly created profile may not expose its config path until it is activated.

Recommended verification sequence:

```bash
hermes profile use <profile>
hermes config path
hermes config show
hermes tools list --platform cli
hermes profile show <profile>
```

Use `hermes profile use <profile>` when you need the profile-specific config path to materialize before validation.

### 6) Treat verification as multi-source, not single-source

Do not rely on only one command. Confirm:

- the profile exists
- the active config path resolves to the profile directory
- the worker configuration matches intent
- the CLI toolset includes the needed categories
- the profile is terminal-first and ready for handoff

## Pitfalls

1. **Assuming creation instantly materializes config files.** On some installs, the profile-specific `config.yaml` becomes visible only after `hermes profile use <profile>`.
2. **Trusting a single readiness field.** A checker may report a toolset status that is only advisory. Cross-check with `hermes config show` and `hermes tools list --platform cli`.
3. **Putting provider/model routing in worker overrides.** Keep deployment metadata separate unless the profile manager explicitly supports that path.
4. **Creating duplicates instead of reusing.** One canonical worker name should map to one reusable role.
5. **Treating `hermes profile show` as sufficient verification.** It confirms existence, not full runtime readiness.

## Support files

- `references/session-provisioning-notes.md` — session-derived notes on profile activation, config-path materialization, and verification pitfalls.

## Suggested handoff format

```json
{
  "profile": "database-architect",
  "action": "created",
  "ready_for_dispatch": true,
  "verification": {
    "exists": true,
    "config_path_resolved": true,
    "tools_ok": true
  }
}
```

Keep this skill class-level: it should apply to any future Hermes worker profile provisioning workflow, not just one project.
