# Session.info Warm-Start for Desktop Telemetry Widgets

## Problem
A Hermes desktop widget that only polls `session.usage` can stay blank on a fresh session until the first user prompt.

## Why it happens
- `host.state.activeSessionId` can be null or not yet useful at session load.
- `session.usage` is explicit-session RPC data and may not have a visible snapshot until the session is fully active.
- Hermes emits `session.info` events during `session.create`, `session.resume`, and `session.activate`.
- Those events already carry a `usage` snapshot when one exists.

## Pattern
1. Start with `host.state.activeSessionId`.
2. Listen to `host.onEvent('*', ...)`.
3. When `event.type === 'session.info'`, seed local state from:
   - `event.session_id`
   - `event.payload.stored_session_id` when present
   - `event.payload.usage` when present
4. Use that seeded state immediately for the widget.
5. Continue polling `host.request('session.usage', { session_id })` every few seconds.
6. Let the RPC data overwrite the event snapshot when fresher.

## Practical fallback order
```js
const resolvedSessionId = activeSessionId || eventSessionId || null
const usage = eventUsage || query.data || null
```

## UI guidance
- If there is no session yet, show a dimmed icon or `No active session`.
- If there is a session but no usage yet, show `Loading…` instead of a blank crash state.
- Never treat missing usage as a fatal plugin error.

## Verification
- Open a new session and confirm the widget shows a placeholder immediately.
- Confirm it fills in after the first `session.info` event, before the first turn.
- Confirm polling continues to refresh values after the session becomes active.
