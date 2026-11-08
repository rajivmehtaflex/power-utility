# Skill plugins (model-invocable instructions)

Skills are instruction packages, not code the model runs. The `skills` registry (`ctx.skills` from `@deepseek-ai/dsh-skill`) merges provider catalogs, resolves the winning skill per name, and feeds the model-facing catalog plus the `skill` loader tool (`@deepseek-ai/dsh-tool-skill`); a loaded body is rendered as one canonical `<skill_content>` block. Contribute skills two ways: register a **provider** (a dynamic source such as directories) or **register a skill directly** (static, embedded in a plugin). Pinned: DSH 0.2.2-rc.1, Node >=24.9.0, `@deepseek-ai/schemastery` ~3.19.0 (config), `@deepseek-ai/cordis` ~4.1.0 (peer).

## Type imports

| Import | Purpose |
| --- | --- |
| `import type { SkillProvider, SkillProviderControl } from "@deepseek-ai/dsh-skill"` | provider contract; registration-scoped lifecycle control |
| `import type { SkillCandidate, SkillDefinition, SkillRegistration } from "@deepseek-ai/dsh-skill"` | catalog entry; loaded body; direct registration input |
| `import { isSkillName } from "@deepseek-ai/dsh-skill"` | name grammar check; also exports `isModelInvocable`, `isUserInvocable`, `renderSkillContent`, `BUNDLED_SKILL_RANK` |

## Shapes (quoted from `dsh-skill/lib/types/index.d.ts`)

```ts
interface SkillProvider {
  readonly name: string;            // unique in the ctx.skills registry
  readonly list: (options: SkillLookupOptions) =>
    Promise<readonly SkillCandidate[] | SkillProviderObservation>;
  readonly get: (candidate: SkillCandidate, options: SkillLookupOptions) =>
    Promise<SkillDefinition | undefined>;
}
interface SkillProviderControl {
  readonly signal: AbortSignal;      // aborts if registration fails or disposes
  readonly invalidate: () => void;   // drop caches; fires skills/change
}
interface SkillCandidate {           // extends SkillSummary
  readonly rank: number;             // lower rank wins a duplicate name
  readonly locator: unknown;         // opaque handle passed back to get()
  readonly metadata?: Readonly<Record<string, unknown>>;
}
interface SkillDefinition {          // extends SkillSummary
  readonly content: string;          // markdown body after frontmatter removal
  readonly metadata?: Readonly<Record<string, unknown>>;
}
type SkillRegistration = Omit<SkillDefinition, "invocation" | "provider"> & {
  readonly invocation?: SkillInvocationPolicy; // omitted permits both surfaces
  readonly provider?: string;                  // omitted uses "runtime"
};
```

Shared `SkillSummary` fields (both candidate and definition inherit): `name`, `description`, `whenToUse?`, `invocation: { modelInvocable, userInvocable }`, `source` (e.g. `"bundled"`, `"runtime"`), `provider`, `path?`, `resourceBase?`. `SkillLookupOptions` is `{ cwd?, signal? }`; `SkillProviderObservation` is `{ candidates, complete }` (return the plain array when discovery completed).

## Registration

```ts
import type { Context } from "@deepseek-ai/cordis";

export const inject = ["skills"];
export function apply(ctx: Context) {
  const disposeProvider = ctx.skills.registerProvider(
    (control) => new MyProvider(control),      // factory must be synchronous
  );
  const disposeSkill = ctx.skills.register({   // direct, runtime-rank entry
    name: "release-notes", description: "Draft release notes from git history",
    source: "bundled", content,
  });
  ctx.effect(function* () { yield disposeProvider; yield disposeSkill; });
}
```

Both methods return the Cordis effect disposer that unregisters. Every mutation fires the `skills/change` event (emit-only, no payload); consumers refetch `ctx.skills.list(options?)` or `ctx.skills.snapshot(options?)` and load bodies with `ctx.skills.get(name, options?)`. Registrations file into the caller's layer: an unscoped plugin registers globally, a plugin mounted by an agent preset registers into that preset's layer, and the nearest layer wins a duplicate name outright; `rank` breaks duplicates only within one layer.

## Naming rule

`isSkillName` validates `/^[a-z0-9]+(?:-[a-z0-9]+)*$/`: lowercase kebab-case segments, digits allowed, no leading/trailing hyphen. The registry throws on invalid names from providers and registrations; reserved names also throw.

## Template A — static registration (embedded content)

```ts
import type { Context } from "@deepseek-ai/cordis";

const content = `# Rename a branch safely

