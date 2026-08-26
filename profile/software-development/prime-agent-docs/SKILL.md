---
name: prime-agent-docs
description: Complete reference and documentation for Prime Agent (RLM-native coding and research agent harness). Use when developing with, configuring, embedding, or extending Prime Agent, including CLI usage, RLM programming model, subagents, daemon runtime, extensions, Python skills, MCP integrations, SDK, ACP/RPC modes, providers, models, and session management.
license: Apache-2.0
metadata:
  author: Prime Intellect
  project: prime-agent
  type: reference
---

# Prime Agent Documentation (`prime-agent-docs`)

## Overview

**Prime Agent** is an RLM-native (Recursive Language Model) coding and research harness built around a persistent IPython kernel, recursive subagents, durable sessions, and a multi-process local runtime.

### Core Architecture

- **Persistent Kernel**: Executes code interactively in a stateful IPython environment across turns.
- **Recursive Subagents**: Spawns isolated or shared subagent sessions to solve subtasks autonomously.
- **Daemon & Runtime**: Decouples UI clients from background execution workers with IPC and ZeroMQ transports.
- **Durable Sessions**: JSONL-backed tree and timeline storage with branching, compaction, and replayability.
- **Flexible Integration**: Supports interactive TUI, headless CLI, SDK (Node.js/TypeScript), ACP (Agent Client Protocol), and RPC (stdin/stdout JSONL).

---

## When to Use This Skill

Activate and consult this skill whenever you need to:
- Understand or configure Prime Agent CLI commands, keybindings, flags, or settings.
- Build, run, or debug recursive RLM subagents or persistent Python kernel tasks.
- Create custom **Extensions** (TypeScript), **Skills** (Markdown/Python), **MCP integrations**, or **Themes**.
- Integrate or embed Prime Agent programmatically via **SDK**, **ACP mode**, **RPC mode**, or **JSON event streams**.
- Configure AI model providers (OpenAI, Anthropic, DeepSeek, local models, custom endpoints, OAuth).
- Understand Prime Agent internal architecture: Daemon supervisor, worker lifecycle, ZeroMQ kernel transport, and session tree storage.

---

## Quick Start & Installation

### Install Stable Release

```bash
# Linux / macOS
curl -fsSL https://app.primeintellect.ai/prime-agent/install.sh | sh
```

### Launch Interactive Session

```bash
cd /path/to/project
prime-agent
```

### Common CLI Invocations

```bash
# Authenticate providers or configure API keys
prime-agent /login

# Run non-interactively with a single prompt
prime-agent -p "Analyze tests and fix failures"

# Resume an existing session by ID
prime-agent --session <session-id>

# Run in ACP (Agent Client Protocol) mode
prime-agent --acp

# Run in JSON event stream mode
prime-agent --json
```

---

## CLI & Interactive Quick Reference

| Feature / Shortcut | Description | Reference |
| :--- | :--- | :--- |
| `/login` | Manage provider logins and API keys | [providers.md](references/providers.md) |
| `/model` | Switch active model or view model list | [models.md](references/models.md) |
| `/compact` | Compact context window and summarize history | [compaction.md](references/compaction.md) |
| `/tree` | Navigate session branch tree | [sessions.md](references/sessions.md) |
| `Ctrl+C` | Interrupt current execution / cancel action | [keybindings.md](references/keybindings.md) |
| `Ctrl+D` | Exit interactive session | [usage.md](references/usage.md) |
| `Ctrl+P` / `Ctrl+N` | History navigation | [keybindings.md](references/keybindings.md) |

---

## Progressive Disclosure Reference Index

Detailed guides and specifications are organized in the [`references/`](references/) directory. Load specific documents on demand based on your task:

### 1. Getting Started & User Guides
- [Quickstart Guide](references/quickstart.md): Complete first-run walkthrough, provider setup, and initial session.
- [Using Prime Agent](references/usage.md): Interactive mode, subagent invocation, slash commands, CLI reference.
- [Settings Reference](references/settings.md): Global and project configuration schema (`settings.json`).
- [Keybindings Guide](references/keybindings.md): Default shortcuts, customizable keymaps, and action identifiers.
- [Themes & Styling](references/themes.md): Terminal UI color themes, syntax highlighting, and custom styles.

