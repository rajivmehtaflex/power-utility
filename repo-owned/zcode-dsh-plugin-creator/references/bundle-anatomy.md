# Bundle anatomy: package.json, patch, and packaging

A DSH plugin ships as an npm package that is ALSO a bundle: a layer of loader
patch entries applied over the profile's stack. The profile composes layers in
order — each bundle in `dsh.profile.bundles`, then the profile's own
`cordis.patch.yml`, then any `--patch` CLI overlays — so your bundle adds or
overrides rows without touching the user's files. See `./verify.md` to prove
a bundle works end to end.

## package.json template

Derive every new bundle from this shape (proven against DSH 0.2.2-rc.1):

```json
{
  "name": "@your-scope/your-plugin",
  "version": "0.1.0",
  "description": "One-line summary shown in plugin lists",
  "type": "module",
  "main": "lib/index.js",
  "types": "lib/index.d.ts",
  "exports": {
    ".": {
      "types": "./lib/index.d.ts",
      "default": "./lib/index.js"
    },
    "./cordis.patch.yml": "./cordis.patch.yml",
    "./package.json": "./package.json"
  },
  "files": [
    "lib/index.js",
    "lib/index.d.ts",
    "cordis.patch.yml"
  ],
  "license": "MIT",
  "dsh": {
    "bundle": {
      "patch": "./cordis.patch.yml"
    }
  },
  "engines": {
    "dsh": "0.2.2-rc.1"
  },
  "scripts": {
    "build": "tsc -p tsconfig.json"
  },
  "peerDependencies": {
    "@deepseek-ai/cordis": "~4.1.0"
  },
  "dependencies": {
    "@deepseek-ai/schemastery": "~3.19.0"
  },
  "devDependencies": {
    "@deepseek-ai/cordis": "~4.1.0",
    "@deepseek-ai/dsh-commands": "0.2.2-rc.1",
    "typescript": "^5.7.3"
  }
}
```

Field notes:

- `exports` MUST expose `"./cordis.patch.yml"` and `"./package.json"` — the
  launcher reads both through the package's export map. `dsh.bundle.patch` is
  one path or an ordered list, each relative to the package root; it names
  the loader patch that defines this bundle's rows.
- Keep `@deepseek-ai/cordis` in BOTH `peerDependencies` and
  `devDependencies` at `~4.1.0`; the host supplies it at runtime.
- `dependencies` holds what the entry imports at runtime:
  `@deepseek-ai/schemastery` for plugin `Config` schemas. Add `zod` instead
  where a host type demands a zod schema (for example action-card kind
  details). `devDependencies` carries the typings package for every service
  you inject (`@deepseek-ai/dsh-commands`, `-tools`, `-skill`,
  `-agent-preset-registry`, `-action-cards`, ...) — only list what you import.

## Version pinning rule

Query the installed release (`dsh --version`, e.g. `0.2.2-rc.1`), then:

- Set `engines.dsh` to that EXACT version (`"0.2.2-rc.1"`, no range).
- Pin every `@deepseek-ai/dsh-*` devDependency to the same exact version.
- `@deepseek-ai/cordis` stays `~4.1.0`; `@deepseek-ai/schemastery` stays
  `~3.19.0` — these follow the host libraries, not the DSH release.
- Node must be >= 24.9.0 (the release's own engine floor); build with `pnpm`.

## tsconfig.json

Copy verbatim from the proven example:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "lib": ["ES2022"],
    "rootDir": "src",
    "outDir": "lib",
    "declaration": true,
    "strict": true,
    "verbatimModuleSyntax": true,
    "skipLibCheck": true,
    "sourceMap": false
  },
  "include": ["src"]
}
```

## cordis.patch.yml semantics

The bundle patch is a top-level YAML array of loader patch entries:

- `- insert:` appends one or more rows; each row is `{id, name, config}`:
  `id` is your stable row id, `name` is the plugin (a package name, or a file
  path relative to the patch file), and `config` is validated against the
  entry's `Config` schema at load.
- Rows are matched by `id` across layers. A later layer (a bundle further
  down `bundles`, the profile patch, or a `--patch` overlay) that reuses an
  id REPLACES its `config` wholesale — there is no deep merge.
- Patch entries may also target existing rows by `id` alone to override their
  config; `!!js` expressions are allowed in patch YAML (a stock profile patch
  uses `!!js` for a conditional `disabled` field).

Two-row example:

```yaml
# Bundle patch: two rows inserted over the base layer.
- insert:
    - id: command-hello
      name: '@your-scope/your-plugin'
      config:
        greeting: Hello, DSH
    - id: greeting-extras
      name: ./extras.mjs
      config:
        loud: false
```

Choose ids you own (`command-hello`, not `commands`): any downstream layer can
override or disable a row by that id.

## Optional distribution metadata

From the manifest schema (`dsh` field), all optional:

- `description`: package summary for discovery and display.
- `icon`: SVG, PNG, JPEG, or WebP file RELATIVE to the package directory, at
  most 256 KiB after resolution, and it must stay inside the package.
- `locale/<lang>.json`: localized display metadata as
  `{"meta": {"title": "...", "description": "..."}}`. An `en.json` fallback is
  REQUIRED (the `LocalizedText` rule: a literal string, or an object whose
  `en` key is mandatory); add one file per extra language.
- `dsh.bundle.platforms`: restrict to named host platforms; omit to allow all.
  `dsh.bundle.listedByDefault: false` hides the bundle from GUI lists until
  the profile enables it; omission means listed.

## Files that MUST ship

The `files` array is the contract — nothing outside it is installed:

1. `lib/index.js` — the compiled entry (`main`).
2. `lib/index.d.ts` — generated by `tsc` (`declaration: true`).
3. `cordis.patch.yml` — the bundle layer itself.
4. Any bundled skill assets the plugin registers (resource-base assets such
   as SKILL.md files) — see `./skill-plugin.md` before trimming `files`.

A missing `lib/` (forgot `pnpm build`) or a missing patch file fails loudly.

## README checklist for a new bundle

1. WHAT it registers: row ids, service injections, user-visible behavior.
2. Requirements: the pinned DSH version, Node >= 24.9.0, pnpm.
3. Build: `pnpm install && pnpm build`.
4. Install: `dsh plugin --profile <name> add file:/abs/path` — and check the
   package landed in `dsh.profile.bundles` after `@deepseek-ai/dsh-base`.
5. Verify: the `--dump-config` grep and the runtime probe from `./verify.md`.
6. Uninstall: `dsh plugin --profile <name> remove <package>`.

Related: `../SKILL.md` (workflow), `./verify.md` (runtime verification),
`./command.md`, `./tool.md`, `./skill-plugin.md` (per-type APIs).
