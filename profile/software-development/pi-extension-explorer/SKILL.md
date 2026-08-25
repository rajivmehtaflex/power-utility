---
name: pi-extension-explorer
description: Explore Pi ecosystem repos with CodeGraph and Mermaid.
license: MIT
metadata:
  author: Rajiv Mehta (rajivmehtapy), Hermes Agent
  hermes_related_skills: codebase-exploration, github-repo-management
  hermes_tags: Pi, ecosystem, CodeGraph, Mermaid, code-exploration
  platforms: linux, macos, windows
  version: 0.1.0
---

# Pi Ecosystem Explorer

Explores any repository in the Pi coding-agent ecosystem (extension, core/runtime, CLI, library, or skill), explains its role and integration from verified source, and writes a Mermaid flow diagram plus rendered SVG into the repository root. It never executes the repo's own code.

## When to Use

- User runs `/pi-extension-explorer` with a Pi repository URL or local path.
- "Explore this Pi repo: <url>" (including the Hermes `@url:` form) or "Use this local Pi folder: <path>".
- "Explain this repo's role in Pi and create the flow diagram."

Don't use for: non-Pi repositories (report the closest detected role instead of inventing a Pi integration), or requests that require running the repo's install/build/test scripts.

## Prerequisites

- `git` and `codegraph` on PATH (install `codegraph` via `brew install codegraph` on macOS).
- Node/npm/npx for Mermaid CLI (`@mermaid-js/mermaid-cli`), fetched via `npx -y` on first run.
- CodeGraph MCP server available (`mcp__codegraph__codegraph_explore`).

## How to Run

Accept a plain task description from the user (a URL, a local path, or "explore <repo>"). Never ask the user for internal flags. Internally:

1. Normalize the input into `repository_path` (and `repository_url` if a URL was given).
2. Clone (if URL and destination absent) or verify the local path.
3. Anchor the desktop workspace via `project_create` when the Project plugin is available.

## Quick Reference

```text
git clone <url> <destination>
codegraph init -v            # only when .codegraph/ is absent
codegraph sync               # only when pendingChanges/mismatch reported
codegraph status -j          # always capture status before/after
npx -y @mermaid-js/mermaid-cli -i <in>.mmd -o <out>.svg
```

## Procedure

1. **Acquire + anchor** (see How to Run). Verify `pwd` equals the repo path and report `git status --short --branch`. Never delete/reset an existing checkout.
2. **CodeGraph**: run `codegraph --version`; `codegraph init -v` if `.codegraph/` is absent, else `codegraph sync` only on reported changes; finish with `codegraph status -j` and capture initialized/projectPath/fileCount/nodeCount/edgeCount/pendingChanges/state.
3. **Detect role**: `read_file` on `package.json` and README; `search_files` (target=`files`) for the entry point, `bin`, a `skills/` dir, and any `pi` block. Assign one role from the table below and record the evidence.
4. **Explore** with CodeGraph MCP (`mcp__codegraph__codegraph_explore`, absolute `projectPath`) using the role-keyed query.
5. **Explain** role + behavior: identity, purpose, entry/load path, execution flow, CLI/helper surface (if any).
6. **Author** the `.mmd` from the evidence table using the role template, with an authoring-time CodeGraph lane as a comment/note (not a runtime node).
7. **Render** the SVG with Mermaid CLI and verify it is non-empty.

### Role templates

| Role | Detection signal | Diagram flow |
|---|---|---|
| Extension / plugin | `pi` block, `pi.extensions`, `pi.skills`, or peer-dep on `@earendil-works/pi-*` with an entry that registers into Pi | user prompt → Pi agent loop → loads extension / registers surface → LLM selects surface → handler → result → response |
| Core / runtime | `pi-ai`, `pi-tui`, `pi-coding-agent`, or `pi-mono` core | user prompt → agent loop → model → action/tool → response |
| CLI tool | `bin` entry whose main is a standalone command | user invokes command → parse args → config/discovery → action → output |
| Library / SDK | `exports`/`main` only; no `pi` block, no `bin` | consumer imports → public API → result |
| Skill collection | ships a `skills/` dir or `pi.skills` | agent loads skill → follows instructions → artifact |

Artifact names: `<repo-name>-pi-flow.mmd` and `<repo-name>-pi-flow.svg` at the repository root. Preserve unrelated existing files (write a timestamped sibling) unless the skill's generated marker is present.

## Pitfalls

- Stale index: run `codegraph sync` only when `pendingChanges`/`worktreeMismatch` is non-zero; do not rebuild a healthy index.
- Role misclassification: confirm by reading the entry point and `package.json`, not the package name alone.
- Never run the repo's install/build/test scripts or launch servers.
- Mermaid CLI may fail with a missing `chrome-headless-shell`; run the matching `puppeteer browsers install chrome-headless-shell@<ver>` command, retry, and verify the output file exists — not just the "Generating" log.
- Do not put `%%` comment lines before the `flowchart TD` / `sequenceDiagram` declaration — some Mermaid versions raise a parse error on the leading comment block. Start the `.mmd` with the diagram directive and place `%%` metadata comments indented immediately inside the body.
- CodeGraph is authoring-time only; never draw it as a runtime node in the diagram.
- `project_create` may be unavailable in some profiles — fall back to `terminal(workdir=<repo path>)`.

## Verification

- `pwd` equals the target repository path.
- `codegraph status -j` → `initialized=true`, `index.state=complete`, `pendingChanges=0`.
- `.mmd` contains `flowchart`/`sequenceDiagram`, the role-appropriate entry point, the processing path, and a result/response node.
- `.svg` exists and is non-empty.
