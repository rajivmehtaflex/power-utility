---
name: pi-extension-authoring
description: Use when authoring TypeScript Pi extensions.
license: MIT
metadata:
  author: Hermes Agent
  hermes_related_skills: pi-operator, pi-extension-explorer
  hermes_tags: Pi, extension, TypeScript, ExtensionAPI, tools, prompts
  platforms: linux, macos
  version: 0.1.0
---

# Pi Extension Authoring

Author and edit Pi coding-agent extension packages (`packages/<name>/` layout, entry
`src/index.ts` with `export default function (pi: ExtensionAPI)`). Covers tool
registration, slash-command prompts, `ctx.ui` dialog primitives, dashboard widgets,
and the port-a-pattern workflow for lifting features from reference repos into a
local package without importing their dependencies.

## When to Use

- Adding or changing a tool (`pi.registerTool`), slash prompt (`prompts/*.md`), custom
  command (`pi.registerCommand`), or widget in a Pi extension package.
- Building a model-invoked interactive dialog (ask-the-user tools) on `ctx.ui` primitives.
- Studying another Pi extension repo to port a pattern into the local package.
- Wiring new modules into a package's `src/index.ts` (`register*(pi, state)` functions).

## Codebase conventions (verified in pi-local-dev packages)

- **Zero runtime npm deps.** JSON-Schema tool args use the hand-rolled TypeBox-compatible
  `Type` builder in `src/types.ts` — never add `@sinclair/typebox` for this.
- **Tool result envelope:** `{ content: [{ type: "text", text }] }` (see plan-mode.ts).
- **Types are re-exported locally:** import `ExtensionAPI`, `ExtensionContext`,
  `WorkflowState` from `./types.js`, not from `@earendil-works/pi` directly.
- **`ctx.ui` primitives:** `confirm(title, msg) → Promise<boolean>`,
  `select(title, options[]) → Promise<string | undefined>`,
  `input(title, placeholder?) → Promise<string | undefined>`. A resolved `undefined`
  from select/input means the user dismissed the dialog — treat as cancel, never as an
  answer. Gate all UI tools on `ctx.hasUI` (headless/`--no-session` runs have no UI).
- **Slash prompts auto-bind:** every `prompts/*.md` becomes `/<filename>` — a name
  shared with `registerCommand(...)` silently collides (two behaviors, one slash string).
- **Module shape:** each feature module exports `registerX(pi: ExtensionAPI, state)`;
  `src/index.ts` calls them in order and owns the shared mutable state object.

## Port-a-pattern workflow (from a reference repo)

1. `git clone --depth 1 <repo> /tmp/<repo>` — read-only study, never run its scripts.
2. Locate the package (`packages/<name>/`), read its entry `*.ts` `registerTool` block,
   then find the **simple path** — repos often ship a huge TUI overlay plus a small
   fallback (e.g. rpiv-ask-user-question: 9.8k-LOC overlay vs 166-line
   `rpc-fallback.ts` walker on `ctx.ui.select/input`). Port the fallback-shaped core.
3. Re-express in local conventions (local `Type` builder, local result envelope,
   local imports). Keep logic pure where possible: validate params → pure dialog
   walker (inject `ui` for testability) → envelope.
4. Add `*.test.ts` under `node:test` with a fake `ui` object — this also fixes the
   zero-tests false-green (see Pitfalls).

## Pitfalls

- `npm test` (`node --test`) passes with **0 test files** — green proves nothing until
  at least one `*.test.ts` exists.
- Stale `dist/`: run `npm run build` after editing `src/*.ts` before loading in Pi.
- `.pi/settings.json` package paths resolve relative to `.pi/` — use
  `../packages/<name>`.
- Widgets/dialogs render only in a live TTY: verify via tmux (`tmux new-session -d -s
  piui -x 150 -y 45 "pi"` then `tmux capture-pane -p`), not headless `-p` runs.
- Authoring question tools: reject reserved option labels (`"Other"`, `"Type
  something."`) at validation time — the free-text row is appended by the runtime.
- When a tool's dialog can't render, tell the model the user **never saw the
  questions** and to re-ask in plain chat — never frame it as a user decline.
- Terminal hardline block on "oversized/unparseable inline command payloads": complex
  `sed -n "$(grep ...)"` one-liners can trip it — split into `read_file`/`search_files`
  tool calls instead of shell text-processing pipelines.

## Verification

1. `npm run build` exit 0 (tsc).
2. `npm test` — real test count > 0, all passing.
3. Load and exercise: `pi -e ./packages/<name>/src/index.ts` (or via
   `.pi/settings.json`), confirm the tool in `pi list`, drive it in tmux for anything
   visual.

## References

- `references/rpiv-ask-user-question.md` — architecture study of the
  `juicesharp/rpiv-mono` ask-user-question extension: schema constraints, dialog
  walker algorithm, answer union, no-UI fallback messaging.
