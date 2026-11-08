# Tool plugins (model-facing tools)

A tool plugin registers a tool the **model calls during a turn** on the `tools` service (`ToolsService` from `@deepseek-ai/dsh-tools`, composed into every profile through `@deepseek-ai/dsh-base`). Unlike commands (./command.md), tools are model-facing: the definition carries its own JSON-schema `parameters` for the model and a mandatory `output` contract (schema + renderer) that the executor enforces. Pinned: DSH 0.2.2-rc.1, Node >=24.9.0, `@deepseek-ai/schemastery` ~3.19.0 (config), `@deepseek-ai/cordis` ~4.1.0 (peer).

## Type imports

| Import | Purpose |
| --- | --- |
| `import { defineTool } from "@deepseek-ai/dsh-tools"` | typed definition helper (preferred) |
| `import type { ToolDefinition, ToolRunContext } from "@deepseek-ai/dsh-tools"` | registration shape; second `execute` argument |
| `import type { ToolOutputDefinition, ToolResult } from "@deepseek-ai/dsh-tools"` | output contract |
| `import type { ToolSchema, ContentBlock } from "@deepseek-ai/dsh-llm"` | model-facing schema; content blocks |

## Shapes (from `dsh-tools/lib/types/` and `dsh-llm`)

```ts
// @deepseek-ai/dsh-llm — the model-facing half
interface ToolSchema {
  deferLoading?: true;                 // request deferred loading into model context
  name: string;
  description: string;                 // sent to the model — write it for the model
  parameters: Record<string, unknown>; // JSON Schema object for arguments
}
// @deepseek-ai/dsh-tools — the executor-facing half
interface ToolOutputDefinition {
  schema: JsonSchemaNode;                              // enforced JSON Schema subset
  render(args: unknown, value: JsonValue): ContentBlock[]; // pure projection
  presentationMeta?(args: unknown, value: JsonValue): JsonValue;
}
interface ToolDefinition extends ToolSchema {
  output: ToolOutputDefinition;        // MANDATORY
  execute(args: unknown, exec: ToolRunContext): Promise<unknown>;
  timeoutMs?: number;                  // cooperative budget; never sent to the model
  isConcurrencySafe?(args: unknown): boolean; // only `true` opts into parallel groups
  presentCall?(args: unknown): ToolCallView | undefined;  // pure; replayed by UIs
  presentResult?(args: unknown, result: ToolResult): ToolResultView | undefined;
  projectContent?(exec: Readonly<ToolExecution>, result: Readonly<ToolExecutionResult>): ContentBlock[] | undefined;
  finalizeContent?(exec: Readonly<ToolExecution>, result: Readonly<ToolExecutionResult>): ContentBlock[] | undefined;
}
```

`JsonSchemaNode` is an enforced subset: `type` (`object|array|string|number|integer|boolean|null`), `properties`, `required`, `additionalProperties`, `items`, `enum`, `const`, `oneOf`; `description`/`title`/`default`/`examples` are annotations only. Anything else rejects.

## The ergonomic path: `defineTool`

`defineTool` compiles an author-friendly spec, infers `args`/`value` types, and validates arguments before `execute` runs. `parameters` is a per-property map (implicit open object root); mark requiredness with `required: true` on each property, not a top-level array. Convention from the builtins (`dsh-tool-todo`, `dsh-tool-goal`): describe every property, and return a plain text block from `render`.

```ts
function defineTool<
  const S extends ParameterSchemaSpec,
  const O extends ValueSchemaSpec,
>(options: DefineToolOptions<S, O>): ToolDefinition;
// Minimal complete tool, following builtin conventions (dsh-tool-todo):
import { defineTool } from "@deepseek-ai/dsh-tools";
const echoUpper = defineTool({
  name: "echo_upper",
  description: "Echo text back uppercased. Deterministic fixture.",
  parameters: {
    text: { type: "string", required: true, description: "Text to uppercase." },
  },
  output: {
    schema: { type: "string" },
    render: (_args, value) => [{ type: "text", text: value }],
  },
  execute(args) {
    return Promise.resolve(args.text.toUpperCase());
  },
});
```

