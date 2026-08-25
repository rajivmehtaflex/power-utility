---
name: kanban-profile-manager
description: Use when managing Kanban profile reuse or provisioning.
license: MIT
metadata:
  author: Hermes Agent
  hermes_related_skills: kanban-orchestrator, kanban-worker
  hermes_tags: kanban, profiles, lifecycle, provisioning, routing, idempotency
  platforms: linux, macos, windows
  version: 3.0.0
---

# Kanban Profile Manager

## Overview

Manage the relationship between durable Kanban tasks and persistent Hermes profiles. Resolve a task to an existing role-based profile whenever possible; provision a new profile only from an approved template and only when policy allows it; validate the result before dispatch.

This skill manages **profile lifecycle and reconciliation**. It does not replace the Kanban orchestrator's responsibility for task decomposition, dependency graphs, or specialist routing, and it does not execute the business task itself.

## When to use

Use this skill when:

- A Kanban task needs an assignee selected from available Hermes profiles
- A requested specialist role may or may not already exist
- A task intake flow should reuse an existing profile idempotently
- A controlled workflow is allowed to create missing role profiles
- A profile's model, provider, skills, description, or tool access must be validated before dispatch
- A Kanban widget, API, webhook, or orchestrator needs a profile-resolution step

Do not use this skill to:

- Create a new profile for every task
- Invent arbitrary assignee names from task text
- Replace the Kanban dispatcher
- Decompose a complex task when the `kanban-orchestrator` skill should handle it
- Copy credentials or broad profile state without an explicit policy
- Delete profiles automatically as a cleanup reaction

## Core invariant: profiles are reusable roles

Create profiles by **stable role**, not by individual task.

```text
Many tasks ───────> one reusable role profile ───────> many worker processes
```

A profile is persistent configuration and identity: model/provider, skills, tools, description, memory/session scope, and other settings. The dispatcher may start multiple worker processes using one profile. Dynamic worker processes are not dynamic profile creation.

## Boundary with Kanban orchestration

The `kanban-orchestrator` skill owns:

- Understanding the user's goal
- Splitting work into lanes
- Choosing dependencies and parent links
- Routing lanes to known specialist profiles
- Creating and reporting the task graph

This skill owns:

- Discovering which profiles actually exist
- Mapping a requested role to an approved profile name
- Reusing an existing profile
- Provisioning a missing profile from a controlled template
- Validating the profile before assignment
- Returning an explicit `reused`, `created`, `blocked`, or `failed` result

If both skills are loaded, the orchestrator calls this lifecycle procedure before assigning a card. Do not let the manager silently invent a new task graph.

## Bootstrap requirement

A skill is not a background listener. A Kanban card entered in the desktop widget does not automatically execute this skill merely because the skill exists.

At least one existing bootstrap/orchestrator profile must receive the intake task and load this skill. The normal pattern is:

```text
Kanban widget/API
    -> existing orchestrator or intake profile
    -> this profile-resolution procedure
    -> existing or approved new specialist profile
    -> Kanban assignment
    -> dispatcher worker
```

Install this skill on the bootstrap/orchestrator profile, or explicitly force-load it for the intake task. A missing specialist profile cannot bootstrap its own creation.

## Profile-resolution procedure

> For a visual decision tree of this procedure, see `references/decision-flowchart.md`. For an automated implementation, see `scripts/profile_check.py`.

## Task-driven profile resolution (v2.1+)

When a user provides a **plain-language task description** (not a list of role names), use this procedure to infer which profiles are needed before running the resolution check.

### How it works

The agent IS the task analyzer. The script provides the role catalog (with capabilities); the agent reasons about which roles the task requires.

### Step 1: Show the role catalog with the task

```bash
python3 scripts/profile_check.py --registry <registry.yaml> --task "Build a monthly report from Xero data and analyze Amazon sales"
```

This prints the task description alongside every registered role's capabilities. The agent reads both and reasons about the match.

### Step 2: Infer the required roles

As the agent, analyze the task against the catalog. Ask:

- Which capabilities does this task need? (research, data analysis, spreadsheet work, review, etc.)
- Which registered roles provide those capabilities?
- Are there dependencies? (e.g., review always comes after the work it reviews)
- Is there a role the task needs that is NOT in the registry? If so, block and report it.

Output a comma-separated list of canonical role names.

### Step 3: Check and provision those roles

```bash
python3 scripts/profile_check.py --registry <registry.yaml> --roles "researcher,analyst,reviewer" --provision
```

This checks only the inferred roles against existing profiles and creates missing ones if policy allows.

### Step 4: Return the readiness handoff

