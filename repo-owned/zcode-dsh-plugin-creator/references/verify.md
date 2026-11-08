# Verify: preflight, compose, schema, runtime probe, lifecycle

Never claim a DSH plugin works from static reading alone. Run this ladder —
every step uses a throwaway profile under a temp `DSH_HOME`, so real user
profiles stay untouched. Proven against DSH 0.2.2-rc.1, Node >= 24.9.0,
pnpm 12.x. Related: `./bundle-anatomy.md`, `../SKILL.md`.

## 1. Preflight

```sh
dsh --version        # must equal the pinned engines.dsh (0.2.2-rc.1)
node --version       # >= 24.9.0 (the release's own engine floor)
pnpm --version
ls ~/.dsh/profiles/  # or $DSH_HOME/profiles — which profiles exist
```

Also confirm the output directory is empty/absent and `lib/` was built.

## 2. Isolated install (proven sequence)

```sh
export DSH_HOME=/tmp/dsh-verify-home && mkdir -p "$DSH_HOME"   # fresh; real home untouched
timeout 90 dsh --profile verify --from-default-profile web   # copy template, then boot; timeout kills it (exit 143 expected)
dsh plugin --profile verify add file:/abs/path/to/your-plugin
```

- `--from-default-profile web` CREATES the profile from the shipped template
  and then BOOTS the web app — always wrap it in `timeout`. Fresh bundles:
  `["@deepseek-ai/dsh-base", "@deepseek-ai/dsh-web-app"]`; `cordis.yml` is
  an empty list (`[]`).
- `dsh plugin add file:` forwards verbatim to pnpm in the profile directory;
  pnpm store and peer-dependency warnings are harmless here. Re-adding the
  same package name replaces the dependency without duplicating the entry.
- On 0.2.2-rc.1, `dsh plugin add` ALSO appends the package name to
  `dsh.profile.bundles` in the profile's `package.json` (at the end, after
  `@deepseek-ai/dsh-base`); verify by cat-ing that file, and add the name
  yourself (AFTER `@deepseek-ai/dsh-base`) if the entry is missing.

## 3. Compose check, then schema check (baseline diff)

```sh
dsh --profile verify --dump-config | grep -A4 <row-id>   # expect your row under "# == <package>"
```

Schema check with diagnostics, against a baseline WITHOUT the plugin
(captured BEFORE `dsh plugin add`, or after `remove`):

```sh
dsh --profile verify --dump-config-schema > /tmp/schema-with.json 2> /tmp/schema-with.err
dsh --profile verify --dump-config-schema > /tmp/schema-without.json 2> /tmp/schema-without.err
diff <(sort /tmp/schema-without.err) <(sort /tmp/schema-with.err)   # must be empty
```

- The schema dump is a large JSON Schema on stdout; ALL diagnostics go to
  stderr; the command exits 1 whenever any error exists — even pre-existing.
- Your row must appear in the schema's `x-cordis.entries` array with
  `"status": "schema"` and a `configRef` to its config definition.
- KNOWN BASELINE: every fresh web-derived profile emits several
  `unrecognized Loader tree carrier` errors on `@deepseek-ai/dsh-agent-preset`
  rows (4 on stock 0.2.2-rc.1 web) — they exist WITHOUT your plugin. Pass
  criteria: expected row present, zero NEW diagnostics.

## 4. Runtime probe overlay

The only reliable runtime check: boot with an extra `--patch` overlay that
inserts a probe plugin. Keep the probe OUTSIDE the plugin package (temp
dir) — it ships to no one. Relative `name` in probe.patch.yml anchors BESIDE
the patch file:

```yaml
- insert:
    - id: probe
      name: ./probe.mjs
```

probe.mjs — the complete working template:

```js
import fs from "node:fs";
const resultPath = "/tmp/probe-result.json";
const trace = (m) => fs.appendFileSync("/tmp/probe-trace.log", m + "\n");
const probe = (ctx) => {
  setTimeout(async () => {
    try {
      const out = {};
      // ADAPT THIS BLOCK PER PLUGIN TYPE — see the table below.
      const def = ctx.commands.find(undefined, "hello");
      out.registered = ctx.commands.list(undefined).some((c) => c.name === "hello");
      if (def) out.handlerResult = await def.handler({ rawInput: "Probe" });
      fs.writeFileSync(resultPath, JSON.stringify(out, null, 2));
      process.exit(0);
    } catch (err) {
      trace("probe failed: " + err);
      fs.writeFileSync(resultPath, JSON.stringify({ error: String(err) }, null, 2));
      process.exit(3);
    }
  }, 2000);
};
probe.inject = ["commands"];
export default probe;
```

Boot and read the result:

```sh
timeout 40 dsh --profile verify --patch /tmp/probe.patch.yml   # then read /tmp/probe-result.json
```

Gotchas learned the hard way: the `ready` event NEVER fires on a serving web
app — do not wait for it; use `setTimeout(..., 2000)` after plugin
invocation as the boot barrier. Write a trace file at every step so a silent
hang shows how far boot got, and ALWAYS end with `process.exit(code)` (0
pass, 3 fail) — the probe must stop the server; `timeout` is only the
backstop.

## 5. Per-type runtime checks (command/tool/skill/preset verified in-probe)

