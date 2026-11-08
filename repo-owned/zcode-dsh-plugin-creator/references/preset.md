# Agent presets (declarative plugin stacks)

A preset is NOT code: it is a declarative entry list (child Cordis plugins plus config) that the `@deepseek-ai/dsh-agent-preset` plugin submits to the `agentPresets` registry, which mounts each declaration as its own scoped plugin tree. Presets surface in the web UI's agent/preset picker through `@deepseek-ai/dsh-agent-preset-registry` plus `@deepseek-ai/dsh-client-ui-agent-preset`; a session selects one and its agent runs that standing composition. Pinned: DSH 0.2.2-rc.1, Node >=24.9.0, `@deepseek-ai/schemastery` ~3.19.0 (config), `@deepseek-ai/cordis` ~4.1.0 (peer).

## Exact shape (quoted from `dsh-agent-preset-registry/lib/types/definition.d.ts`)

```ts
interface PresetDefinition {
  readonly id: string;
  readonly name?: string;
  readonly description?: string;
  readonly order?: number;
  readonly plugins: readonly (Omit<EntryOptions, "id" | "disabled"> & {
    id?: string;
    disabled?: EntryOptions["disabled"] | JsExpr;
  })[];
}
```

`EntryOptions` (`@deepseek-ai/cordis-plugin-loader`) is `{ id, name, config?, group?, disabled?, inject? }` — so each row keeps `name` (the plugin package specifier) and `config`, and may carry `id`/`disabled` (boolean, null, or a `!!js` expression). The `dsh-agent-preset` plugin's own schemastery config validates exactly these fields: `id` required, `plugins` array required, `name`/`description`/`order` optional.

## Authoring modes

**(a) Supported path — a bundle patch row.** A new preset or an override of a shipped one is a Cordis bundle patch: insert a `@deepseek-ai/dsh-agent-preset` row whose `config` is the `PresetDefinition`. The registry neither scans directories nor accepts preset paths; definitions are ordinary plugin rows. Author the patch in `cordis.patch.yml` (a top-level YAML array of loader patch entries).

**(b) Programmatic — `ctx.agentPresets.register(definition)`.** The registry class exposes a public `register(definition: PresetDefinition): Promise<() => Promise<void>>` (eager activation; the disposer retires the revision). Use it only when a host composes presets in code; conversation-authored presets go through (a).

```yaml
# cordis.patch.yml — registry row (default is required) + preset declaration
- id: agent-preset-registry
  name: "@deepseek-ai/dsh-agent-preset-registry"
  config:
    default: reviewer
- insert:
    - id: preset-reviewer
      name: "@deepseek-ai/dsh-agent-preset"
      config:
        id: reviewer
        name: Reviewer
        description: Focused review pass with todos and feedback
        order: 20
        plugins:
          - id: skill-tool
            name: "@deepseek-ai/dsh-tool-skill"
          - id: todo
            name: "@deepseek-ai/dsh-tool-todo"
            config:
              allowParallelInProgress: false
          - id: feedback
            name: "@deepseek-ai/dsh-command-feedback"
```

All three child packages are real installable plugins: `@deepseek-ai/dsh-tool-skill` (optional config `catalogDescriptionMaxLength`), `@deepseek-ai/dsh-tool-todo` (required config `allowParallelInProgress: boolean`), `@deepseek-ai/dsh-command-feedback` (no config). The `insert` form appends rows into the profile's entry list; a patch with `id` and no `insert` targets an existing row by id and replaces its fields (`config` is replaced wholesale, never deep-merged — restate every field).

## Ordering and shadowing

- `order` is roster metadata only: the picker and `ctx.agentPresets.list()` sort by `(order ?? Infinity)` then `id.localeCompare`. It never affects mounting.
- Plugin row order is Loader activation order inside the preset's entry tree; rows run in declared order and may use `group`, `disabled`, and `isolate` like any Loader row.
- The preset tree does not replace the base profile: the profile keeps the host (registry included), while the preset's rows mount under a registry-owned scope. Services a preset plugin provides register into that preset's layer, so for agents in the preset the nearest layer wins a duplicate name outright — a preset-scoped skill or tool shadows the global one. Rows that import-fail, miss an injected service, or leak a root-realm service reject the mount; the preset stays listed with a `broken` diagnostic instead of silently vanishing.

## Verify

See ./verify.md. Service-level, in a Node REPL over the running runtime:

```ts
const presets = await ctx.agentPresets.list();          // [{ id, name?, description?, order?, broken? }]
const roster  = await ctx.agentPresets.resolve("reviewer"); // metadata incl. failure
const doc     = await ctx.agentPresets.readDocument("reviewer"); // declared rows as YAML
const inv     = await ctx.agentPresets.compositionInventory();   // rows + activation states
```

Then select it for a session — `await ctx.agentPresets.select(agent, "reviewer")` before the first turn, or pick it in the web UI — and confirm a child capability activated: `ctx.agentPresets.serviceFor(agent, "skills")` (or `actionCards`, `tools`) returns the preset-scoped service, and the model's next turn sees the preset's tools and skills. A default may also be pinned through the registry row's `config.default`.

Related: [../SKILL.md](../SKILL.md) · [./bundle-anatomy.md](./bundle-anatomy.md) · [./skill-plugin.md](./skill-plugin.md) · [./action-card.md](./action-card.md) · [./tool.md](./tool.md) · [./command.md](./command.md) · [./verify.md](./verify.md)
