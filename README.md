# Skill Collections — Cross-Agent Mono-Repo

Spec: https://agentskills.io/specification.md · 73 skills · synced 2026-09-17

[![skills.sh](https://skills.sh/b/rajivmehtaflex/power-utility)](https://skills.sh/rajivmehtaflex/power-utility)

Normalized copies of every user-added skill. Live sources
(~/.hermes/skills, ~/.agents/skills, ~/Documents/Dev/Skills) are never modified;
re-sync with `uv run python -m src.skill_collections.sync`.

## Install with `npx skills` (all agents)

The [skills CLI](https://github.com/vercel-labs/skills) auto-detects installed
agents (Claude Code, Codex, Cursor, Copilot, OpenCode, …) or takes `--agent`:

```bash
# Install ALL 73 skills (auto-detect agents, interactive pick)
npx skills add rajivmehtaflex/power-utility

# List available skills without installing
npx skills add rajivmehtaflex/power-utility --list

# Install ONE specific skill
npx skills add rajivmehtaflex/power-utility --skill get-info

# Install the 1-minute video generation skill
npx skills add rajivmehtaflex/power-utility --skill 1-minute-video-gen

# Install SEVERAL skills
npx skills add rajivmehtaflex/power-utility --skill modal-deploy --skill gh-cli-ops

# Install dynamic-orchestrator for Codex globally
npx skills add rajivmehtaflex/power-utility --skill dynamic-orchestrator --agent codex --global --copy -y

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

## Use `dynamic-orchestrator`

Invoke the skill explicitly with a substantive implementation request:

```text
$dynamic-orchestrator

Add CSV export to the reporting module.

Goal: users can export the currently filtered report as a CSV file.
Acceptance criteria:
- preserve the active filters and column order;
- handle empty results with a valid header-only CSV;
- add focused tests for filtered and empty reports;
- run the relevant test suite and report the exact verification output.

First inspect the repository and decide whether delegation is useful. If you
delegate, keep file ownership disjoint, route all findings through the lead,
and use a separate reviewer before reporting completion. If the runtime has no
real subagent controls, state that limitation instead of simulating agents.
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

### Repo-owned skills and generated refresh (maintainer)

`repo-owned/` contains skills maintained directly in this repository. The
`unsloth-workflows` skill covers Linux/NVIDIA Unsloth setup, data validation,
text SFT, evaluation, export, and framework-wide guidance:

```bash
npx skills add rajivmehtaflex/power-utility --skill unsloth-workflows
python repo-owned/unsloth-workflows/scripts/unsloth_workflow.py doctor --project .
```

The `hf-generative-model-converter` skill converts pinned Hugging Face
text-generation models to GGUF with a source-built llama.cpp toolchain or to
ONNX with Optimum plus a provenance-verified ONNX Runtime, validates the
converted model by real inference, and publishes verified packages to the
Hugging Face Hub behind a SHA-256 manifest and guarded publication helper.
Verified scope is deliberately narrow: GGUF and ONNX on linux-x86_64 CPU
(demonstrated with `Qwen/Qwen3-0.6B`); the VLM ONNX row is deferred and
LiteRT-LM is planned — neither is advertised by the skill. The skill
package is Apache-2.0 — converted models keep their own source license terms,
and publication requires that license status be resolved first:

```bash
npx skills add rajivmehtaflex/power-utility --skill hf-generative-model-converter
uv run --project tools/skill-validation skills-ref validate repo-owned/hf-generative-model-converter
```

Generated collections must be built in a separate staging directory and then
imported. The import updates only `agents-shared/`, `dev-workspace/`, and
`profile/`; it preserves `repo-owned/`, `docs/`, and repository metadata:

```bash
python tools/import_generated_skills.py /path/to/staged-collection --repo .
```

### Prompt cookbook: `unsloth-workflows`

Use these prompts after installing the skill. Start each request by naming the
mode you want: **Discuss** is read-only, **Prepare** creates reviewable files,
and **Execute** may install packages and run GPU work inside the selected
project.

#### Build a mental model

```text
Use unsloth-workflows in Discuss mode. Explain how CPT, SFT, DPO, GRPO,
LoRA, QLoRA, full fine-tuning, quantization, GGUF, and vLLM fit together.
Use one small customer-support example and clearly separate the training
objective from the parameter-update method. Do not install anything.
```

#### Inspect a Linux/NVIDIA machine

```text
Use unsloth-workflows in Discuss mode. Inspect this Linux/NVIDIA project with
doctor only. Report the Python version, NVIDIA driver, visible GPU memory,
CUDA availability, expected project environment, and any blocker. Do not
create `.unsloth`, install packages, or download a model.
```

#### Prepare a dataset and configuration

```text
Use unsloth-workflows in Prepare mode. I have `data/support.jsonl` with
ChatML messages. Validate required roles, empty responses, duplicates,
train/eval overlap, and likely token-length risks. Create a reviewable
`run.json` for QLoRA SFT of `Qwen/Qwen2.5-0.5B-Instruct`, max sequence length
512, batch size 1, 10 smoke-test steps, and an explicit evaluation file.
Do not install packages or start training.
```

#### Run a small SFT job

```text
Use unsloth-workflows in Execute mode for this project. First run doctor,
then validate the configured train and eval files, then create or reuse the
project-local `.unsloth/venv`. Run a 10-step QLoRA SFT smoke test, save a
checkpoint, record model revision, dataset hashes, dependency versions, and
the chat template, and report each phase separately. Stop before training if
the host is not Linux with a visible NVIDIA GPU.
```

#### Compare the base model with the adapter

```text
Use unsloth-workflows in Execute mode. Evaluate the base model and the adapter
from `outputs/` on `data/eval.jsonl`. Support either ChatML or Alpaca records,
report held-out loss, exact-match when expected answers exist, and save sample
generations. Load only one model copy at a time if VRAM is limited. Do not
claim improvement unless the measured results support it.
```

#### Export and verify a model

```text
Use unsloth-workflows in Execute mode. Export the trained adapter from
`outputs/` as a merged 16-bit model and as GGUF Q4_K_M. Preserve tokenizer and
chat-template metadata. Reload every format that the selected runtime
supports, run a short generation, and report which artifacts were actually
verified. Keep the original training output unchanged.
```

#### Ask for an advanced workflow

```text
Use unsloth-workflows in Prepare mode. I want to train a vision model with
GRPO using a reward function that checks structured answers. Read the current
official Unsloth example, check the installed API and GPU requirements,
prepare a task-specific script and dependency list, and propose a bounded
smoke test. Do not execute until the script and risks are reviewable.
```

#### Diagnose a failed run

```text
Use unsloth-workflows in Discuss mode to diagnose this failure. Inspect the
command, resolved config, environment report, traceback, and output directory.
Classify the cause as data, chat-template/tokenization, dependency/CUDA,
memory, training configuration, or export/runtime mismatch. Give the smallest
safe next check and do not reinstall or delete anything.
```

For reliable results, include the model revision, dataset paths, intended
training method, GPU name and memory, sequence length, output directory, and
whether the request is a smoke test or a production run.

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
| `unsloth-workflows` | repo-owned | mlops | yes | Explain, prepare, and execute Unsloth workflows on Linux/NVIDIA machines. |
| `data-to-okf` | agents-shared | — | yes | Converts any local folder of mixed documents (docx, pdf, xlsx, duckdb, csv, imag |
| `release-notes` | agents-shared | — | yes | >- |
| `graph-flow` | dev-workspace | — | yes | Use when coordinating a repository implementation from a goal through approved,  |
| `intent-first-action-boundaries` | profile | assistant-behavior | yes | Use for question-vs-action intent routing. |
| `hermes-agent-api-bridge` | profile | autonomous-ai-agents | yes | Bridge Hermes Agent to external apps via subprocess or HTTP. |
| `pi-operator` | profile | autonomous-ai-agents | yes | Operate and verify the Pi coding-agent CLI safely. |
| `subagent-orchestration` | profile | autonomous-ai-agents | yes | Decompose implementation plans into parallel-safe task waves and dispatch them v |
| `dynamic-orchestrator` | profile | autonomous-ai-agents | yes | Coordinate substantive implementation work with real subagents using adaptive assignments, lead-mediated handoffs, review, and verified reporting. |
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