Report which profiles are ready for Kanban dispatch. The workforce is prepared — the orchestrator or dispatcher can now assign tasks to these worker profiles.

### Example: full agent flow

```
User: "I need a financial report built from Xero data, with sales analysis
       across Amazon and TikTok, delivered as an Excel workbook, and reviewed."

Agent (loading kanban-profile-manager):
  1. Runs: --task "..." → sees role catalog with capabilities
  2. Reasons: "This needs data analysis (analyst), Excel work (excel-specialist),
              and quality review (reviewer). Xero data may need a xero-specialist
              if one exists in the registry."
  3. Runs: --roles "analyst,excel-specialist,reviewer" --provision
  4. Reports: "3 worker profiles ready for Kanban dispatch.
              Created: excel-specialist, reviewer. Reused: analyst."
```

The user never sees YAML, role names, or script paths. They describe the task; the agent handles the rest.

## Advanced profile configuration (v3.0+)

When provisioning a profile, the skill automatically applies role-specific
configuration to the new profile's `config.yaml`. This turns a bare profile
into a properly configured Kanban worker.

### How it works

1. The registry role includes a `config_overrides` block.
2. After `hermes profile create` runs, the checker reads the new profile's `config.yaml`.
3. The override values are deep-merged into the config (field-level, not section-level).
4. The profile is ready as a configured worker — not a bare shell.

### What is configurable

See `references/config-capability-reference.md` for the full table. Key areas:

| Area | Examples |
|---|---|
| Agent behavior | max_turns, tool_use_enforcement, verify_on_stop, reasoning_effort |
| Toolsets | enable/disable web, browser, delegation, cronjob, kanban |
| Terminal | backend, cwd, timeout |
| Memory | enabled/disabled, approval policy, char limits |
| Security | redact_secrets, approvals mode, blocklists |
| Delegation | max_concurrent_children, max_spawn_depth, orchestrator_enabled |
| Kanban | dispatch_in_gateway, failure_limit, auto_decompose |

### What is NOT configurable (explicitly excluded)

- **Model** — never touched. Set manually with `hermes -p <profile> model`.
- **Providers/API keys** — set via `.env` or `hermes config set`.
- **MCP servers** — configure separately.

### Skipping config application

To create profiles without applying overrides (bare creation):

```bash
python3 scripts/profile_check.py --registry my-roles.yaml --provision --no-config
```

### 1. Discover the live profile catalog

Before selecting an assignee, inspect the current installation rather than relying on memory or a hard-coded roster:

```bash
hermes profile list
```

Record the actual profile names for this resolution attempt. If the task requires a role that is not present, do not assign a guessed name: continue to the provisioning policy check or block for user choice.

Use profile descriptions where available. Descriptions should explain what the profile is good at and may be used by Kanban decomposition/routing.

### 2. Normalize the requested role

Convert the task's requested capability into an approved role key, such as:

```text
xero-specialist
excel-specialist
data-analyst
reviewer
```

Do not derive a shell command or arbitrary profile name directly from untrusted task text. Reject ambiguous roles or ask the orchestrator/user to choose.

### 3. Reuse before creating

If the approved role maps to an existing profile:

1. Use the exact existing profile name.
2. Inspect it if model, skills, or description requirements matter.
3. Do not create a duplicate profile.
4. Assign the Kanban card only after the profile meets the required contract.

Profile existence and profile readiness are different checks. An existing but misconfigured profile should be reported as `needs_update` or `blocked`, not silently duplicated.

### 4. Apply the missing-profile policy

Choose one explicit mode per deployment:

| Mode | Missing approved role |
|---|---|
| `reuse-only` | Block and request an existing profile or approval to create one |
| `provision-approved` | Create only when a registry template exists |
| `approval-required` | Prepare the proposed profile and wait for human approval |

Never provision a role merely because the task wording contains a new noun. The role must match an approved registry entry.

### 5. Provision from a controlled template

When provisioning is allowed:

1. Select an approved template and base profile.
2. Create the profile with a stable role name and description.
3. Apply only the declared model/provider, skills, toolsets, and workspace policy.
4. Avoid broad state cloning unless explicitly required.
5. Treat `.env`, OAuth state, tokens, and other credentials as sensitive; do not copy them by default.
6. Re-read the profile after creation and verify the contract.

Use the Hermes profile CLI rather than hand-editing `config.yaml`:

```bash
hermes profile create <role-name> --description "<role description>"
hermes profile describe <role-name>
hermes profile show <role-name>
```

If a clone operation is used, make the credential-copy decision explicit first. A clone option that copies configuration or `.env` is not a safe default for arbitrary role provisioning.

### 6. Verify before assignment

Verify at minimum:

