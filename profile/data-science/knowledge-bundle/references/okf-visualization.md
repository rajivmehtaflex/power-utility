# OKF v0.2 Visualization

## Tools

### okapi-okf (Recommended)
Full interactive knowledge studio — graph explorer, detail panel, editor, insights, AI Q&A.

```bash
# Install and run (from any directory containing an OKF bundle)
npx okapi-okf <path-to-bundle>
# Serves on http://127.0.0.1:3847 by default
```

Features: force-directed graph, type-colored nodes, click-to-expand detail panels, search, type filter, insights (orphans, broken links, disconnected groups), in-browser editing, AI-assisted Q&A with graph citations.

### okfgen (Quick graph)
Generates a single self-contained `graph.html` — no backend, no install.

```bash
pip install okfgen
okfgen generate <bundle-dir> -o /tmp/bundle
okfgen visualize /tmp/bundle -o /tmp/bundle/graph.html
open /tmp/bundle/graph.html
```

### Google's reference_agent visualize
From the official Google knowledge-catalog repo. Requires cloning the repo.

```bash
cd /tmp && git clone https://github.com/GoogleCloudPlatform/knowledge-catalog.git
cd knowledge-catalog
/Users/rajivmehtapy/.hermes/hermes-agent/venv/bin/python \
  -m reference_agent visualize --bundle <bundle-dir> --out <bundle-dir>/viz.html
open <bundle-dir>/viz.html
```

Layouts: `cose` (force-directed, default ≤150 nodes), `concentric`, `breadthfirst`, `circle`, `grid`. For bundles >150 concepts, use `--layout concentric` or `--layout breadthfirst` to avoid force-layout freezing.

## Bundle Structure (OKF v0.2)

OKF bundles are directories of markdown files with YAML frontmatter. `fc-plus-okf/` follows this structure:

- `index.md` — top-level, lists subfolders
- `<subfolder>/index.md` — concept listing for that folder
- `<concept>.md` — individual concept with `type`, `title`, `description`, `resource` frontmatter
- `log.md` — generation/change log

Navigation path: top index → subfolder index → concept file → `resource:` URI following to original source.
