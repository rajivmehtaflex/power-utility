# Profile Configuration Capability Reference

This reference maps each Hermes `config.yaml` section to the profile
capabilities that the kanban-profile-manager can configure via
`config_overrides` in the role registry.

**Model is excluded.** The `model` section is never touched by the
profile manager. Set it manually after profile creation via
`hermes -p <profile> model <model_id>` or by editing the profile's
`config.yaml`.

## How to use this reference

Add a `config_overrides` block to any role in your registry YAML:

```yaml
roles:
  reviewer:
    description: "Reviews outputs against acceptance criteria."
    config_overrides:
      agent:
        max_turns: 20
      memory:
        memory_enabled: false
```

Only the fields you list are overridden. Everything else inherits
from the profile's base config (default or cloned source).

## Configurable areas

### Agent behavior

Controls how the agent reasons, acts, and verifies.

```yaml
config_overrides:
  agent:
    max_turns: 30              # max reasoning turns per task
    tool_use_enforcement: strict  # auto | strict | off
    verify_on_stop: always     # auto | always | never
    reasoning_effort: high     # low | medium | high
    task_completion_guidance: true
    parallel_tool_call_guidance: true
```

| Field | Type | Typical values for workers |
|---|---|---|
| `max_turns` | int | 20-30 for focused workers, 60+ for autonomous |
| `tool_use_enforcement` | str | `strict` for constrained roles, `auto` for general |
| `verify_on_stop` | str | `always` for quality-critical, `auto` for general |
| `reasoning_effort` | str | `high` for analysts, `medium` for simple workers |

### Toolsets

Controls which tool categories are available to the profile.

```yaml
config_overrides:
  toolsets:
    - hermes-cli    # core tools (file, terminal, web search, etc.)
```

For a restricted worker:

```yaml
config_overrides:
  toolsets:
    - hermes-cli
  agent:
    disabled_toolsets:
      - browser
      - delegation
      - cronjob
```

### Terminal

Controls where shell commands run.

```yaml
config_overrides:
  terminal:
    backend: local        # local | docker | modal | ssh | daytona
    cwd: ~/Documents/Dev  # working directory
    timeout: 300          # max seconds per command
```

### Memory

Controls persistent and user-profile memory.

```yaml
config_overrides:
  memory:
    memory_enabled: false       # stateless worker — fresh each run
    user_profile_enabled: false
    write_approval: true        # require approval before writing memory
    memory_char_limit: 1000
```

| Use case | `memory_enabled` | `user_profile_enabled` |
|---|---|---|
| Stateless worker (reviewer, QA) | `false` | `false` |
| Role with accumulating expertise (analyst) | `true` | `false` |
| Full personal assistant | `true` | `true` |

### Approvals / security

Controls approval prompts, secret redaction, and safety guards.

```yaml
config_overrides:
  approvals:
    mode: 'off'            # off | always | on-failure — workers run headless
    cron_mode: deny        # deny | allow — workers can't create cron jobs
  security:
    redact_secrets: true
    allow_lazy_installs: false
    website_blocklist:
      enabled: true
      domains: []
```

### Delegation

Controls whether the profile can spawn subagents.

```yaml
config_overrides:
  delegation:
    max_concurrent_children: 0   # 0 = cannot delegate at all
    max_spawn_depth: 0           # 0 = leaf-only, no nesting
    orchestrator_enabled: false  # cannot act as orchestrator
```

For a profile that CAN fan out work:

```yaml
config_overrides:
  delegation:
    max_concurrent_children: 4
    max_spawn_depth: 1
    orchestrator_enabled: true
```

### Kanban

Controls board-driven work queue behavior.

```yaml
config_overrides:
  kanban:
    dispatch_in_gateway: true      # worker picks up tasks automatically
    failure_limit: 3              # max consecutive failures before blocking
    auto_decompose: false          # workers don't decompose; orchestrators do
```

For an orchestrator profile:

```yaml
config_overrides:
  kanban:
    auto_decompose: true
    auto_decompose_per_tick: 5
```

### Checkpoints / curator

Controls snapshots and skill lifecycle cleanup.

```yaml
config_overrides:
  checkpoints:
    enabled: true
    max_snapshots: 10
    retention_days: 14
```

### Display / voice

Controls interface, skin, language, TTS/STT.

```yaml
config_overrides:
  display:
    personality: technical
    language: en
    show_reasoning: true
```

## What is NOT configurable via overrides

- **`model`** — never touched. Set manually with `hermes -p <profile> model`.
- **`providers`** — API keys/credentials. Set manually or via `.env`.
- **`mcp_servers`** — MCP server connections. Configure separately.
- **`platform_toolsets`** — platform-specific tool mappings. Configure separately.

## Example: full worker role with overrides

```yaml
roles:
  excel-specialist:
    description: "Creates, edits, validates, and exports Excel workbooks."
    capabilities: "Excel workbook creation, formula validation, charts, CSV import/export."
    skills: [xlsx, document-generation]
    auto_create: true
    config_overrides:
      agent:
        max_turns: 40
        tool_use_enforcement: auto
        verify_on_stop: always
      toolsets:
        - hermes-cli
      terminal:
        cwd: ~/Desktop/FC-Plus
        timeout: 600
      memory:
        memory_enabled: true
        user_profile_enabled: false
      security:
        redact_secrets: true
      delegation:
        max_spawn_depth: 0
      kanban:
        dispatch_in_gateway: true
        failure_limit: 2
```
