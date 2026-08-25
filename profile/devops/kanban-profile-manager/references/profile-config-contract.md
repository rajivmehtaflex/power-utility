# Hermes Profile Configuration Contract for Kanban and Bot Mode

Use this reference when a reusable Hermes profile will serve as a Kanban worker, Kanban orchestrator, or Bot Mode agent. It is a **configuration contract**, not a requirement to materialize every Hermes default in `config.yaml`.

## Source and versioning

Hermes configuration evolves. Before applying a contract, inspect the live installation:

```bash
hermes --version
hermes profile list
hermes profile show <name>
hermes -p <name> config check
hermes -p <name> tools list
```

Use `hermes config set` / `hermes profile` commands for changes. Keep secrets in the target profile's `.env` or OAuth store; do not copy credentials without an explicit policy.

## Profile layers

A profile is the reusable role boundary. The durable surface includes:

- `config.yaml` — non-secret runtime settings
- `.env` / `auth.json` — API keys, bot tokens, OAuth pools
- `SOUL.md` — persona and standing instructions
- `profile.yaml` — role metadata (`description`, `description_auto`) and optional UI metadata
- `skills/` — installed role capabilities
- `memories/`, `sessions/`, `cron/`, `logs/` — state and operations

A Bot is a profile. Kanban workers and Bot Mode share the same profile configuration.

## Identity contract

Every reusable role should define:

- canonical profile name: lowercase, stable, and not task-specific
- human-readable `description`: concrete capabilities for Kanban routing
- `SOUL.md`: role, boundaries, output/handoff style
- required installed skills
- credential policy: shared OAuth/token pool or isolated credentials
- workspace policy: explicit `terminal.cwd` or task workspace contract

`description_auto` records whether the profile description was generated. A missing description is allowed by the runtime but weakens Kanban decomposition and routing.

Bot Mode may additionally persist `profile.yaml.ui_meta.hermes-bots` metadata such as:

- `title`
- `shape`
- `color`
- `imageKind`
- `hidden`
- `created`

Uploaded/generated avatar data is stored as a profile asset rather than as a large inline metadata blob. Bot appearance is UI metadata, not a replacement for `SOUL.md` or the Kanban role description.

## Main model/provider contract

A runnable profile needs an available model route:

```yaml
model:
  provider: custom
  default: <model-id>
  base_url: <openai-compatible-url>
  api_mode: chat_completions
```

The main model surface can include `provider`, `default`/`model`, `base_url`, `api_key` (prefer `.env`), `api_mode`, `context_length`, `max_tokens`, `default_headers`/`extra_headers`, `auth_mode`, `entra.scope`, and `aliases`.

Named `providers.<id>` entries may define `api`/`base_url`, `api_key`, `key_env`, `key_cmd`, `api_mode`/`transport`, `model`/`models`, `context_length`, `extra_headers`, `discover_models`, `request_timeout_seconds`, `stale_timeout_seconds`, `rate_limit_delay`, `extra_body`, SSL settings, and per-model timeout/context/prompt-caching overrides.

Related routing keys include `fallback_providers`, `fallback_model`, `credential_pool_strategies`, `model_aliases`, `model.aliases`, `model_overrides`, and provider-specific routing policy.

The Kanban profile manager's `config_overrides` intentionally does not own model/provider credentials. Validate those separately before dispatch.

## Behavior contract

For a focused worker, inspect or override:

- `agent.max_turns`
- `agent.tool_use_enforcement`
- `agent.verify_on_stop`
- `agent.reasoning_effort` / `agent.reasoning_overrides`
- `agent.task_completion_guidance`
- `agent.parallel_tool_call_guidance`
- `agent.gateway_timeout` and relevant retry/build timeouts
- `agent.bot_mode_protocol` for Bot Mode
- `agent.disabled_toolsets`

For an orchestrator, also validate delegation and Kanban decomposition settings. Do not assume a skill is a listener: Bot/Kanban intake still needs a running gateway, orchestrator, webhook, or other bootstrap path.

## Capability contract

Validate three distinct surfaces:

1. `toolsets` — global/default capability bundle
2. `platform_toolsets.<platform>` — gateway-specific capability bundles
3. `agent.disabled_toolsets` — explicit restrictions

Also validate:

- installed/enabled skills and any task-pinned skills
- `mcp_servers` and the selected MCP tools
- enabled plugins and plugin-provided toolsets
- optional `image_gen`, `video_gen`, `x_search`, and service integrations

MCP server entries use either stdio (`command`, `args`, `env`, `timeout`, `connect_timeout`) or HTTP (`url`, `headers`, `timeout`, `connect_timeout`). Optional sampling settings include `enabled`, `model`, `max_tokens_cap`, `timeout`, `max_rpm`, `allowed_models`, `max_tool_rounds`, and `log_level`.

## Workspace and execution contract

Validate:

- `terminal.backend`
- `terminal.cwd`
- `terminal.timeout`
- `terminal.home_mode`
- `terminal.env_passthrough`
- `terminal.persistent_shell`
- backend-specific image/resource/mount/network settings