- The exact profile name exists.
- The profile description matches the intended role.
- The configured model/provider is available under policy.
- Required skills are installed and discoverable.
- Required tools/toolsets are enabled.
- The profile can run in the selected workspace and tenant scope.
- The profile is not being created repeatedly by a retrying intake task.

Only then assign or create the task with that exact profile name.

### 7. Assign and hand off

Use the verified profile name for Kanban assignment. An unknown assignee is not automatically corrected by the dispatcher; depending on the failure path, the card can remain ready or eventually be blocked after spawn failures.

The manager should return a structured handoff, for example:

```json
{
  "requested_role": "excel-specialist",
  "profile": "excel-specialist",
  "action": "reused",
  "profile_created": false,
  "ready_for_dispatch": true,
  "reason": "Existing profile satisfies the role contract"
}
```

For a provisioned role, include the template and verification result. For a blocked role, include the missing capability, allowed alternatives, and the precise approval needed.

## Idempotency and concurrency

Profile provisioning must be safe when two intake attempts race:

- Normalize the role key before checking.
- Re-check existence immediately before creation.
- Use one canonical profile name per role.
- Treat an already-created profile as success, then validate it.
- Do not create suffixes such as `excel-specialist-2` unless the user explicitly requested a separate profile.
- Record the task/profile decision in a Kanban comment or structured handoff.
- Do not assign the card until the create-or-reuse result is verified.

If the CLI or an orchestration layer offers an atomic create operation, prefer it. Otherwise serialize provisioning per role in the manager's own coordination layer.

## Recommended role registry

Keep approved role templates separate from free-form task text. A registry entry should define:

- canonical role/profile name
- human-readable description
- base profile or safe creation method
- required skills
- allowed model/provider
- required toolsets
- whether automatic creation is allowed
- approval owner

See `references/profile-provisioning-registry.md` for a compact example and decision contract.

## Failure handling

Use explicit states:

- `reused`: existing profile found and verified
- `created`: missing profile provisioned and verified
- `needs_update`: profile exists but does not meet the contract
- `blocked`: no approved profile/template or approval is required
- `failed`: a concrete creation or verification operation failed

Do not conceal a profile mismatch by routing to a vaguely similar role. Ask the orchestrator/user to choose, or block the task with a useful reason.

## Common pitfalls

1. **Creating one profile per Kanban card.** Profiles are persistent roles; reuse them across tasks.
2. **Assuming a skill is a listener.** A `SKILL.md` changes an agent's procedure only when that agent loads it; connect widget intake through an existing orchestrator, hook, or backend.
3. **Assigning a guessed profile name.** Discover the live catalog and use exact names.
4. **Solving a missing profile by silently falling back.** Fallback can send financial or coding work to the wrong agent; require an approved fallback policy.
5. **Blindly cloning a profile.** Credential and state copying must be explicit and minimal.
6. **Letting retries create duplicates.** Re-check by canonical role name and verify idempotently.
7. **Mixing routing and execution.** The manager resolves and hands off; the assigned worker performs the business task.
8. **Assuming the Kanban widget invokes arbitrary skills.** The widget creates/updates board state; an agent or integration must process the intake.
9. **Editing `config.yaml` by hand.** Use Hermes profile/config commands and verify the live result.
10. **Exposing implementation details in user-facing prompts.** Sample prompts and usage examples should accept plain task descriptions ("build a monthly report from Xero data"), not internal references (file paths, YAML filenames, phase numbers, script flags). The user describes the work; the agent translates that into registry lookups and script invocations. See `references/task-driven-design-pattern.md` for the agent-as-analyzer architecture that enables this.
11. **Assuming `done` means durable output.** Worker workspaces are scratch and may be deleted at task completion. If the deliverable must survive, the task must name the final destination or include a copy/export step back to a persistent project path. See `references/persistent-workspace-delivery.md` for a concrete example.

## Verification checklist

- [ ] A bootstrap/orchestrator profile is identified.
- [ ] The live profile catalog was discovered.
- [ ] The requested role maps to an approved registry entry.
- [ ] Existing profile reuse was attempted before provisioning.
- [ ] Any provisioning used an approved template and explicit credential policy.
- [ ] The resulting profile was re-read and validated.
- [ ] The task uses the exact verified assignee name.
- [ ] Missing/ambiguous roles produce a clear blocked or approval-required result.
- [ ] No duplicate profile was created during retries.
- [ ] The manager returned a structured handoff suitable for Kanban comments/events.

## Related skills

- `kanban-orchestrator` — task decomposition and assignment graph; user-owned/protected in some installations, so do not patch it automatically.
- `kanban-worker` — execution lifecycle for the assigned worker.

