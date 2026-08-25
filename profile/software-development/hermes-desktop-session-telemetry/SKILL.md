---
name: hermes-desktop-session-telemetry
description: Use for session telemetry widgets. Seed from session.info.
metadata:
  hermes_category: software-development
  hermes_related_skills: hermes-desktop-plugins, hermes-token-usage
  hermes_tags: hermes, desktop, plugins, statusbar, telemetry, sessions, ui
  platforms: linux, macos, windows
  version: 1.0.0
---

# Hermes Desktop Session Telemetry

Use this skill when a Hermes desktop plugin or widget needs to display live session data such as token usage, timers, context fill, model, or running state.

This skill complements `hermes-desktop-plugins`. Use that skill for generic plugin scaffolding and this one for widgets whose main job is to surface session telemetry quickly and accurately.

## Core pattern

A fresh desktop session can exist before the first user message. If you only poll `session.usage`, the widget may render as empty until the first turn. The fix is to combine:

1. `host.state.activeSessionId` for the primary session key.
2. `host.onEvent('*', ...)` to catch `session.info` events.
3. `session.info` payload data as the warm-start snapshot.
4. `host.request('session.usage', { session_id })` as the polling source of truth.

## Recommended implementation

1. Track a `resolvedSessionId`.
   - Prefer `host.state.activeSessionId`.
   - Fall back to the last `session.info` event's session id.

2. Keep a lightweight event-backed usage snapshot.
   - On `session.info`, read `payload.usage` if present.
   - Prefer `payload.stored_session_id` when available; otherwise use `event.session_id`.

3. Poll the usage RPC.
   - Query `session.usage` for the resolved session id.
   - Use a few-second interval; do not poll faster than necessary.

4. Render a safe placeholder.
   - Before any session is known, show a dimmed icon or `No active session`.
   - If the widget has a session id but no usage yet, show a loading or blank state rather than throwing.

5. Merge event data and RPC data carefully.
   - Use the event snapshot immediately when it exists.
   - Let the RPC overwrite it when fresher data arrives.
   - Avoid duplicate listeners on hot reload by cleaning up in the effect teardown.

## Pitfalls

- Do not assume `activeSessionId` alone is enough on initial load.
- Do not wait for the first conversation turn to show telemetry.
- Do not treat missing usage as a hard error; it is often just an unopened or idle session.
- `session.info` can arrive as a global broadcast; if the event carries no explicit session id, use the payload's stored session id when present.
- Keep the widget stable on reload: one listener, one query, no blank crash state.

## Verification

- Open a fresh session and confirm the widget shows a placeholder immediately.
- After `session.info` arrives, confirm the widget updates before the first user prompt.
- Send the first message and confirm the polling source remains in sync.
- Reload the plugin and verify the event listener is not duplicated.

## Support files

- `references/session-info-warm-start.md` — concise recipe for seeding live telemetry widgets from `session.info`.
