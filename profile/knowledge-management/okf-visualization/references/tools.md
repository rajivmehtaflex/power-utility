# OKF Visualization Tools — Reference

## The task
Render/explore an OKF v0.2 bundle (directory of `.md` concepts with YAML frontmatter + cross-links) as an interactive knowledge graph or browser UI.

## Tools (all found via Exa web search in session 2026-07-27 "Visualizing the OKF Knowledge Bundle"; re-confirmed 2026-07-28)

### 1. okapi-okf (RECOMMENDED)
- `npx okapi-okf ./path-to-bundle` — npm `okapi-okf@0.2.1`, bin `okapi`, github `sebastienfi/okapi-okf-knowledge-studio`.
- Parses bundle → document graph (nodes = `.md`, edges = markdown links; code fences & `resource:` never become edges). Link resolution mirrors the OKF reference validator; broken links reported, never dangling.
- Features: force-directed graph sized by connectedness, colored by type; type filter; search (title/id/tag); focus; detail panel (frontmatter + rendered GFM + Links-to + Cited-by); Insights (orphans, broken links, disconnected groups, stale timestamps, type distribution); optional in-browser editing (writes `.md`); optional AI "ask" (BYO key).
- Observed output: `✔ Parsed phob_okf — 286 concepts, 6158 links` → `Local: http://127.0.0.1:4317`.
- Needs network once (npm fetch); cached + offline after.

### 2. okfgen (offline-friendly Python)
- `uvx okfgen generate . -o my-okf` then `uvx okfgen visualize my-okf -o graph.html`; `open graph.html`.
- Deterministic producer+consumer of OKF; viewer is a single self-contained HTML (no backend, no CDN, data stays local). Also `okfgen search`, `okfgen validate`, `okfgen ask`.

### 3. okf-viewer (read-only, offline)
- `npx okf-viewer open [path]` (default `.`); `okf-viewer validate <dir>` for v0.1 §9 conformance; `--bind 0.0.0.0 --port 3847` to expose.
- Directory tree + index-first browse + Concept view + bundle links + backlinks + filterable graph (type-colored, switchable layouts) + light/dark.

### 4. okf-kit (pip)
- `okf visualize` — collapsible tree explorer + detail pane (frontmatter, rendered body, Links-to, Cited-by); self-contained `viz.html`, no CDN. Replaces force graph (hairball on dense docs) with a tree.

### 5. Google reference visualizer
- From `GoogleCloudPlatform/knowledge-catalog` repo: `python -m reference_agent visualize --bundle ./bundles/<name>` writes `viz.html`. Cytoscape.js graph + marked markdown; CDN-loaded. Flags `--bundle` (req), `--out` (default `viz.html`), `--name`.
- Also: `scaccogatto/okf-skills` `okf_visualize.py` — single self-contained HTML graph; layouts cose/concentric/breadthfirst/circle/grid; per-type filter; search; neighbor highlight; auto switches to concentric above ~AUTO_COSE_MAX concepts (force freezes on large bundles).

## Offline custom fallback (only if all above unavailable)
If npm/uv/network blocked, build a self-contained HTML with stdlib Python + vendored `vis-network`:
- Parser: walk bundle, parse minimal YAML frontmatter, extract `## Related` links `](/path/file.md)`, dedupe undirected. Node id = `/<relpath>`.
- Builder: embed `{nodes, edges, stats}` JSON into an HTML template; render with `vis-network` (nodes colored by top-level folder, sized by degree; search box; per-category checkboxes; click → detail panel linking to the `file://` resource).
- Vendor `https://unpkg.com/vis-network@9.1.9/standalone/umd/vis-network.min.js` into `assets/`; include a unpkg `<script>` fallback in the HTML.
- No PyYAML/pyvis needed — runs on system Python 3.9.6.

## Provenance
- OKF spec: `github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md`
- Google announcement: `cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing`
- Prior session that first found these tools: `2026-07-27_164219_8a8f11` ("Visualizing the OKF Knowledge Bundle").