A profile is not a sandbox. Use Docker/SSH/Modal/etc. when isolation is required. For Kanban, distinguish profile `terminal.cwd` from the task's `scratch`, `worktree`, or `dir:<absolute-path>` workspace.

## Memory and context contract

Choose the intended state policy explicitly:

- `memory.memory_enabled`
- `memory.user_profile_enabled`
- `memory.write_approval`
- `memory.memory_char_limit`
- `memory.user_char_limit`
- `memory.provider`
- `context.engine`
- `context.memory_trim.*`
- `compression.*`
- `prompt_caching.cache_ttl`
- `checkpoints.*`

Stateless reviewers usually disable agent/user memory. Persistent Bots and analyst roles usually enable agent memory, but should not inherit personal user-profile memory accidentally.

## Security and unattended execution contract

Validate:

- `approvals.mode`, `approvals.timeout`, `approvals.cron_mode`, `approvals.single_query_mode`
- `security.redact_secrets`
- `security.allow_private_urls`
- `security.allow_lazy_installs`
- `security.allow_data_training_tiers_noninteractive`
- `security.tirith_*`
- `security.website_blocklist.*`
- `security.protected_instruction_files`
- command allowlist and MCP reload/destructive-action confirmations

Keep secret redaction enabled. Headless Kanban workers cannot answer interactive prompts, so their approval/cron policy must be deliberate rather than copied from an interactive desktop profile.

## Delegation contract

Leaf workers should normally use:

```yaml
delegation:
  max_concurrent_children: 0
  max_spawn_depth: 0
  orchestrator_enabled: false
```

Orchestrators need an explicit positive budget for `max_concurrent_children`, `max_spawn_depth`, and `orchestrator_enabled`. Other delegation fields include `model`, `provider`, `base_url`, `api_key`, `api_mode`, `inherit_mcp_toolsets`, `max_iterations`, `max_summary_chars`, `child_timeout_seconds`, `reasoning_effort`, and `subagent_auto_approve`.

## Kanban contract

Dispatcher/gateway settings include:

- `kanban.dispatch_in_gateway`
- `kanban.dispatch_interval_seconds`
- `kanban.failure_limit`
- `kanban.review_dispatch`
- `kanban.auto_subscribe_on_create`
- `kanban.worker_log_rotate_bytes`
- `kanban.worker_log_backup_count`
- `kanban.orchestrator_profile`
- `kanban.default_assignee`
- `kanban.max_in_progress`
- `kanban.max_in_progress_per_profile`
- `kanban.auto_decompose`
- `kanban.auto_decompose_per_tick`
- `kanban.dispatch_stale_timeout_seconds`
- `kanban.reconcile_orphans`
- `kanban.done_sub_retention_days`

`dispatch_in_gateway` is primarily a gateway/dispatcher concern, not a signal that an individual worker can autonomously pick up arbitrary cards. Workers receive task-scoped `HERMES_KANBAN_*` environment values and dedicated Kanban tools when dispatched.

## Bot Mode and gateway contract

For a Bot profile, validate:

- `agent.bot_mode_protocol`
- Bot `profile.yaml` metadata and optional avatar asset
- canonical `Bot Chat` session behavior
- gateway platform enablement and per-platform toolsets
- allowed users/channels/rooms and mention/thread policy
- per-platform credentials in `.env`
- profile-scoped cron routines

Cross-machine Bot messaging additionally requires:

- peer definitions under `bot_peers`
- peer API-server URL
- peer API-server credential in the local secret store
- API server enabled on the remote gateway
- optional `gateway.multiplex_profiles`, `gateway.multiplex_profile_allowlist`, and `profile_routes`

## Role-registry contract

Keep role templates separate from free-form task text. A role entry should define:

- canonical role/profile name
- description and capabilities
- approved base/creation method
- required skills
- required toolsets
- allowed model/provider policy
- workspace and tenant policy
- whether auto-provisioning is allowed
- approval owner
- `config_overrides`

`config_overrides` can cover agent behavior, tool restrictions, terminal, memory, approvals/security, delegation, Kanban, checkpoints, and selected display fields. Treat model/provider credentials, MCP server connections, and platform-specific tool mappings as separate validated inputs.

## Verification contract

Do not treat profile existence as readiness. Before assignment, verify:

```bash
hermes profile list
hermes profile show <profile>
hermes -p <profile> config check
hermes -p <profile> tools list
hermes -p <profile> skills list
hermes -p <profile> doctor
hermes kanban assignees
```

A successful handoff should report the exact profile, whether it was reused or created, the model/provider readiness result, required skills/tools, workspace policy, and any blocked credential or approval decision.

## Upgrade-safety rule

Do not copy the entire generated `DEFAULT_CONFIG` into every profile. Set only role-specific overrides and re-check the live schema after Hermes upgrades. Hermes supplies defaults at load time, and materializing every default makes future migrations harder to reason about.
