# Refresh durability exercise (plan P9)

Executed 2026-09-27 on a disposable copy of the repository (`/tmp/refresh-test`; `.git`,
`.hf-converter`, venvs excluded). Two tests against `tools/import_generated_skills.py`:

## Test A — adversarial: staged collection shadows the owned skill's name

Staged `profile/hf-generative-model-converter` (a copy of the owned SKILL.md) → importer **rejected**
the import: `ValueError: duplicate skill name(s): hf-generative-model-converter`. Owned skill tree
byte-identical after the rejected import.

## Test B — normal refresh: new generated group replaces `profile/`

Staged a generated `profile/` containing two fixture skills → import succeeded; the whole generated
group was replaced by the staging content (documented semantics: staging replaces the group). Verified:

- Tracked content of `repo-owned/hf-generative-model-converter` **byte-identical** before/after
  (SHA-256 over all tracked files, build artifacts excluded).
- The `hf-generative-model-converter` entry in `MANIFEST.json` **survived `rebuild_catalog` verbatim**
  (name, source=repo-owned, category, description, original_fields, spec_compliant, warnings).
- Fixture entries were imported with `spec_compliant: true` — the importer's optimistic compliance
  assignment applies to *generated* skills (pre-existing behavior).

## Findings and limitation

1. Durability of repo-owned content: **confirmed** — refresh neither deletes, modifies, nor
   re-catalogues the owned skill's evidence.
2. Name-collision protection: **confirmed** — a generated skill cannot shadow or overwrite an
   owned skill; the import aborts.
3. Known pre-existing limitation (not fixed here, maintainer's call): `rebuild_catalog` forces
   `spec_compliant: true` for every entry it rebuilds, so *if* a skill's metadata validation ever
   regressed while its warnings list stayed empty, refresh would overstate compliance. Today every
   entry is genuinely compliant (74/74 validated 2026-09-27), so no falsification occurs; the plan's
   "make only a demonstrated, tested correction" bar is not met yet. Noted for a future maintainer
   change to derive compliance from recorded validation evidence instead of hard-coding it.
