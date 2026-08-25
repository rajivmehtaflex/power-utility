---
name: browser-preview-ops
description: Use when opening or verifying any web page in Hermes.
license: MIT
metadata:
  author: Hermes Agent
  hermes_related_skills: hermes-web-research, get-info
  hermes_tags: browser, preview, open-preview, browserbase, google, verification
  version: 1.0.0
---

# Browser & Preview Ops — Automation vs Visible Pane

## Overview

Hermes has **two distinct browsers** that users constantly confuse:

| Surface | Tools | Who sees it | When it fails |
|---------|-------|-------------|---------------|
| **Automation browser** (Browserbase remote) | `browser_navigate`, `browser_snapshot`, `browser_vision`, `browser_click` | Agent only — invisible to user | Google `/sorry/index` bot-check without residential proxies, CAPTCHAs |
| **Preview pane** (beside chat) | `open_preview`, `read_preview` | **User sees it** — split view on right | No bot-check — renders like normal user session |

Misrouting = user says "I don't see anything" even though agent screenshot shows success.

## When to Use

- User says **"open browser"**, **"open google.com"**, **"show me X in browser"** → they mean the **preview pane** (`open_preview`). Always use `open_preview` for visibility.
- User says **"search for X"** → do **both**: `open_preview` for user + `mcp__exa__web_search_exa` (or automation browser) for data. Preview alone has no structured search API.
- User asks **"what page are you able to see?"** → check **both**: `read_preview` (what user sees) + `browser_snapshot`/`browser_vision` (what automation sees). Report URLs separately.

## Workflow

### 1 — Open visibly first

```js
open_preview({ url: "https://www.google.com", label: "Google" })
// or for search:
open_preview({ url: "https://www.google.com/search?q=Junagadh+city+news", label: "Junagadh News" })
read_preview() // confirms what landed
```

### 2 — Fetch data via Exa (not just automation Google)

Automation Google frequently hits:
```
https://www.google.com/sorry/index?continue=https://www.google.com/search?q=...
IP: 2402:3a80:... | "Our systems have detected unusual traffic"
```
This is expected **without residential proxies** (`stealth_warning: Running WITHOUT residential proxies`). Do NOT retry Google in automation — switch to:

```js
tool_call("mcp__exa__web_search_exa", { query: "Junagadh city news Gujarat latest updates", numResults: 10 })
tool_call("mcp__exa__web_search_exa", { query: "Junagadh Gujarat news headlines latest August 2026", numResults: 10 })
```

Merge 2×10 results, dedupe, return ≥10 items (see get-info).

### 3 — Verify duality

Before answering "what do you see?":

```
read_preview()          // preview pane text + title + url
browser_snapshot()      // automation DOM
browser_vision(question="What page is currently visible?") // screenshot analysis
```

Report both tables. If automation shows `/sorry/index` but preview shows content, explain the split and tell user they can type directly in preview.

### 4 — Help user self-serve in preview

If automation is blocked, instruct: *"You can type 'Junagadh city news' directly in the Google search bar in the Preview Pane on the right and hit Enter — that path bypasses the automation bot-check."*

## Pitfalls

## Pitfalls

1. Open browser != browser_navigate. browser_navigate is headless/remote; user sees nothing. The preview pane is open_preview. First utterance of open browser must call open_preview.
2. Google automation without proxies = /sorry/index. stealth_features local alone triggers bot detection on google.com/search. Treat as expected, not transient. Fall back to Exa immediately; don't retry same URL.
3. Only checking one surface. Answering what do you see? from automation alone lies to user. Always pair read_preview + browser_snapshot/browser_vision.
4. Assuming preview supports click automation. Preview is not drivable via browser_click — only open_preview/read_preview. For clicks/typing, use automation browser; for visibility, use preview. When both needed, keep them in sync.
5. News queries need >=10 items. User expects comprehensive tables. Run 2 complementary queries and merge.
6. Browser backend confusion. browser.backend controls automation driver, not preview pane. off = built-in tools; unset = Browser Use default; browser-use = force Browser Use. Preview visibility is independent of backend.

## Browser Backend Capabilities
User prefers capability lists/tables for Hermes profile explanations.

| browser.backend | Driver | Automation task class |
|---|---|---|
| "" / unset | Browser Use mode default | High-level autonomous browsing via single browser_exec tool; uses Browser Use CLI + browser source. Auto-fallback to built-in if Browser Use not runnable |
| browser-use | Force Browser Use | Same as above, forced |
| off | Built-in browser tools | Low-level actions: browser_navigate, browser_click, browser_type, browser_snapshot, browser_scroll, browser_console, browser_vision, browser_get_images |

Built-in tools enable:
- Navigation & page load: browser_navigate, browser_back
- Inspection: browser_snapshot, browser_console
- Interaction: browser_click, browser_type, browser_press, browser_scroll
- Visual QA: browser_vision
- Assets: browser_get_images
- Session control via browser.* config: inactivity_timeout, command_timeout, headed/headless, record_sessions

## Verification Checklist

- [ ] User-visible page opened via `open_preview` (not just `browser_navigate`)
- [ ] `read_preview` confirms title/url/text the user actually sees
- [ ] If search needed, Exa called (≥2 queries) and ≥10 unique results merged
- [ ] Automation Google `/sorry/index` handled via fallback, not retried
- [ ] Final answer reports both surfaces separately when asked "what do you see?"

## References

- `references/google-sorry-block.md` — full `/sorry/index` reproduction, stealth_warning payload, and dual-query merge pattern from Junagadh session (2026-08-06).