Before renaming a branch that others may track, check \`git branch -r\` for
remotes that already carry the target name, then rename and push with
--force-with-lease only when you own the branch.`;

export const inject = ["skills"];
export function apply(ctx: Context) {
  ctx.skills.register({
    name: "rename-branch-safely",
    description: "Rename a git branch without breaking remote tracking",
    whenToUse: "Renaming shared or already-pushed branches",
    invocation: { modelInvocable: true, userInvocable: false },
    source: "bundled",
    content,
  });
}
```

Omit `invocation` to permit both surfaces; omit `whenToUse` when the description alone routes well. The content string is the body the model receives verbatim inside `<skill_content>` — frontmatter-like headers belong in fields, not the body.

## Template B — minimal directory provider

Modeled on `@deepseek-ai/dsh-skill-filesystem` (the real implementation): the provider owns `list`/`get` over a directory, candidates carry a `locator` that `get` replays, and validation happens on both paths.

```ts
import { readFile, readdir } from "node:fs/promises";
import { join } from "node:path";
import { isSkillName } from "@deepseek-ai/dsh-skill";
import type { SkillCandidate, SkillDefinition, SkillProvider, SkillProviderControl } from "@deepseek-ai/dsh-skill";
// splitFrontmatter: your YAML frontmatter splitter (--- fences; name/description required)

class DirProvider implements SkillProvider {
  readonly name = "docs-provider";
  constructor(private control: SkillProviderControl, private root: string) {}
  async list({ signal }: { signal?: AbortSignal }) {
    const candidates: SkillCandidate[] = [];
    for (const entry of await readdir(this.root, { withFileTypes: true })) {
      signal?.throwIfAborted();
      if (!entry.isFile() || !entry.name.endsWith(".md")) continue;
      const name = entry.name.replace(/\.md$/, "");
      if (!isSkillName(name)) continue;
      candidates.push({
        name, description: `Docs skill ${name}`, invocation: { modelInvocable: true, userInvocable: true },
        source: "custom", provider: this.name, rank: 300,
        locator: { path: join(this.root, entry.name) },
      });
    }
    return candidates;
  }
  async get(candidate, options): Promise<SkillDefinition | undefined> {
    options.signal?.throwIfAborted();
    const raw = await readFile(String((candidate.locator as { path: string }).path), "utf8");
    const { frontmatter, body } = splitFrontmatter(raw); // name/description required
    return {
      name: candidate.name, description: frontmatter.description,
      ...("whenToUse" in frontmatter ? { whenToUse: frontmatter.whenToUse } : {}),
      invocation: candidate.invocation, source: candidate.source,
      provider: this.name, content: body,
    };
  }
}
export const inject = ["skills"];
export function apply(ctx: Context) {
  ctx.skills.registerProvider((control) => new DirProvider(control, process.env.DOCS_SKILLS_ROOT ?? "docs/skills"));
}
```

Call `control.invalidate()` whenever your source changes so catalogs refetch; abort long work on `control.signal`.

## When not to write a plugin

If skills simply live on disk, mount `@deepseek-ai/dsh-skill-filesystem` instead of writing a provider: it scans `<project>/.dsh/skills`, `<project>/.agents/skills`, `customSkillDirs`, `~/.dsh/skills`, `~/.agents/skills` and a bundled root (ranks 100–600, lower wins), accepts directory bundles `<name>/SKILL.md` or flat `<name>.md`, requires frontmatter `name` and `description` (optional `whenToUse`, `metadata`, `disable-model-invocation`, `user-invocable`), and watches roots so edits land without a restart. Write a plugin only when skills are generated, remote, or embedded in plugin data. `resourceBase` (`{ kind: "directory", path } | { kind: "url", url } | { kind: "opaque", description }`) tells consumers where the body's relative assets resolve — the filesystem provider sets it to the skill's owning directory; set it on bundled assets when the body references companion files.

## Verify

See ./verify.md. Service-level: `await ctx.skills.list()` shows the winning summary (name, description, provider); `await ctx.skills.get("rename-branch-safely")` returns the body; a `ctx.on("skills/change", ...)` listener proves invalidation fires on register/dispose. End to end: one model turn must show the skill in the `<available_skills>` catalog and load it through the `skill` tool. SKILL.md format conventions: https://agentskills.io/specification

Related: [../SKILL.md](../SKILL.md) · [./bundle-anatomy.md](./bundle-anatomy.md) · [./preset.md](./preset.md) · [./action-card.md](./action-card.md) · [./tool.md](./tool.md) · [./command.md](./command.md) · [./verify.md](./verify.md)
