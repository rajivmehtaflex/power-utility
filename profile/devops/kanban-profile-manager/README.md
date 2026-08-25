# Kanban Profile Manager (`kanban-profile-manager`)

> Managed lifecycle and profile reconciliation skill for the **Hermes Agentic Harness**.

---

## Overview

The `kanban-profile-manager` skill manages the relationship between durable Kanban tasks and persistent Hermes profiles. It resolves task requirements to existing role-based profiles whenever possible, provisions new profiles only from approved templates when policy permits, and validates profile configuration before dispatch.

### Key Capabilities & Invariants

- **Role Reusability**: Profiles are created by stable, reusable role (e.g., `analyst`, `reviewer`, `researcher`), not per task.
- **Idempotent Resolution**: Reuses existing role profiles when available, avoiding profile proliferation.
- **v3.0 Config Overrides**: Automatically applies role-specific configuration overrides (e.g., `max_turns`, `reasoning_effort`, `memory_enabled`, `terminal.cwd`, `terminal.timeout`, `tool_use_enforcement`) while leaving models, credentials, and MCP server settings untouched.
- **Task-Driven Role Inference**: Analyzes plain-language task descriptions against the role catalog to infer needed specialist profiles automatically.
- **Orchestration Boundary**: Works alongside `kanban-orchestrator`—the orchestrator owns task graph decomposition and routing, while this skill owns profile discovery, provisioning, and handoff verification.

---

## Sample Prompts

Use these prompts to test the **v3.0 config-override feature live**. None of them mention config files, scripts, or model settings—they are pure task descriptions, and the skill applies role-specific configurations automatically.

---

### Prompt 1: Strict Reviewer Role

> **"I need a reviewer profile that checks work against acceptance criteria. Create it if it doesn't exist."**

**What happens:**
1. Agent infers role: `reviewer`
2. Runs `profile_check.py --provision` with the reviewer role
3. Profile is created **AND configured automatically** with:
   - `max_turns: 20` (strict turn limit)
   - `tool_use_enforcement: strict`
   - `memory_enabled: false` (stateless)
   - `max_spawn_depth: 0` (cannot delegate)

Verification:
```bash
hermes -p reviewer config get agent.max_turns        # → 20
hermes -p reviewer config get memory.memory_enabled  # → false
hermes -p reviewer config get delegation.max_spawn_depth  # → 0
```

---

### Prompt 2: Autonomous Data Analyst

> **"I need an analyst profile that can handle long-running data work with deep reasoning. Set it up."**

**What happens:**
1. Agent infers role: `analyst`
2. Profile is created with:
   - `max_turns: 60` (higher turn limit)
   - `reasoning_effort: high`
   - `memory_enabled: true` (accumulates expertise)
   - `terminal.cwd: ~/Documents/Dev`
   - `terminal.timeout: 600` (10-minute shell timeout)

---

### Prompt 3: Multi-Role Workforce Setup

> **"Set up my Kanban workforce for recurring financial reporting. I need a data analyst, an Excel specialist, and a reviewer — all configured and ready for dispatch."**

**What happens:**
1. Agent infers 3 roles from the task
2. Profiles are created **with distinct configurations**:
   - `analyst` — high turn limit, memory enabled, Dev workspace
   - `excel-specialist` — moderate turn limit, memory enabled, optimized for workbook work
   - `reviewer` — low turn limit, memory disabled, strict tool enforcement
3. Returns readiness report with config-override confirmation

---

### Prompt 4: Bare Profile Creation (Skip Overrides)

> **"Create a bare researcher profile with default configuration — I'll configure it myself manually."**

**What happens:**
1. Agent infers role: `researcher`
2. Runs with `--no-config` flag (bare creation mode)
3. Profile is created but **NO config overrides are applied**
4. You can then manually configure via `hermes -p researcher config set ...`

---

### Prompt 5: Verify Model Was NOT Touched

> **"Create a reviewer profile, then show me that its model setting is still at the default (your call). The skill should not touch the model."**

**What happens:**
1. Profile created with overrides applied
2. You verify model is untouched:
   ```bash
   hermes -p reviewer config get model.default  # Shows default configured model
   ```
3. The skill never modifies `model.default`, `providers`, `mcp_servers`, or `platform_toolsets`.

---

### Quick Reference

| # | Prompt | Config Areas Demonstrated |
|---|---|---|
| 1 | Strict reviewer | Agent behavior, memory disabled, delegation blocked |
| 2 | Autonomous analyst | High turn limit, high reasoning, workspace, timeout |
| 3 | Multi-role workforce | Different configs per role in one request |
| 4 | Bare profile | `--no-config` flag skips all overrides |
| 5 | Model protection | Proves model configuration is never touched |

---

## Installation in Hermes Agentic Harness

All skills in the Hermes ecosystem reside inside `~/.hermes/skills/`.

### Method 1: Git Clone (Recommended for complete skill repos)

Clone this repository directly into your Hermes skills directory:

```bash
cd ~/.hermes/skills/devops
git clone https://github.com/rajivmehtaflex/kanban-profile-manager.git
```

Or clone to a standalone directory under skills:

```bash
git clone https://github.com/rajivmehtaflex/kanban-profile-manager.git ~/.hermes/skills/kanban-profile-manager
```

### Method 2: Configure External Skills Directory

If you store skills in an external path, update `~/.hermes/config.yaml`:

```yaml
skills:
  external_dirs:
    - /path/to/custom/skills
    - ~/.hermes/skills/devops/kanban-profile-manager
```

### Method 3: Hermes CLI Install

If registered in a skill tap/registry:

```bash
hermes skills install devops/kanban-profile-manager
```

---

## Verification

Confirm Hermes detects the skill by running:

```bash
hermes skills list
```

or asking Hermes in chat:

> *"Show available skills"* or *"Check if kanban-profile-manager skill is loaded"*

---

## Repository & License

- **GitHub Repository**: [https://github.com/rajivmehtaflex/kanban-profile-manager](https://github.com/rajivmehtaflex/kanban-profile-manager)
- **License**: MIT