For a reusable registry and structured decision examples, see `references/profile-provisioning-registry.md`.
For durable artifact persistence guidance, see `references/persistent-workspace-delivery.md`.

## Interaction style for sample prompts

When providing sample prompts to test this skill, always use **plain-language task descriptions** — never leak YAML paths, script names, role identifiers, or "Phase N" terminology into user-facing text. The skill is designed so the user describes *what work they need done* and the agent infers everything else. A prompt like "Run profile_check.py with --task flag against sample-registry.yaml" is wrong; "Build a monthly report from Xero data and have it reviewed" is right.

## Bundled artifacts

This skill ships with executable and reference artifacts that automate the
procedures described above. Load them when you need to run Phase 1 checks
rather than following the prose manually.

### Scripts

- **`scripts/profile_check.py`** — Phase 1 readiness checker. Reads a role
  registry YAML, reconciles against `hermes profile list`, optionally
  provisions missing profiles (with `--provision`), and returns a structured
  readiness report. Supports `--json` for machine-readable output.

  ```bash
  # Check only — no mutations
  python3 scripts/profile_check.py --registry my-roles.yaml

  # Check + provision missing approved roles
  python3 scripts/profile_check.py --registry my-roles.yaml --provision

  # Machine-readable output for CI or orchestrator consumption
  python3 scripts/profile_check.py --registry my-roles.yaml --provision --json
  ```

- **`scripts/requirements.txt`** — Python dependencies (`pyyaml`).
- **`scripts/config_merger.py`** — Standalone deep-merge utility for applying
  config overrides to profile `config.yaml` files. Importable and testable
  independently of the main checker. Protects `model`, `providers`,
  `mcp_servers`, and `platform_toolsets` from being modified.

### References

- **`references/decision-flowchart.md`** — ASCII decision-tree visualizing the
  full 7-step profile-resolution procedure. Use as a quick-reference when
  deciding reuse vs provision vs block.

- **`references/readiness-report-contract.md`** — Machine-readable JSON output
  contract. Defines every field the script produces. Downstream consumers
  (orchestrators, dashboards, CI pipelines) should treat this as the stable
  API.

- **`references/profile-provisioning-registry.md`** — Starter registry YAML
  and decision-contract examples (existing, updated for v2.0.0).
- **`references/config-capability-reference.md`** — Full reference for every
  configurable area with example values for worker vs orchestrator profiles.

- **`references/task-driven-design-pattern.md`** — How the agent-as-analyzer
  pattern works: the user describes a task in plain language, the agent
  reasons against the role catalog's `capabilities` fields, then calls the
  script with `--roles`. Includes why keyword matching was rejected.

### Tests

- **`tests/test_profile_check.py`** — pytest suite covering registry loading,
  reuse-only mode, provision-approved mode, unknown-role blocking,
  idempotency, and Phase 1 boundary enforcement. All tests use mocked
  subprocess calls — no live Hermes installation needed.

  ```bash
  cd ~/.hermes/skills/devops/kanban-profile-manager
  pip install pyyaml pytest
  python3 -m pytest tests/ -v
  ```

- **`tests/fixtures/`** — Minimal domain-agnostic registry YAML files for
  testing. See `tests/README.md` for the article test-case mapping.

### Running bundled scripts and tests (macOS / Python 3.9+)

Two environment pitfalls recur when running `scripts/profile_check.py` or
the pytest suite outside the Hermes venv:

1. **PYTHONPATH leakage.** The Hermes terminal inherits a `PYTHONPATH` that
   points at the Hermes-managed Python 3.11 venv. Running `/usr/bin/python3`
   (system Python 3.9) with that `PYTHONPATH` causes `pip` to crash with
   `TypeError: dataclass() got an unexpected keyword argument 'slots'` and
   other version-mismatch errors. **Fix:** prefix every system-Python
   invocation with `env -u PYTHONPATH`:
   ```bash
   env -u PYTHONPATH /usr/bin/python3 -m pytest tests/ -v
   env -u PYTHONPATH /usr/bin/python3 scripts/profile_check.py --registry ...
   ```
   Alternatively, use the Hermes venv Python directly
   (`~/.hermes/hermes-agent/venv/bin/python`) without clearing `PYTHONPATH`.

2. **Python 3.9 f-string backslash limitation.** System Python on this
   machine is 3.9, which does not allow backslashes inside f-string
   expressions (e.g. `f"{'\u2500'*60}"` raises `SyntaxError`). The script
   avoids this by assigning the separator to a variable first:
   `sep = "\u2500" * 60; print(sep)`. If you extend the script, keep this
   pattern — never embed escape sequences inside `{...}` in f-strings when
   targeting Python 3.9.
