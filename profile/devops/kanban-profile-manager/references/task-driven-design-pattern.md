# Task-Driven Design Pattern: Agent-as-Analyzer

How to let users describe a task in plain language while the skill handles
registry lookups, role inference, and profile provisioning internally.

## The problem

A skill that requires users to know internal file paths, role names, YAML
registries, or phase numbers is leaking implementation details. Users should
describe *what work they need done*, not *which infrastructure to invoke*.

## The solution: agent IS the analyzer

The LLM agent is the task-analysis layer. A deterministic script cannot
reason about natural language, but the agent can. The pattern:

```
User says:  "Build a monthly report from Xero data with Amazon sales analysis"

Agent (loads skill):
  1. Calls script with --task flag → gets structured role catalog
     (role names, descriptions, capabilities, skills)
  2. Reasons: "This task needs data analysis + Excel work + review"
  3. Maps to roles: analyst, excel-specialist, reviewer
  4. Calls script with --roles "analyst,excel-specialist,reviewer" --provision
  5. Reports to user: "3 worker profiles ready for Kanban dispatch"
```

The user never sees YAML, role names, or script paths.

## Why not keyword matching?

A keyword-matching approach (scan task text for trigger words) was considered
and rejected in favor of agent-driven inference because:

- **Agent reasoning handles synonyms and complex phrasing** that keywords miss.
- **No keyword maintenance** — the registry's `capabilities` field is descriptive, not a keyword list.
- **Handles multi-role inference** naturally (one task often needs 3-5 roles).
- **Already available** — the agent IS an LLM; no extra infrastructure needed.

## Why not pure agent reasoning (no script at all)?

The script is still needed because:

- **Profile discovery is deterministic** — `hermes profile list` is a CLI call, not reasoning.
- **Idempotency needs enforcement** — re-checking existence before creation must be coded, not hoped for.
- **Structured output** — downstream consumers (orchestrators, CI) need a stable JSON contract.
- **Testability** — mocked subprocess calls let you unit-test the resolution logic.

## The registry's `capabilities` field

Each role in the registry YAML should include a `capabilities` field — a
plain-language description of what the role can do. This is what the agent
reads when matching a task description to roles.

```yaml
roles:
  excel-specialist:
    description: "Creates and validates Excel workbooks"
    capabilities: "Excel workbook creation, formula validation, multi-sheet
      reporting, formatting, chart generation, CSV import/export."
    skills: [xlsx, document-generation]
    auto_create: true
```

The `capabilities` text should be:
- Specific enough to distinguish roles (analyst vs researcher)
- Broad enough to cover variations ("build a report" vs "create a spreadsheet")
- Free of internal jargon (no skill names, no tool names)

## Three CLI modes of profile_check.py

| Mode | Flag | Purpose |
|---|---|---|
| Task analysis | `--task "<text>"` | Print role catalog for agent reasoning (no mutations) |
| Explicit check | `--roles "role1,role2"` | Check specific roles only (after agent inference) |
| Full check | (no --task, no --roles) | Check all roles in the registry |

All three can be combined with `--provision` (create missing) and `--json` (machine-readable output).
