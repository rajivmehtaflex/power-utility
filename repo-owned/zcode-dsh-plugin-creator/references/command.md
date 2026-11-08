# Command plugins (`/name` in the chat input)

A command plugin registers a slash command on the `commands` service (the registry exported by `@deepseek-ai/dsh-commands`, composed into every profile through `@deepseek-ai/dsh-base`). Commands run with **no model turn**: typing `/name args` dispatches straight to your handler, and the web/tui UI renders the returned `CommandResult` directly. Use commands for deterministic, human-triggered actions — never for work the model should decide. Pinned: DSH 0.2.2-rc.1, Node >=24.9.0, `@deepseek-ai/schemastery` ~3.19.0 (config), `@deepseek-ai/cordis` ~4.1.0 (peer).

## Type imports

| Import | Purpose |
| --- | --- |
| `import type { CommandDefinition } from "@deepseek-ai/dsh-commands"` | shape passed to `ctx.commands.register` |
| `import type { CommandInvocation } from "@deepseek-ai/dsh-commands"` | single handler argument |
| `import type { CommandResult } from "@deepseek-ai/dsh-commands"` | handler return union |
| `import { CommandDefinitionId } from "@deepseek-ai/dsh-commands"` | optional stable identity (brand constructor) |

## Shapes (from `dsh-commands/lib/types/`, trimmed to author-facing fields)

```ts
interface CommandDefinition {
  definitionId?: CommandDefinitionId; // stable plugin-owned identity
  name: string;                       // lowercase, no leading slash
  description: string;                // shown in discovery UI
  input?: { hint: string; attachments?: boolean }; // hint must be non-empty when present
  recordInput?: boolean;              // default true; false when a domain event owns the payload
  handler: (invocation: CommandInvocation) => CommandResult | Promise<CommandResult>;
}

interface CommandInvocation {
  commandId: CommandId;          // pairing id for command/run + command/done events
  agent: Agent;                  // exact agent whose UI dispatched the line
  rawInput: string;              // text after the name, verbatim (whitespace included)
  attachments: readonly (ImageBlock | FileBlock)[]; // empty unless input.attachments
  signal: AbortSignal;           // cancellation owned by the dispatching UI request
}

type CommandResult =
  | { kind: "success"; text?: string; sourceEventSeq?: SessionSeq }
  | { kind: "error"; text: string }; // error text must be a non-empty string
```

## Naming rules

- `name` must match `/^[a-z][a-z0-9_-]*$/`. No leading slash, no uppercase. `register` throws a `TypeError` on mismatch, empty `description`, or a non-function `handler`.
- Builtin names resolve first-party: `goal`, `plan`, `feedback`, `compact`, `permission`, `export` (plus Simplified Chinese tokens 目标 计划 反馈 压缩 权限 导出). Typing a builtin token always selects the first-party definition, so a same-named plugin command is unreachable. Avoid all of them.

## Worked template (`src/index.ts`)

```ts
import type { Context } from "@deepseek-ai/cordis";
import type { CommandDefinition } from "@deepseek-ai/dsh-commands";
import z from "@deepseek-ai/schemastery";

// Cordis validates the bundle patch row's config against this at load.
// Gotcha: keep punctuation OUT of string defaults — the handler appends its own.
// greeting "Hello!" would render "Hello!, name!".
const Config = z.object({
  greeting: z.string().default("Hello, DSH"),
});

interface HelloPlugin {
  (ctx: Context, config: { greeting: string }): void;
  inject: string[]; // Cordis reads inject/Config off the plugin itself
  Config: typeof Config;
}

const plugin: HelloPlugin = (ctx, config) => {
  const definition: CommandDefinition = {
    name: "hello",
    description: "Say hello from the bundle plugin",
    input: { hint: "[name]" },
    handler(invocation) {
      const name = invocation.rawInput.trim();
      if (name.length > 32) {
        return { kind: "error", text: "name must be at most 32 characters" };
      }
      return {
        kind: "success",
        text: `${config.greeting}${name ? `, ${name}` : ""}!`,
      };
    },
  };
  ctx.commands.register(definition); // returns the disposer that unregisters
};

plugin.inject = ["commands"]; // the commands service name
plugin.Config = Config;

export default plugin;
```

## Scoped commands

`register` on a plain context is global. Register through a child of an agent context and the definition shadows the global one **for that agent only** — other agents keep the global. Use this to offer an agent-specific variant without uninstalling anything.

## Config schema

- Declare a static `Config = z.object({...})` (schemastery, ~3.19.0) with `.default(...)` on every key so a missing patch row still loads.
- The bundle patch row's `config` value is validated against it at plugin load; schema defaults apply before the entry runs.
- Read config inside the handler closure, not at module scope, so reloads pick up new values.

## Verify

Registration and dispatch are checkable without a model turn. See ./verify.md for the full recipe:

- `ctx.commands.list(undefined)` — name-sorted effective descriptors (`undefined` = global view; the parameter is typed `Agent`, so cast in strict TS).
- `ctx.commands.find(undefined, "hello")` — resolve one definition and inspect `input.hint`.
- Invoke `definition.handler({ rawInput: " world", ... })` directly with a stub invocation and assert the `CommandResult`.

Related: [../SKILL.md](../SKILL.md) · [./bundle-anatomy.md](./bundle-anatomy.md) · [./tool.md](./tool.md) · [./verify.md](./verify.md)
