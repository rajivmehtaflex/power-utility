---
name: get-info
description: "Use when the user asks for news, information, or research on any topic within a specific time window. Searches the Exa MCP server (web_search_exa) and returns results in a clean tabular format with Date, Title, and Content columns. Accepts two parameters: topic and timespan."
license: MIT
metadata:
  author: Hermes Agent
  hermes_related_skills: ""
  hermes_tags: news, research, exa, mcp, web-search, information
  version: 1.0.0
---

# Get INFO — Exa MCP News & Research Search

## Overview

This skill retrieves news and information about any topic for a given time period using the **Exa MCP server** (`web_search_exa` tool). Results are formatted as a clean markdown table with three columns: **Date**, **Title**, and **Content**. Links are excluded from the output.

## When to Use

- User asks for news about a topic (e.g., "give me news about India")
- User asks for information within a specific time window (e.g., "last 24 hours", "this week")
- User wants research results presented in a tabular format without links
- User explicitly requests using the Exa MCP server

## Parameters

| Parameter  | Required | Description | Example |
|------------|----------|-------------|---------|
| `topic`    | Yes      | The subject to search for. Can be a country, event, technology, person, company, etc. | `India`, `AI regulation`, `Tesla earnings` |
| `timespan` | Yes      | The time window for results. Expressed as a natural language duration. | `last 24 hours`, `last 7 days`, `this week`, `last month` |

## Workflow

### Step 1 — Build the Search Query

Construct a semantically rich search query from the two parameters:

```
"{topic} news latest headlines current events {timespan}"
```

Examples:
- `topic=India`, `timespan=last 24 hours` → `"India news today latest headlines current events last 24 hours"`
- `topic=AI regulation`, `timespan=this week` → `"AI regulation news latest headlines current events this week"`
- `topic=SpaceX`, `timespan=last 7 days` → `"SpaceX news latest headlines current events last 7 days"`

### Step 2 — Execute the Exa Search

Call the Exa MCP `web_search_exa` tool with the constructed query:

```
mcp_exa_web_search_exa(query="<constructed query>", numResults=15)
```

If the `mcp_exa_*` tools are available in the current session, use them directly. In desktop sessions they may be registered as **deferred tools** — if not directly callable, `tool_describe` the exact registered name (e.g. `mcp__exa__web_search_exa`) and invoke it via `tool_call`; only drop to the Python fallback below if that path also fails.

**Fallback — Direct MCP Client Connection:**

If the Exa MCP tools are NOT registered in the current session (unstable HTTP Streamable connection), connect directly using the Hermes venv Python:

```python
~/.hermes/hermes-agent/venv/bin/python << 'PYEOF'
import asyncio
import json
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def main():
    async with streamablehttp_client("https://mcp.exa.ai/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("web_search_exa", {
                "query": "<QUERY_HERE>",
                "numResults": 15
            })
            for content in result.content:
                if hasattr(content, 'text'):
                    print(content.text)

asyncio.run(main())
PYEOF
```

**IMPORTANT:** The result text is NOT JSON — it is plain text with entries structured as:
```
Title: <title>
URL: <url>
Published: <date or N/A>
Author: <author or N/A>
Highlights:
<summary text with [...] separators>
---
```

Parse the plain text output; do NOT attempt `json.loads()` on it.

### Step 3 — Parse Results

