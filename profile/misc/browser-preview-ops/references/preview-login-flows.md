# Preview Pane Login Flows — YouTube & Outlook (2026-08-23)

## Context
User asked to "open youtube in sidepanel and bring the login button, I will login" then "open outlook.com". Session exercised `open_preview` + `drive_preview` + `annotate_preview` for user-visible auth.

## YouTube login via preview pane

### Discovery
- `open_preview({ url: "https://www.youtube.com" })` → title "(1) YouTube"
- `drive_preview(action='elements')` lists top bar:
  - `Account menu` / `btn-account-menu` / `#avatar-btn` — avatar circle at top-right, doubles as Sign in when logged out
  - No explicit "Sign in" button in snapshot when logged out; the menu button is the entry point.

### Interaction
```js
drive_preview({ action: 'click', ref: 'btn-account-menu' })
drive_preview({ action: 'elements' }) // re-snapshot; overlay may not appear in delta if Google auth interstitial loads
annotate_preview({ action: 'add', ref: 'btn-account-menu', label: 'Click to Sign in' })
```

### Fallback
If overlay doesn't render, navigate directly:
```
https://accounts.google.com/ServiceLogin?continue=https://www.youtube.com&service=youtube
```
Expect redirect to `https://www.youtube.com/?pli=1` after Google resolves — re-check `drive_preview(action='elements')` after redirect; re-annotate avatar if still logged out.

## Outlook login via preview pane

### Discovery
- `open_preview({ url: "https://outlook.live.com" })` first loads:
  `https://www.microsoft.com/en-us/microsoft-365/outlook/email-and-calendar-software-microsoft-outlook?deeplink=%2Fmail%2F&sdf=0&sessionId=...`
  Title "Microsoft Outlook Personal Email and Calendar | Microsoft 365"
  Snapshot shows marketing page, not inbox. Key link: `Sign in to Outlook` / `lnk-sign-in-to-outlook` / `#action-oc5b26`

### Interaction
```js
drive_preview({ action: 'click', ref: 'lnk-sign-in-to-outlook' }) // often no navigation in preview; stays on marketing URL
// fallback — go directly to auth:
open_preview({ url: "https://login.live.com" })
drive_preview({ action: 'elements' })
// → inp-enter-your-email-phone-o / #i0116 / "Enter your email, phone, or Skype."
// → btn-next / #idSIButton9 / "Next"
// → btn-no-account-create-one / #signup
annotate_preview({ action: 'add', ref: 'inp-enter-your-email-phone-o', label: 'Sign in here' })
```

### Pitfall
Clicking the marketing "Sign in" link in preview does not guarantee navigation (delta showed `same: 118`, url unchanged). Prefer direct `login.live.com` after one click attempt.

## General pattern for preview-pane logins

1. `open_preview({ url })` → `drive_preview(action='elements')` to inventory
2. Identify auth entry: YouTube `#avatar-btn`, Outlook `lnk-sign-in-to-outlook` or `#i0116`
3. `drive_preview(action='click', ref=...)` → re-snapshot via `drive_preview(action='elements')` (check `delta` for nav)
4. `annotate_preview(action='add', ref=..., label=...)` to highlight for user self-serve
5. If click doesn't navigate (marketing interstitials, bot redirects), `open_preview` directly to the IdP: `login.live.com` or `accounts.google.com/ServiceLogin?...`

## Verification
- After `open_preview`, confirm `drive_preview(action='elements')` title/url matches expectation; Outlook may show `microsoft.com/...` not `outlook.live.com/mail/` until authed.
- After annotate, `acted: "pinned ..."` confirms highlight is visible to user in side panel.
