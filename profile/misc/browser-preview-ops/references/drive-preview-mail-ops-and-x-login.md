# Drive-Preview Mail Ops & X Login — 2026-08-23 Session

Second session exercising `drive_preview` beyond login flows: Outlook mail move to folder + X.com login.

## Outlook: Move mail to folder (DL)

### Precondition
- Inbox already loaded via `open_preview({ url: "https://outlook.live.com/mail/" })`
- `drive_preview(action='elements')` shows inbox list with:
  - `btn-move-to` / `#540` — Move to toolbar button
  - `chk-select-a-conversation` / `opt-*` rows — checkbox indicates selection
  - `btn-by-date`, `btn-filter` etc.

**Selection matters:** the conversation with `value: "checked"` is the one `Move to` will act on. In this session it was `Daily Dose of DS — How Semantic Code Navigation...` (`chk-select-a-conversation-1` checked). Verify checked state before moving, or ask user which mail they mean by "this mail".

### Interaction sequence

```js
// 1. Ensure fresh snapshot (handles stale-ref after prior nav)
drive_preview({ action: 'elements' })

// 2. Open Move menu
drive_preview({ action: 'click', ref: 'btn-move-to' })
// → delta adds: el-move-to / #Ribbon-540Dropdown, srch-search-for-a-folder / #689_moveToMenu_SearchBox,
//   mi-dl, mi-html5, mi-online-transaction, mi-cloud, mi-mantra, inp-create-new-folder

// Stale-ref guard: if you get
// "The page navigated since the last snapshot, so btn-move-to no longer points anywhere. Call elements again."
// → re-call drive_preview(action='elements') and retry.

// 3. Click target folder
drive_preview({ action: 'click', ref: 'mi-dl' })
// → delta confirms: el-moved-to-dl / "Moved to DL" + btn-undo
//   same: 58, removed: el-move-to / mi-dl / ...
```

### Verification
- Success = delta contains `el-moved-to-dl` (`label: "Moved to DL"`, `role: "listitem"`) + `btn-undo`
- If delta lacks toast, the move failed — re-check selection or folder exists.
- After move, inbox re-renders; re-call `elements` to see updated list (moved row disappears).

### Pitfalls
- **Empty elements on first load:** `outlook.live.com/mail/` often returns `[]` (`No interactive elements found — page may still be loading`) on first snapshot. `sleep 3` then re-call `elements` until toolbar appears (Rajiv Mehta account button `btn-rajiv-mehta` is a good readiness anchor).
- **Marketing interstitial:** unauthenticated `outlook.live.com` redirects to `microsoft.com/...deeplink...OUTLOOK...` marketing page (title "Microsoft Outlook Personal Email..."). That snapshot has `lnk-sign-in-to-outlook` but not `btn-move-to`. Resolve via `open_preview({ url: "https://login.live.com" })` first, then back to `/mail/`.

---

## X.com (x.com) login via preview

### Direct login URL
Prefer the flow URL over `/login` (which bounces to onboarding):
```
https://x.com/i/flow/login
→ redirects to https://x.com/i/jf/onboarding/web?mode=login
```

Avoid `https://x.com/login` → lands on `.../onboarding/web#/s/signup_phone/r-...` with country phone selector (`inp-search-countries`, `opt-india-91` etc.) — signup, not login.

### Login snapshot (working)
```js
open_preview({ url: "https://x.com/i/flow/login" })
drive_preview({ action: 'elements' })
// → el-see-what-s-happeningsee / group
// → btn-continue-with-phone
// → btn-continue-with-appleconti / "Continue with Apple"
// → inp-username-or-email / #jf-input-username_or_email / "username_or_email"
// → lnk-terms-of-service, lnk-privacy-policy, lnk-cookie-use
```

Sometimes first snapshot only shows footer (`lnk-about`, `lnk-grok` etc.) — interstitial loading. Wait 3s and re-call `elements` until `inp-username-or-email` appears.

### Interaction
```js
annotate_preview({ action: 'add', ref: 'inp-username-or-email', label: 'Enter Email / Username here' })
drive_preview({ action: 'type', ref: 'inp-username-or-email', text: 'user@example.com', submit: false })
// User completes password/2FA self-serve in preview; no agent credential handling.
```

### General reuse
- Outlook move pattern generalizes to any Outlook folder: `mi-<folder-id>` items under `el-move-to` menu. Use `srch-search-for-a-folder` to filter long folder lists.
- X login pattern generalizes to other X entry points: always target `inp-username-or-email` as readiness probe, not footer links.

## Relation to existing references
- Extends `references/preview-login-flows.md` (YouTube + Outlook login) with X.com and with post-login mail operations.
- Complements `references/google-sorry-block.md` — preview-pane logins bypass automation `/sorry/index` entirely.
- Skill pitfall #4 in SKILL.md still claims preview is not drivable — this file documents the counter-evidence and should drive a SKILL.md patch to correct it.