## Registration

```ts
ctx.tools.register(definition);              // → disposer that unregisters
ctx.tools.register(definition, { when });    // when(context): step-time activation condition
ctx.tools.restrict({ allow: ["a"], deny: ["b"] }); // per-scope global mask → disposer
ctx.tools.guard((exec) => undefined);        // monotonic denial (reason string) → disposer
ctx.tools.setExecutor(executor);             // scope executor provider → disposer
```

Scoped tools (registered from a child of an agent context) shadow globals for that agent, mirroring commands.

## Reserved names

`run_code` is reserved (`RUN_CODE_NAME`, the PTC-mode presentation transport): `register` throws if you register or shadow it, and `restrict` may not name it. That is the only reserved name; duplicates within one layer also fail.

## Output contract gotchas

- `render` must return an array of content blocks. The simplest is `TextBlock` from `@deepseek-ai/dsh-llm`: `{ type: "text", text: string }`.
- `execute`'s resolved value is validated against `output.schema`; a violation fails the call loudly (`ToolOutputError`). `defineTool` tools additionally get arguments validated first (`ToolArgsError`).
- `render`, `presentCall`, and `presentResult` must be pure — UIs replay them from session logs. Forward `exec.signal` in async work; a declared `timeoutMs` asserts you do.

## Worked template (`src/index.ts`)

```ts
import type { Context } from "@deepseek-ai/cordis";
import { defineTool } from "@deepseek-ai/dsh-tools";
import z from "@deepseek-ai/schemastery";

// Same gotcha as commands: defaults must not duplicate what execute appends.
const Config = z.object({ suffix: z.string().default("") });

interface EchoUpperPlugin {
  (ctx: Context, config: { suffix: string }): void;
  inject: string[];
  Config: typeof Config;
}

const plugin: EchoUpperPlugin = (ctx, config) => {
  ctx.tools.register(defineTool({
    name: "echo_upper",
    description: "Echo text back uppercased.",
    parameters: {
      text: { type: "string", required: true, description: "Text to uppercase." },
    },
    output: {
      schema: {
        type: "object",
        additionalProperties: false,
        properties: { text: { type: "string", required: true } },
      },
      render: (_args, value) => [{ type: "text", text: value.text }],
    },
    execute(args) {
      return Promise.resolve({ text: `${args.text.toUpperCase()}${config.suffix}` });
    },
    isConcurrencySafe: () => true, // read-only, no shared state
  }));
};

plugin.inject = ["tools"];
plugin.Config = Config;

export default plugin;
```

## Config schema and inject

Identical discipline to commands: static `Config` (schemastery `z.object` with `.default(...)` on every key) validated against the bundle patch row at load; static `inject = ["tools"]` plus any services the handler uses; read config inside the closure.

## Verify

Without a model turn (see ./verify.md): introspect with `ctx.tools.definitions()` (global view when scope omitted), `ctx.tools.schemas()` (model-facing projection), `ctx.tools.get("echo_upper")`; or execute directly through the service:

```ts
import { ToolCallId } from "@deepseek-ai/dsh-llm";
const batch = await ctx.tools.execute({
  calls: [{
    type: "tool-call",
    id: ToolCallId("verify-1"),
    name: "echo_upper",
    arguments: JSON.stringify({ text: "hi" }),
  }],
  signal: new AbortController().signal,
});
```

Then confirm end to end with one real model turn (for example via the `dsh` headless entry point): the model must discover `echo_upper` via `ctx.tools.schemas()` and its call must settle through the output contract.

Related: [../SKILL.md](../SKILL.md) · [./bundle-anatomy.md](./bundle-anatomy.md) · [./command.md](./command.md) · [./verify.md](./verify.md)
