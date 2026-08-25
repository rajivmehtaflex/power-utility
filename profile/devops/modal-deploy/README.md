# Modal Deploy — Agent Skill

Deploy GPU-enabled applications to [Modal](https://modal.com) cloud with intelligent configuration, GPU pre-checks, and best practices.

Works with **Claude Code**, **Codex**, **Antigravity**, and **Hermes Agent**.

## Quick Install

### Option 1: `npx skills add` (Recommended — All Agents)

```bash
# Auto-detect and install for all available agents
npx skills add rajivmehtaflex/modal-deploy

# Install for a specific agent
npx skills add rajivmehtaflex/modal-deploy -a claude-code
npx skills add rajivmehtaflex/modal-deploy -a codex
npx skills add rajivmehtaflex/modal-deploy -a antigravity

# Install globally (user-level, not project-level)
npx skills add rajivmehtaflex/modal-deploy -g

# List available skills without installing
npx skills add rajivmehtaflex/modal-deploy -l
```

### Option 2: One-Line Install Script

```bash
curl -fsSL https://raw.githubusercontent.com/rajivmehtaflex/modal-deploy/main/install.sh | bash
```

The script auto-detects installed agents (Hermes, Claude Code, Codex) and copies the skill to the correct location for each.

### Option 3: Manual Install

```bash
# Clone
git clone https://github.com/rajivmehtaflex/modal-deploy.git

# Hermes Agent
mkdir -p ~/.hermes/skills/mlops/
cp -r modal-deploy ~/.hermes/skills/mlops/modal-deploy

# Claude Code
mkdir -p ~/.claude/skills/
cp -r modal-deploy ~/.claude/skills/modal-deploy

# Codex
mkdir -p ~/.codex/skills/
cp -r modal-deploy ~/.codex/skills/modal-deploy
```

## Features

- **GPU Support**: T4, L4, A10, L40S, A100, H100, H200, B200
- **Pricing**: $0.59/h (T4) to $6.25/h (B200)
- **GPU Pre-Check**: Timeout-bounded allocation test (`check_gpu.py`) for scarce GPUs
- **Templates**: Complete deployable web-terminal app — `modal_app.py`, `main.py` (PTY-WebSocket bridge), `static/index.html` (xterm.js), `pyproject.toml`, `deploy.sh`, `check_gpu.py`, `.env.example`
- **Best Practices**: Mount filtering, WebSocket PTY bridge, bundle optimization
- **Cross-Agent**: Follows the [Agent Skills](https://agentskills.io) open specification

## Quick Deploy

```bash
cp -r templates my-terminal && cd my-terminal
cp .env.example .env          # edit resources
uv sync                       # install dependencies
./deploy.sh                   # prints the https://...modal.run URL
```

## Sample Prompts

You can use these example prompts to instruct your AI agent using the `modal-deploy` skill:

### 1. CPU & RAM (CPU-only)
> "Use the modal-deploy skill to allocate a machine with 2-core cpu and 4-gb ram. I want to access this machine via web-terminal."

### 2. GPU, CPU, & RAM
> "Use the modal-deploy skill to deploy a machine with 4-core cpu, 16-gb ram, and 1 A10 GPU."

### 3. Persistent Storage
> "Use the modal-deploy skill to allocate a machine with 2-core cpu and 4-gb ram, and mount a persistent storage volume named 'my-persistent-workspace' to /workspace so that my environment data is saved."

## Agent Skills Specification

This skill conforms to the [Agent Skills open specification](https://agentskills.io):

| Field | Value |
|-------|-------|
| `name` | `modal-deploy` |
| `license` | MIT |
| `compatibility` | Claude Code, Codex, Antigravity, Hermes Agent |
| `allowed-tools` | Bash, Read, Write, Edit |

## License

MIT
