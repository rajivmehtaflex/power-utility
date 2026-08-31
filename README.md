# Skill Collections — Cross-Agent Mono-Repo

Spec: https://agentskills.io/specification.md · 71 skills · synced 2026-08-31

[![skills.sh](https://skills.sh/b/rajivmehtaflex/power-utility)](https://skills.sh/rajivmehtaflex/power-utility)

Normalized copies of every user-added skill. Live sources
(~/.hermes/skills, ~/.agents/skills, ~/Documents/Dev/Skills) are never modified;
re-sync with `uv run python -m src.skill_collections.sync`.

## Install with `npx skills` (all agents)

The [skills CLI](https://github.com/vercel-labs/skills) auto-detects installed
agents (Claude Code, Codex, Cursor, Copilot, OpenCode, …) or takes `--agent`:

```bash
# Install ALL 71 skills (auto-detect agents, interactive pick)
npx skills add rajivmehtaflex/power-utility

# List available skills without installing
npx skills add rajivmehtaflex/power-utility --list

# Install ONE specific skill
npx skills add rajivmehtaflex/power-utility --skill get-info

# Install the 1-minute video generation skill
npx skills add rajivmehtaflex/power-utility --skill 1-minute-video-gen

# Install SEVERAL skills
npx skills add rajivmehtaflex/power-utility --skill modal-deploy --skill gh-cli-ops

# Install ALL skills to a specific agent
npx skills add rajivmehtaflex/power-utility --all --agent claude-code

# Install globally (user-level) instead of project-level
npx skills add rajivmehtaflex/power-utility --skill get-info --global

# Non-interactive (CI-friendly): auto-confirm
npx skills add rajivmehtaflex/power-utility --skill get-info -y

# Install from a direct skill path in the repo
npx skills add https://github.com/rajivmehtaflex/power-utility/tree/main/profile/research/get-info

# Try a skill ONCE without installing (prints the prompt)
npx skills use rajivmehtaflex/power-utility --skill get-info

# Update installed skills to latest
npx skills update rajivmehtaflex/power-utility

# Remove an installed skill
npx skills remove get-info
```

### Variant parameters at a glance

| Variant | Flag(s) | Example |
|---|---|---|
| Install everything | `--all` | `npx skills add rajivmehtaflex/power-utility --all` |
| Pick one skill | `--skill <name>` | `npx skills add rajivmehtaflex/power-utility --skill modal-deploy` |
| Pick many skills | repeat `--skill` | `--skill get-info --skill gh-cli-ops --skill xurl` |
| Wildcard all skills | `--skill '*'` | `npx skills add rajivmehtaflex/power-utility --skill '*'` |
| Target one agent | `-a/--agent <name>` | `--agent codex` (claude-code, cursor, copilot, opencode, …) |
| Target several agents | repeat `-a` | `-a claude-code -a codex` |
| All agents | `--agent '*'` | `npx skills add rajivmehtaflex/power-utility --agent '*' --skill get-info` |
| User-global install | `-g/--global` | installs to user skill dir, not the project |
| Copy instead of symlink | `--copy` | durable files for CI/containers |
| Yes to all prompts | `-y` | non-interactive installs |
| List only | `--list` | see the catalog before choosing |
| Use without install | `npx skills use <src>` | one-shot prompt to stdout |

### Other install paths

- **GitHub CLI** (v2.90+): `gh skill install rajivmehtaflex/power-utility get-info`
- **Manual**: copy a skill dir into your agent's skills folder (e.g. `~/.claude/skills/`, `~/.agents/skills/`, `~/.hermes/skills/<category>/`)
- **Any agentskills.io-compatible client** — spec: https://agentskills.io/specification.md

### Verify a skill (agentskills.io spec)

```bash
npx skills-ref validate <skill-dir>
```

### Re-sync from live sources (maintainer)


```bash
cd ~/Documents/Dev/pi-local-dev-exp-v1
uv run python -m src.skill_collections.sync            # full rebuild
uv run python -m src.skill_collections.sync --dry-run  # plan only
```

Live sources (~/.hermes/skills, ~/.agents/skills, ~/Documents/Dev/Skills)
are never modified — only these copies are normalized.

## Index

| Name | Group | Category | Spec-compliant | Description |
|---|---|---|---|---|
| `data-to-okf` | agents-shared | — | yes | Converts any local folder of mixed documents (docx, pdf, xlsx, duckdb, csv, imag |
| `release-notes` | agents-shared | — | yes | >- |
| `graph-flow` | dev-workspace | — | yes | Use when coordinating a repository implementation from a goal through approved,  |
| `intent-first-action-boundaries` | profile | assistant-behavior | yes | Use for question-vs-action intent routing. |
| `hermes-agent-api-bridge` | profile | autonomous-ai-agents | yes | Bridge Hermes Agent to external apps via subprocess or HTTP. |
| `pi-operator` | profile | autonomous-ai-agents | yes | Operate and verify the Pi coding-agent CLI safely. |
| `subagent-orchestration` | profile | autonomous-ai-agents | yes | Decompose implementation plans into parallel-safe task waves and dispatch them v |
| `html-artifact` | profile | creative | yes | Build self-contained HTML files to explain, plan, or review. |
| `interactive-3d-web` | profile | creative | yes | Build self-contained interactive 3D scenes with Three.js: orbit controls, transl |
| `procedural-3d-composite-scenes` | profile | creative | yes | Design, debug, verify, and parallelize Three.js scenes that combine organic char |
| `jupyter-live-kernel` | profile | data-science | yes | Iterative Python via live Jupyter kernel (hamelnb). |
| `knowledge-bundle` | profile | data-science | yes | Research knowledge bundles and query database schemas. |
| `cli-tool-installation` | profile | devops | yes | Install, verify, and expose command-line tools on the user's machine, including  |
| `colab-cli-authentication` | profile | devops | yes | Use for Colab CLI OAuth2/ADC authentication lifecycle. |
| `colab-operator` | profile | devops | yes | Operate Google Colab sessions via the `colab` CLI. |
| `colab-ssh-setup` | profile | devops | yes | \"Use when setting up Colab SSH for VSCode via colab CLI.\" |
| `hermes-home-maintenance` | profile | devops | yes | Audit and clean ~/.hermes safely by separating core state from caches, logs, and |
| `hermes-worker-provisioning` | profile | devops | yes | Use when provisioning Hermes worker profiles. |
| `hermes-workspace-management` | profile | devops | yes | Manage and clean up Hermes Desktop Project workspaces. |
| `kanban-orchestrator` | profile | devops | yes | Decomposition playbook + anti-temptation rules for an orchestrator profile routi |
| `kanban-profile-manager` | profile | devops | yes | Use when managing Kanban profile reuse or provisioning. |
| `kanban-worker` | profile | devops | yes | Pitfalls, examples, and edge cases for Hermes Kanban workers. The lifecycle itse |
| `modal-deploy` | profile | devops | yes | Deploy GPU-enabled applications to Modal with pre-check workflow, optimization p |
| `python-version-management` | profile | devops | yes | Force Python versions via uv for cloud compatibility. |
| `system-update` | profile | devops | yes | Use when the user asks to update/upgrade system packages and CLI tools — Homebre |
| `web-service-launch` | profile | devops | yes | Launch a web service (e.g., Chainlit, FastAPI) on a specific port, handling port |
| `gh-cli-ops` | profile | github | yes | Use for any gh CLI or GitHub-via-terminal task; routes refs. |
| `github-codespace-ssh` | profile | github | yes | Manage and SSH into GitHub Codespaces via gh CLI. |
| `hermes-model-management` | profile | hermes | yes | Add, find, and use models in Hermes that are NOT in the interactive provider pic |
| `hermes-token-usage` | profile | hermes | yes | Query Hermes's token, cost, and model-usage telemetry. Two paths: SQLite state.d |
| `local-model-endpoints` | profile | hermes | yes | Hermes picker omits local Ollama models `ollama ls` shows. |
| `okf-visualization` | profile | knowledge-management | yes | Visualize an OKF knowledge bundle; use npx okapi-okf first. |
| `heartmula` | profile | media | yes | HeartMuLa: Suno-like song generation from lyrics + tags. |
| `1-minute-video-gen` | profile | media | yes | Generate duration-aware videos through OpenRouter with prompt review, resolution/audio controls, and frame-continuous segment assembly. |
| `browser-preview-ops` | profile | misc | yes | Use when opening or verifying any web page in Hermes. |
| `hermes-desktop-plugins` | profile | misc | yes | Write desktop app plugins that add UI panes and commands. |
| `hermes-themes` | profile | misc | yes | Author a Hermes color theme that skins every surface. |
| `svg-illustration` | profile | misc | yes | Create hand-coded SVG illustrations (characters, scenes, icons) as standalone .s |
| `yuanbao` | profile | misc | yes | Yuanbao (元宝) groups: @mention users, query info/members. |
| `audiocraft` | profile | mlops | yes | AudioCraft: MusicGen text-to-music, AudioGen text-to-sound. |
| `colab-llm-inference` | profile | mlops | yes | Use when running LLM inference on Colab GPUs. |
| `llm-agent-lifecycle` | profile | mlops | yes | Unsloth GRPO training, HF export and vLLM serving lifecycle. |
| `llm-cpu-calculator` | profile | mlops | yes | Estimate CPU and RAM needs for plain-English LLM workloads. |
| `pi-model-specialization-orchestration` | profile | mlops | yes | Use when orchestrating staged local-model specialization. |
| `remote-gpu-model-specialization` | profile | mlops | yes | Use for SSH GPU model specialization workflows. |
| `segment-anything` | profile | mlops | yes | SAM: zero-shot image segmentation via points, boxes, masks. |
| `workflow-contract-gap-analysis` | profile | mlops | yes | Use when comparing setup and downstream pipeline workflows. |
| `command-output-tables` | profile | productivity | yes | Render command output (e.g. ls -alr) as a lossless table. |
| `document-generation` | profile | productivity | yes | Generate and verify professionally formatted PDF, DOCX, and Excel documents from |
| `petdex` | profile | productivity | yes | Install and select animated petdex mascots for Hermes. |
| `tui-widgets` | profile | productivity | yes | Author live widget apps for the Hermes TUI dock. |
| `evaluation-prompt-design` | profile | research | yes | Design, categorize, refine, and publish structured test prompts for comparing AI |
| `get-info` | profile | research | yes | Use when the user asks for news, information, or research on any topic within a  |
| `hermes-web-research` | profile | research | yes | Exa MCP backstops research engines with no web backend. |
| `polymarket` | profile | research | yes | Query Polymarket: markets, prices, orderbooks, history. |
| `technical-source-comparison` | profile | research | yes | Research current technical announcements, APIs, runtimes, and provider behavior  |
| `agent-skills-discovery` | profile | software-development | yes | Discover and install Agent Skills via npx and gh skill. |
| `agent-skills-publishing` | profile | software-development | yes | Use when adapting or publishing a Hermes skill for the cross-agent Agent Skills  |
| `chrome-prompt-api-pitfalls` | profile | software-development | yes | Use for Chrome Prompt API, Pyodide WASM, or COEP apps. |
| `code-explainer` | profile | software-development | yes | Use when building interactive codebase explainers. |
| `codebase-exploration` | profile | software-development | yes | Explore codebases with CodeGraph: symbols, calls, impact. |
| `cross-agent-skills` | profile | software-development | yes | Use when adapting, publishing, or installing skills across multiple AI coding ag |
| `git-workspace-init` | profile | software-development | yes | Make a root git repo over nested repos; skip gitlink traps. |
| `hermes-desktop-session-telemetry` | profile | software-development | yes | Use for session telemetry widgets. Seed from session.info. |
| `pi-extension-authoring` | profile | software-development | yes | Use when authoring TypeScript Pi extensions. |
| `pi-extension-explorer` | profile | software-development | yes | Explore Pi ecosystem repos with CodeGraph and Mermaid. |
| `pi-orchestrated-remote-workflows` | profile | software-development | yes | Use for Pi extensions coordinating resumable remote phases. |
| `prepare-python-folder` | profile | software-development | yes | Sets up a new Python project directory using uv. |
| `project-feature-maintenance` | profile | software-development | yes | Study, plan, harden, and verify project/workspace features with scoped files, de |
| `prime-agent-docs` | profile | software-development | yes | Prime Agent docs: RLM subagents, daemon, SDK, ACP/RPC, extensions. |
| `pyscript-pyodide-worker` | profile | software-development | yes | Pyodide WASM apps in Web Workers. Use for Python-in-browser. |