| Type | Registry introspection | Direct execution |
|---|---|---|
| command | `ctx.commands.list(undefined)`, `find(undefined, name)` | `await def.handler({ rawInput: "..." })` |
| tool | `ctx.tools.definitions(undefined)`, `get(name, undefined)`, `schemas(undefined)` | `await ctx.tools.execute({ calls: [{ id: "probe-1", type: "tool-call", name, arguments: JSON.stringify({...args}) }], signal: AbortSignal.timeout(10000) })` — `arguments` is the raw JSON string; block type is `"tool-call"` (hyphen). Settled `results[0]` is `{callId, result:{isError, content, value}}` |
| skill | `await ctx.skills.list({})`; load with `await ctx.skills.get(name)`; subscribe `skills/change` for refresh | headless turn: `dsh --profile verify headless "use skill X"` (needs credentials — see honest reporting) |
| preset | `await ctx.agentPresets.list()` (stock profile: `standard`, `ptc`, `minimal`, `cordis`; plus `ctx.agentPresets.defaultId`) and `await ctx.agentPresets.resolve(id)` | selecting a preset for a session is a UI/agent action — assert presence and error-free resolve |
| action card | the web template ships NO `action-cards` rows — first enable the service (see below), then prove kind registration via the duplicate-register throw and the gating skill via `ctx.skills.list()` | `ctx.actionCards.act(agent, callId, verb, payload)` / `record(agent, decision)` need a live agent with a logged card — see honest reporting |

Verified notes: `list(undefined)` reads the GLOBAL view (correct for
globally registering plugins). The global tools view at boot is SMALL (stock
web: only `working_directory`; many built-ins register per-agent), but a
third-party global tool DOES appear in `definitions(undefined)`. Inject only
what the probe touches, so boot fails loudly if a service is missing.

Action-card service enablement (proven on 0.2.2-rc.1): the stock web template
mounts neither half of the action-cards stack. Install both as plain deps and
wire their rows through the profile's own patch layer:

```sh
dsh plugin --profile verify add @deepseek-ai/dsh-action-cards@<pinned>
dsh plugin --profile verify add @deepseek-ai/dsh-client-ui-action-cards@<pinned>
# both print "declares no dsh.bundle — installed as a plain dependency" — expected
```

Then REPLACE the profile's `cordis.patch.yml` content (it starts as a bare
`[]`; appending after it is a YAML second-document error — rewrite the file):

```yaml
- insert:
    - id: action-cards
      name: '@deepseek-ai/dsh-action-cards'
    - id: client-ui-action-cards
      name: '@deepseek-ai/dsh-client-ui-action-cards'
```

Two benign diagnostic additions to expect and to prove benign by probe: one
more `unrecognized Loader tree carrier` error for a preset-shaped row you add
(same class as the baseline four), and `/N Config is not a native Schemastery
schema` for the official `action-cards` row (its Config is zod). Both
activate and serve despite the diagnostics; the probe result is the verdict.

## 6. Lifecycle exercises

(a) Rebuild + reinstall with a VISIBLE behavior change:

```sh
pnpm build                                            # after editing src (changed output string)
dsh plugin --profile verify add file:/abs/path/to/your-plugin   # re-add picks up the rebuild
```

Then re-run the probe: the new string must appear in probe-result.json.
`file:` installs are content-frozen into the profile's pnpm store. On the
same filesystem pnpm HARD-LINKS package files, so an in-place `tsc` rebuild
may propagate without re-add (observed) — do NOT rely on it: when pnpm warns
it cannot hard-link from its store, the copy is frozen and only re-add
updates it. Always re-add, then re-probe.

Config-source trap (verified): a behavior knob pinned by your patch row's
`config:` OVERRIDES the schema default at composition. Editing only the
source default and rebuilding changes nothing at runtime — change the row's
`config` in `cordis.patch.yml` too (or drop the override), re-add, re-probe.
A "visible change" exercise that stays invisible almost always hit this.

(b) Failed install — feed a broken package (invalid `package.json`, or
missing `files`/build output). Verified: pnpm fails with a clear parse error,
dsh prints `plugin command failed; diagnostics: <profile>/.plugin-manager/logs/operation-*/pnpm.log`,
and the profile's `package.json` (deps and bundles) is unchanged.

(c) Removal:

```sh
dsh plugin --profile verify remove @your-scope/your-plugin
dsh --profile verify --dump-config | grep -c <row-id>   # expect 0
```

Verified on 0.2.2-rc.1: `remove` drops the dependency AND the
`dsh.profile.bundles` entry; confirm both, and the row's absence above.

## 7. Cleanup

```sh
pgrep -af dsh     # probe self-exits; kill only what YOU started — never the user's own instances; check the served port
rm -rf /tmp/dsh-verify-home /tmp/probe.mjs /tmp/probe.patch.yml /tmp/probe-result.json /tmp/probe-trace.log
unset DSH_HOME
```

## 8. Honest reporting

A runtime check that was not exercised leaves the recipe UNQUALIFIED. Report
exactly which checks ran (compose, schema-diff, probe, lifecycle) and which
did not. Typical unverified leftovers: headless model turns — the headless
route requires `DEEPSEEK_API_KEY` (exported or in the credentials store);
web-profile account credentials do NOT satisfy it, so model-path checks
(tool invoked by the model, preset selection in a session, a card proposed
through `propose_action`) stay unqualified without that key —
`skills/change` timing, and action-card `act`/`record` (need a live agent
and a logged card; service-level proofs are the duplicate-register throw for
the kind and `ctx.skills.list()` for the gating skill).
Say so; never mark a plugin "verified" on static evidence.
