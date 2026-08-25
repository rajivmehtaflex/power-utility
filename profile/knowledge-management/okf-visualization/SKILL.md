---
name: okf-visualization
description: Visualize an OKF knowledge bundle; use npx okapi-okf first.
license: MIT
metadata:
  author: Hermes Agent
  hermes_tags: okf, knowledge-graph, visualization, markdown, okapi
  platforms: linux, macos, windows
  version: 1.0.0
---

# OKF Bundle Visualization & Exploration

## Overview
OKF (Open Knowledge Format, v0.2) is Google's vendor-neutral format: a directory of plain `.md` files, each with YAML frontmatter (`type`, `title`, `description`, `resource: file://…`, `tags`) and a `## Related` cross-link section. When a user shares an "OKF folder" and wants to *see* it, the right move is almost always a **ready-made viewer**, not a hand-rolled graph.

## When to use
- User shares a folder and asks to "visualize", "explore", "browse", or "see the knowledge graph" of it.
- The folder contains many `.md` files with `---` frontmatter and `## Related` / cross-links.

## Workflow (preferred path)
1. **Confirm it's OKF** (read-only): `index.md` with `okf_version:`; count concepts: `find . -name '*.md' | grep -v -E '/index.md|/log.md' | wc -l`.
2. **Recall prior research FIRST** — `session_search(query="OKF visualize")` before building anything (see Pitfalls).
3. **Launch the viewer** (read-only; does not touch bundle files):
   ```bash
   cd <parent-of-bundle>
   npx okapi-okf ./<bundle>
   ```
   First run fetches the package from npm (network once); afterwards cached + offline. Prints a local URL (e.g. `http://127.0.0.1:4317`) and "Parsed <bundle> — N concepts, M links".
4. **Verify**: `curl -s -o /dev/null -w "HTTP %{http_code}\n" <url>` → `HTTP 200`. Open the URL.
5. **User explores**: graph (nodes sized by connectedness, colored by type), type filter, search, click → detail panel (frontmatter + body + Links-to / Cited-by), Insights (orphans, broken links, disconnected groups).

## Ready-made tools (condensed)
Full commands, versions, and provenance in `references/tools.md`. Summary:
- **`npx okapi-okf ./bundle`** (v0.2.1, *Okapi OKF Knowledge Studio*) — **recommended**. Interactive graph + editing(opt-in) + AI ask(opt-in) + Insights. Bundled SPA, no CDN at view time.
- **`uvx okfgen visualize ./bundle -o graph.html`** (Python, deterministic) — self-contained graph HTML, no CDN. Offline fallback if npm blocked.
- **`npx okf-viewer open ./bundle`** — read-only tree + graph viewer, offline.
- **`okf-kit` (pip)** — `okf visualize` tree explorer, no CDN.
- **Google reference**: `python -m reference_agent visualize --bundle ./bundles/<name>` → `viz.html` (Cytoscape.js + marked, CDN).

## Pitfalls
- **CHECK SESSION HISTORY BEFORE BUILDING CUSTOM.** The user often already researched the exact tool in a prior session. A 2026-07-27 session ("Visualizing the OKF Knowledge Bundle") had already identified `npx okapi-okf` via web search; jumping straight to a from-scratch `vis-network` HTML builder wasted a round-trip. Always `session_search` for "OKF" / "visualize" first.
- **Edits are opt-in.** Okapi can write back to the `.md` files via its in-browser editor. For view-only requests, do NOT use the save/edit features.
- **Resource paths are machine-specific.** `resource: file:///Users/…` URIs only resolve on the machine that generated the bundle.
- **Link-count differs by extractor.** Okapi counts *all* markdown cross-links (e.g. 6158 for phob_okf); a `## Related`-only parse counts fewer (5789). Not a conflict — different extraction scopes.
- **Custom zero-dep build is the fallback, not the default.** Only build a from-scratch HTML graph (stdlib Python + vendored `vis-network`) if npm/uv/network are unavailable. See `references/tools.md`.

## Verification
- `npx okapi-okf --help` exits 0 (also triggers the one-time fetch).
- Server returns HTTP 200; in-browser graph shows ~N nodes; Insights shows 0 broken links (expected for a clean bundle).

## Serving Procedure (absorbed from okf-explain)

1. **Collect inputs.** Get `BUNDLE_PATH` and `PORT` (default 4317). Confirm the path exists.
2. **Launch as a backend service** via `terminal` with `background=true`:
   ```bash
   npx okapi-okf "<BUNDLE_PATH>" -p <PORT> --no-open
   ```
   Keep watch on (default) for live-reload; `--no-watch` for static serve.
3. **Wait for readiness** — poll process output until:
   ```
   ✔ Parsed <name> — N concepts, M links
     ➜ Local:  http://127.0.0.1:<ACTUAL_PORT>
   ```
   Record ACTUAL_PORT — it may differ from `-p` if busy.
4. **Health-check:** `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:<ACTUAL_PORT>/` → expect 200. The page is an SPA shell; curl only proves the server is up — use a browser/preview for visual verification.
5. **Surface the URL** via `open_preview` or report the link.
6. **Stop when done** — `process(action='kill')` on the tracked session; the server persists after the turn ends.

Quick flag reference: `-p/--port` (auto-increments), `--host`, `--no-open`, `--no-watch`, `--ai --provider openai|anthropic` (opt-in, needs key), `lint <bundle>` for conformance check.

## References
- `references/tools.md` — full tool list with exact commands, versions, session provenance, and the offline custom-build approach.