Extract from each result entry:
- **Date:** Use the `Published:` field if available (convert to `dd/mm/yyyy` format). If `N/A`, infer the date from highlights (e.g., "7 hrs ago" → calculate from today's date) or use today's date.
- **Title:** From the `Title:` field.
- **Content:** Synthesize from the `Highlights:` section. Clean up `[...]` markers. Provide a concise 2-4 sentence summary of the key points.

### Step 4 — Format Output

Present results in a markdown table with exactly these columns:

```
| Date [dd/mm/yyyy] | Title | Content |
|-------------------|-------|---------|
| 17/06/2026 | ... | ... |
```

Rules:
- **Date** column: always `dd/mm/yyyy` format
- **Title** column: concise headline
- **Content** column: 2-4 sentence summary, no links, no URLs
- **Exclude all links/URLs** from every column
- Add a footer line: `**Source:** Exa MCP server (web_search_exa) | Retrieved on **dd/mm/yyyy**`

### Step 5 — Comprehensive & Unique Details Only

The user requires comprehensive, non-redundant output. Apply this deduplication and completeness filter before formatting:

- **Deduplicate aggressively:** Collapse results that repeat the same fact/headline across outlets (same Title normalized + >60% Highlights overlap counts as one). Keep the earliest/most complete representative and discard duplicates.
- **Unique-details-only:** In each Content cell, include only facts that are new for the requested `timespan`. Exclude recycled background that predates the window (e.g., older meetings, boilerplate bill history) unless it is needed in one sentence for context — and label older context as `Background:` in that single sentence.
- **Comprehensive:** Return at least 10 distinct rows when Exa returns ≥10 distinct hits; never return fewer than the distinct hits available. If hits collapse to <10 after dedup, run a second complementary Exa query with a paraphrased `topic` (e.g., add an alias/acronym) and merge unique results before formatting.
- **Signal vs noise:** Prefer rows with a concrete new development (vote, filing, quote, price move, release) over generic round-ups. If a result contains multiple unique facts, split its signal into separate rows only when dates/sources differ; otherwise synthesize into one comprehensive row.
- **No invented filler:** Never pad to 10 with speculation; if fewer than 10 unique items truly exist in the window, state `Only N unique developments found in this window` above the table.

## One-Shot Recipe

**Scenario:** User asks: "Give me news about {topic} for {timespan}"

1. Parse `topic` and `timespan` from the user's request.
2. Construct query: `"{topic} news latest headlines current events {timespan}"`.
3. Call `mcp_exa_web_search_exa(query=..., numResults=15)`. If results look thin or highly duplicative, run a second complementary query with a paraphrased topic alias/acronym and merge.
4. If MCP tools unavailable, use the direct Python MCP client fallback (Step 2).
5. Parse each result entry (Title, Published date, Highlights).
6. Apply Step 5 deduplication & unique-details filter (collapse duplicates, strip recycled background, keep ≥10 distinct rows when available; if <10 unique exist, note count above table).
7. Convert dates to `dd/mm/yyyy` format.
8. Build the markdown table (Date | Title | Content) — Content contains only new facts for the window (+ one `Background:` sentence max if needed).
9. Exclude all URLs and links.
10. Add source footer with retrieval date.

## Common Pitfalls

1. **Trying to JSON-parse the result text.** The `web_search_exa` tool returns plain text, not JSON. Parsing with `json.loads()` will throw `JSONDecodeError`. Treat the output as plain text and parse with string operations.

2. **Exa MCP tools not in session.** The Exa server uses HTTP Streamable transport which can be unstable (GET stream disconnects). If `mcp_exa_*` tools are not registered, always fall back to the direct Python MCP client connection script in Step 2.

3. **Forgetting to convert dates.** Raw results may show relative dates ("7 hrs ago", "2 days ago") or ISO format (`2026-06-17T05:35:02.000Z`). Always normalize to `dd/mm/yyyy` in the output table.

4. **Including URLs in the output.** The user explicitly asked to exclude links. Do not include any URLs in the Date, Title, or Content columns.

5. **Using keyword-only queries.** Exa works best with semantically rich, descriptive queries. "India news today latest headlines" works better than just "India news".

## Verification Checklist

- [ ] Both parameters (`topic`, `timespan`) extracted from user request
- [ ] Query constructed as semantically rich sentence
- [ ] Exa search executed (via MCP tools or direct Python fallback); second complementary query run if dedup left <10 rows
- [ ] Results parsed from plain text (not JSON) and deduplicated (Title+Highlights overlap collapsed)
- [ ] Unique-details-only enforced: recycled background stripped, only new facts for the window in Content
- [ ] At least 10 distinct rows returned when available, otherwise explicit `Only N unique developments...` notice shown
- [ ] Dates converted to `dd/mm/yyyy` format
- [ ] Output formatted as markdown table (Date | Title | Content)
- [ ] No links/URLs in any column
- [ ] Source footer added with retrieval date
