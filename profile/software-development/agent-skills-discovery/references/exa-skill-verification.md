# Exa Skill Verification — Query Templates & Spillover Parsing

## Query templates (deferred tool `mcp__exa__web_search_exa`)

```js
// Generic
query = `${tool} agent skill teaches agent to use ${tool} CLI`
query = `${tool} CLI skills offer skills.sh agent skills`
query = `${tool} news latest headlines current events ${timespan}` // for get-info style
numResults = 15
```

Examples used:
- `runpod.io RunPod CLI skills offer skills.sh agent skills`
- `GitHub CLI gh skills agent skills skills.sh`
- `gh CLI agent skill teaches agent to use GitHub CLI pull request issue`

## Result format (plain text, NOT JSON)

```
Title: <title>
URL: <url>
Published: <date or N/A>
Author: <author>
Highlights:
<summary with [...] separators>
---
Title: <next>
...
```

## Spillover handling (>50KB)

Tool returns: `{"output": "...", "saved_to": "~/.hermes/cache/spillover/call_*.txt"}` with preview truncated.

```python
import pathlib, json
p = "~/.hermes/cache/spillover/call_xxx.txt"
j = json.loads(pathlib.Path(p).read_text())
raw = j["result"]                       # plain text, not JSON
entries = raw.split("\n---\n")
for e in entries:
    title = next((l for l in e.splitlines() if l.startswith("Title:")), "")
    pub = next((l for l in e.splitlines() if l.startswith("Published:")), "")
```

Pitfall: Do NOT `json.loads` the inner `Highlights:` text. Clean `[...]` markers, synthesize 2-4 sentence summaries, exclude URLs from tables.

## Deduplication rule (from get-info)

Collapse results where normalized Title matches + >60% highlights overlap. Keep earliest/most complete. Return ≥10 distinct rows when available; otherwise state "Only N unique developments found".

## Date normalization

- `Published: 2026-08-17T14:50:10.956Z` → `17/08/2026`
- `N/A` or relative ("7 hrs ago") → infer from highlights or use retrieval date `dd/mm/yyyy`.
- Footer: `**Source:** Exa MCP server (web_search_exa) | Retrieved on **dd/mm/yyyy**`
