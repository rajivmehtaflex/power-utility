---
name: zcode-dsh-plugin-creator
description: Create, build, install, and verify DeepSeek Harness (DSH) 0.2.x plugins — slash commands, model tools, skills, agent presets, and action cards — as installable dsh bundles. Covers the intake interview, Cordis package scaffolding (package.json dsh.bundle, cordis.patch.yml, TypeScript source), pinned builds, isolated installation into a dsh profile, and end-to-end runtime verification with a probe overlay. Use when the user asks to create, modify, install, or troubleshoot a DSH plugin, add a slash command or tool to dsh, write a Cordis plugin for dsh, or register a plugin bundle in a dsh profile. Triggers on dsh plugin, DSH plugin, dsh bundle, cordis.patch.yml, /command for dsh, dsh tool, dsh skill, agent preset, action card, dsh profile.
license: MIT
compatibility: Requires the dsh CLI 0.2.2-rc.1 on PATH, Node.js >=24.9.0, and pnpm. Verification boots dsh profiles inside a temporary DSH_HOME; model-turn checks additionally require dsh credentials.
metadata:
  author: rajivmehtaflex
  version: "0.1.0"
---

# zcode-dsh-plugin-creator

Author DeepSeek Harness (DSH) plugins end to end: interview the user, scaffold the
Cordis plugin package, build it, install it into a dsh profile, and verify
composition, schema, and runtime behavior. Qualified against DSH `0.2.2-rc.1`
and Node `>=24.9.0`. A plugin is an npm package that is also a **bundle** — a
layer of loader patch entries (`cordis.patch.yml`) applied over a profile.

Five plugin types are supported, each with its own reference recipe:

| Type | Registers | Model turn? | Recipe |
|---|---|---|---|
| Command (`/name`) | `ctx.commands` | No — renders directly in the UI | [references/command.md](references/command.md) |
| Tool | `ctx.tools` | Yes — called by the model | [references/tool.md](references/tool.md) |
| Skill | `ctx.skills` | Loaded via the `skill` tool | [references/skill-plugin.md](references/skill-plugin.md) |
| Agent preset | `ctx.agentPresets` | Declarative plugin stack, no code | [references/preset.md](references/preset.md) |
| Action card | `ctx.actionCards` | Proposed by the model, verified host-side | [references/action-card.md](references/action-card.md) |

Shared material: [references/bundle-anatomy.md](references/bundle-anatomy.md)
(package.json `dsh` field, patch semantics, files that must ship) and
[references/verify.md](references/verify.md) (preflight, isolated install,
compose/schema checks, runtime probe overlay, lifecycle exercises).

## Non-negotiables

1. **Intake is mandatory** for create, modify, install, and troubleshoot
   requests. Never skip Phase 0, even when the request looks complete — a
   complete request simply shortens it.
2. **Isolate first.** Install and verify inside a fresh temporary `DSH_HOME`.
   Install into the user's persistent profiles only when the user explicitly
   names the destination.
3. **Stop, don't improvise**, on version mismatches, dependency script approval
   prompts, or existing package/row conflicts. Report what is needed and the
   recovery command.
4. **Honest qualification.** A runtime check you could not exercise leaves that
   recipe **unqualified** — say so in the final report. Never claim a green
   check that was not run.
5. **Clean up on success and failure alike**: kill booted profiles, remove the
   temporary `DSH_HOME` and probe files. Keep probes outside the plugin package.

## Phase 0 — Intake (mandatory)

Resolve four things **before any operation that depends on them**: plugin
type, intended behavior, package identity, target profile.

- Use the `AskUserQuestion` tool where the host provides it. Put the
  recommended choice first, labeled `(Recommended)`. Where the host lacks the
  tool, ask in ordinary chat with the same options.
- At most **3 rounds**, at most 4 questions each. Ask only for details the
  request has not already fixed; a complete request may need zero questions.
  Never re-ask an answered point.

**Round 1 — kind and destination** (ask whichever is unresolved):

- Plugin type: command / tool / skill / preset / action card (one-line
  descriptions from the table above; command is the usual recommendation for a
  first plugin).
- Target profile: list real candidates with `ls $DSH_HOME/profiles/` (default
  `~/.dsh/profiles/`). Offer: a fresh temporary profile (recommended for new
  plugins), an existing profile by name, or a new profile from the `web`
  template. Action cards additionally require the web profile's optional
  services — say so when that type is chosen.
- Package identity: scope and name (e.g. `@local/my-plugin`). Default the row
  id to a short kebab id derived from the plugin's core noun.