### 2. Core Concepts & Runtime
- [Architecture Overview](references/architecture.md): Client, daemon, worker, session, kernel, provider, and storage boundaries.
- [RLM Programming Model](references/rlm.md): Recursive language model paradigm, programmatic state, subagents, and Python execution.
- [Long-Running & Background Agents](references/long-running-agents.md): Daemon workers, messaging, heartbeats, goals, schedules, and autonomous mode.
- [Sessions & Branching](references/sessions.md): Tree navigation, checkpoints, branch switching, and persistence.
- [Compaction & Summarization](references/compaction.md): Context window management, branch summarization, and token optimization.

### 3. Customization & Extensions
- [Extensions Guide](references/extensions.md): Comprehensive TypeScript extension system for custom tools, commands, events, and UI.
- [Skills Guide](references/skills.md): Authoring Markdown and Python-backed skills for Prime Agent.
- [MCP Integrations](references/mcp-integrations.md): Integrating Model Context Protocol servers through Python skills without tool bloat.
- [Prompt Templates](references/prompt-templates.md): Creating reusable slash-command prompt expansions.
- [Packages](references/packages.md): Packaging and distributing extensions, skills, prompts, and themes.
- [Custom Models](references/models.md): Adding custom model endpoints, token limits, and pricing.
- [Custom Providers](references/custom-provider.md): Implementing custom API adapters, stream handlers, and auth workflows.

### 4. Programmatic Usage & Protocols
- [SDK Reference](references/sdk.md): Embedding Prime Agent into Node.js / TypeScript host applications.
- [ACP Mode](references/acp.md): Driving Prime Agent over Agent Client Protocol from external editors/tools.
- [RPC Mode](references/rpc.md): Interfacing via bidirectional JSONL over standard input/output.
- [JSON Stream Mode](references/json.md): Streaming structured JSON events for headless CI/CD and automation.
- [TUI Components](references/tui.md): Building custom interactive widgets and displays with Prime Agent TUI framework.

### 5. Platform Setup & Environment
- [Terminal Setup](references/terminal-setup.md): Terminal emulator configuration (Ghostty, iTerm2, Kitty, WezTerm, Alacritty).
- [Tmux Integration](references/tmux.md): Running Prime Agent smoothly inside Tmux sessions.
- [Shell Aliases](references/shell-aliases.md): Productivity aliases and shell completions.
- [Windows Setup](references/windows.md): WSL2 recommendations and native Windows considerations.
- [Termux on Android](references/termux.md): Mobile setup and troubleshooting on Android Termux.

### 6. Architecture & Internals
- [Daemon Architecture](references/daemon.md): Supervisor process, worker catalog, lifecycle management, and failover recovery.
- [Agent Connection Architecture](references/agent-connection.md): IPC, socket protocols, and connection handling.
- [RLM Runtime Architecture](references/rlm-runtime.md): ZeroMQ IPython kernel integration and recursive subagent execution pipeline.
- [Session Format Specification](references/session-format.md): Detailed JSONL schema, message entry types, and `SessionManager` internals.
- [Development Guide](references/development.md): Contributing to Prime Agent, local monorepo setup, build scripts, and test suite.

---

## Extension & Skill Authoring Quick Reference

### Creating a Markdown Skill

Place skills in `.prime-agent/skills/<skill-name>/SKILL.md` or `~/.prime-agent/skills/<skill-name>/SKILL.md`:

```markdown
---
name: my-skill
description: Use when performing specific domain workflows or tasks.
---

# My Skill Title

## Workflow
1. Step one instructions
2. Step two instructions
```

### Creating a TypeScript Extension

Place extensions in `.prime-agent/extensions/` or configure via `settings.json`:

```typescript
import { ExtensionContext } from "@prime-agent/sdk";

export function activate(context: ExtensionContext) {
  context.registerCommand("my-command", async (args) => {
    return `Executed with ${args}`;
  });
}
```

For advanced extensions with custom tools, UI widgets, or event listeners, see [extensions.md](references/extensions.md).
