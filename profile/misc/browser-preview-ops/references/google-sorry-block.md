# Google `/sorry/index` Block — Reproduction (2026-08-06 Junagadh session)

## Context
User: "Can you check with browser and open with google.com" → "I'm talking about open browser" → "and search for Junagadh city news" → "What page are you able to see"

## Reproduction

### Step 1 — Automation google.com homepage = OK
```
browser_navigate({ url: "https://www.google.com" })
→ { success: true, title: "Google", element_count: 26 }
→ snapshot: generic / search / combobox "Search" / image "Google" / etc.
→ browser_vision: dark mode, "India" locale, no CAPTCHA, search bar ready
```

### Step 2 — Automation google.com/search = BLOCKED
```
browser_navigate({ url: "https://www.google.com/search?q=Junagadh+city+news" })
→ { success: true,
    url: "https://www.google.com/sorry/index?continue=https://www.google.com/search%3Fq%3DJunagadh%2Bcity%2Bnews&sei=snV0...",
    title: "https://www.google.com/search?q=Junagadh+city+news...",
    stealth_warning: "Running WITHOUT residential proxies. Bot detection may be more aggressive. Consider upgrading Browserbase plan for proxy support.",
    stealth_features: ["local"],
    snapshot: "- link \"Why did this happen?\" / StaticText \"IP address: 2402:3a80:87c:639c:...\" / Time: 2026-08-06T11:53:23Z" }
```

Root cause: Browserbase `stealth_features: ["local"]` only — no residential proxies → Google flags as bot on `/search` (homepage is unprotected).

### Step 3 — Fallback that WORKED: Exa dual-query merge

```js
tool_call("mcp__exa__web_search_exa", { query: "Junagadh city news Gujarat latest updates", numResults: 10 })
// → 10 results: scholarship scam (Gujarat First 2026-08-05), lion rescue (Hindu/TOI/Mirror Aug 01), DivyaBhaskar digest, LC-III ports, rain alert, municipal commissioners, Girnar noise, Rajkot hit-and-run, Adulterated milk

tool_call("mcp__exa__web_search_exa", { query: "Junagadh Gujarat news headlines latest August 2026", numResults: 10 })
// → 10 results (overlap on lion rescue) + NDTV pilgrim bus (2 killed), flood camps 6868, Parbardham fair, Sakkarbaug zoo, etc.

// Merge → dedupe → 12 unique items, sufficient for ≥10-item get-info contract
```

### Step 4 — Dual verification for "what page are you able to see?"

```
read_preview()       // preview pane — what user sees
→ { kind: "url", title: "Latest Junagadh News (જુનાગઢ સમાચાર)...", url: "https://www.divyabhaskar.co.in/local/gujarat/junagadh/", text: "જુનાગઢ ન્યૂઝ / શેરિયાખાણમાં કચરો...", total_chars: 4136 }

browser_snapshot()   // automation browser — what agent sees
→ { success: true, snapshot: "(empty page)" }  // stale after preview nav

browser_navigate({ url: "https://www.divyabhaskar.co.in/local/gujarat/junagadh/" })
→ { success: true, title: "Latest Junagadh News...", element_count: 347, snapshot: "heading જુનાગઢ ન્યૂઝ / listitem SC-ST scholarship ..." }
→ browser_vision: dark mode, breadcrumb Gujarati News/Local/Gujarat/Junagadh, center feed with 1:30/1:53 video thumbnails, left nav, no CAPTCHA
```

Lesson: after `open_preview` nav, automation `browser_snapshot` goes stale (empty). Re-navigate automation to same URL before claiming state.

## Payload to recognise

Signature of this class of failure:
- `url` contains `/sorry/index?continue=`
- `stealth_warning` contains `WITHOUT residential proxies`
- `snapshot` contains `Why did this happen?` + `IP address:`

When seen: do NOT retry `browser_navigate` to Google `/search`. Switch to Exa immediately.