**Round 2 — behavior, per type** (from the recipe's "Worked template" fields):

- Command: name (`/^[a-z][a-z0-9_-]*$/`, not a builtin), description, input
  hint, output shape, config options and defaults.
- Tool: name (`run_code` is reserved), parameters, output schema + render,
  concurrency/timeout needs.
- Skill: name (kebab-case), description, `whenToUse`, invocation flags, whether
  bundled assets ship with the package.
- Preset: id, display name, plugin rows and their config, ordering.
- Action card: action id, gating skill, verbs, details schema, what `act()`
  records.

**Round 3 — gaps only**: config defaults, version pin exceptions, persistent
install destination if the user wants one after all.

**Troubleshoot requests**: inspect before proposing anything. Read the plugin
package, the profile's `package.json` (`dsh.profile.bundles`) and
`cordis.patch.yml`, run the compose and schema checks from
[references/verify.md](references/verify.md), and read the plugin-manager
operation log under `<profile>/.plugin-manager/logs/` when an install failed.
Diagnose from evidence, then propose the minimal edit.

## Phase 1 — Scaffold

1. Read the type's recipe file **before writing code** — the registration API,
   shapes, and naming rules are exact, not illustrative.
2. Follow [references/bundle-anatomy.md](references/bundle-anatomy.md) for
   `package.json` (including the `dsh.bundle.patch` field, `exports` with the
   `./cordis.patch.yml` subpath, `files`, `engines`), `tsconfig.json`, and the
   `cordis.patch.yml` insert rows.
3. Pin `engines.dsh` and every `@deepseek-ai/*` dependency to the installed
   release (`dsh --version`); cordis stays `~4.1.0`.
4. The command recipe is the proven reference implementation. For the other
   types, derive from the installed release: the packages under the dsh
   install's `node_modules/@deepseek-ai/` ship both `.d.ts` types and real
   implementations to copy conventions from. Include any assets the plugin
   needs after installation (skill content files, `locale/en.json`, icon) in
   `files`.

## Phase 2 — Build

Preflight, then build with a lockfile:

```sh
dsh --version        # must equal the pinned engines.dsh, else STOP and report
node --version       # >=24.9.0
pnpm --version
```

Also preflight the output directory (empty or absent) and, for action cards,
that the target profile is web-based with the required optional services.

```sh
pnpm install         # a dependency script approval prompt => STOP and report
pnpm build
```

Audit the installable package before any install: `lib/index.js`,
`lib/index.d.ts`, `cordis.patch.yml`, and every declared asset are present and
listed in `files`; `exports` resolves for `.`, `./cordis.patch.yml`, and
`./package.json`. A missing export or patch file is a build failure.

## Phase 3 — Install (isolated first)

Use the proven sequence from
[references/verify.md §2](references/verify.md) — absolute package path, fresh
temporary `DSH_HOME`, profile suited to the plugin (web for action cards):

```sh
export DSH_HOME=/tmp/<plugin>-home && mkdir -p "$DSH_HOME"
timeout 90 dsh --profile <p> --from-default-profile web   # create + first boot
dsh plugin --profile <p> add file:/abs/path/to/plugin
```

`dsh plugin add` appends the package to `dsh.profile.bundles` itself. Then:

- **One activation, expected order**: `--dump-config` shows the row exactly
  once, appended after `@deepseek-ai/dsh-base` and the bundle layers.
- **Artifact matches the build**: the profile's installed copy has the same
  content as your build output (compare the built `lib/index.js` against the
  installed one). Re-run `dsh plugin add` after every rebuild — `file:`
  installs are copies (pnpm may hard-link on one filesystem; never rely on it).
- **Conflicts**: an existing dependency or patch row with the same id/name —
  STOP, report the partial change, and give the recovery command
  (`dsh plugin --profile <p> remove <pkg>` plus the bundles-entry edit if any).
- **Persistent install** only into a profile the user explicitly named, as the
  last step, after isolated verification passes.

## Phase 4 — Verify

Follow [references/verify.md](references/verify.md) in order:

1. Compose check — the expected row and config appear in `--dump-config`.
2. Schema baseline diff — `--dump-config-schema` with vs. without the plugin:
   the row appears with status `schema`; **zero new or changed diagnostics**.
   A fresh web profile carries 4 pre-existing `dsh-agent-preset` carrier
   errors; report them as unchanged baseline, never as failures of this plugin.
3. Runtime probe overlay — the probe plugin pattern (§4) drives the type's
   service directly: dispatch the command and assert its result; execute the
   tool through the tools service and assert structured output; list and load
   the skill from its intended scope; list presets and select one; for action
   cards, register the kind and its gating skill, exercise a verb through
   `ctx.actionCards.act`, and confirm the recorded decision. Use bounded waits;
   model-turn checks (headless) require credentials — without them, mark the
   model-path check unqualified and rely on the service-level check.

## Phase 5 — Lifecycle exercises

On a disposable profile, prove the loop users will actually run:

- **Rebuild with a visible behavior change** — edit, `pnpm build`, re-add,
  re-probe: the new behavior shows. A knob pinned by the patch row's
  `config:` overrides source defaults — change the row too, or the rebuild
  looks like a no-op.
- **Failed install** — break the package deliberately (e.g. missing build
  output), confirm a clear error and an unchanged profile, then restore.
- **Removal** — `dsh plugin --profile <p> remove <pkg>`; the dependency, the
  bundles entry, and the composed row are all gone.

## Worked invocation

User request: *"Create a dsh plugin named `@local/standup` that adds a
`/standup` command printing today's date and a configurable checklist
path."*

What the skill does with it: the intake interview only fills real gaps —
package identity and behavior are already fixed, so Round 1 collapses to one
question (target profile, temp recommended). It then scaffolds the bundle
(`@local/standup`, row id `command-standup`), pins `engines.dsh` to the
installed release, builds, installs into a fresh temporary `DSH_HOME`,
verifies compose/schema/runtime (dispatching `/standup` and asserting the
date line), and reports. The user's persistent profiles are touched only if
they name one afterward.

## Reporting

End with a table: package identity and path, profile used (temp or named),
compose/schema/runtime results per check, diagnostics (new vs. baseline),
lifecycle outcomes, cleanup status — plus the iteration recipe
(edit → `pnpm build` → `dsh plugin add` → restart) and an explicit
**unqualified** list for anything not exercised.
