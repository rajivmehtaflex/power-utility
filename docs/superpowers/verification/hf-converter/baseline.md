# P1 Baseline — tooling pins and pre-existing repository state

Recorded: 2026-09-27. Host: Ubuntu 24.04.5 LTS (x86_64), 4 CPU, 14 GB RAM (11 GB available), 333 GB free disk.

## Branch and base

- Branch: `feat/hf-generative-model-converter`
- Base: `4614fe6e4cd026f4384de5a005d615623e58eb67` (matches the reference SHA recorded in the v2 plan)
- Plan v2 carried at `docs/superpowers/plans/2026-09-26-hf-generative-model-converter-skill-implementation-plan-v2.md`
- Design doc `2026-09-26-hf-generative-model-conversion-skill-design.md` referenced by the plan is **not present** in the repository and was not supplied; recorded as a missing input.

## Pinned authoring tooling (`tools/skill-validation/`)

| Component | Pin | Provenance |
|---|---|---|
| `skills-ref` (official Python validator) | `0.1.0` @ git rev `f130f348f502d9804278a617f86929846896d2e9`, subdirectory `skills-ref` | `pyproject.toml` + locked `uv.lock` (resolved: `click`, `strictyaml 1.7.3`, `python-dateutil 2.9.0.post0`, `six 1.17.0`) |
| `skills` npm installer | `1.7.0` exact | `package.json` + `package-lock.json` |
| Python interpreter | 3.12.3 | system (declared bootstrap input) |
| uv | 0.11.18 | declared bootstrap input |
| Node | v22.23.3 linux-x64 | nodejs.org official tarball, SHA256-verified, installed under `~/.local/node-v22.23.3-linux-x64` (declared bootstrap input) |
| npm | 10.9.2 | ships with the Node tarball |

## Exact invocations

```bash
# Official metadata validator (pinned)
uv sync --project tools/skill-validation --locked
uv run --project tools/skill-validation skills-ref validate repo-owned/unsloth-workflows

# Pinned installer (offline, from lockfile)
npm ci --prefix tools/skill-validation
tools/skill-validation/node_modules/.bin/skills --version   # → 1.7.0
```

Scope note: `skills-ref validate` checks Agent Skills metadata (frontmatter, naming, description bounds). It does **not** check links, runtime behavior, or catalog consistency.

## Observed baseline results

- Official validator on the existing owned skill: **PASS** (`Valid skill: repo-owned/unsloth-workflows`)
- Root tests `python -m unittest discover -s tests -v`: **7/7 OK**
- Unsloth skill tests `python -m unittest discover -s repo-owned/unsloth-workflows/tests -v`: **14/15 pass, 1 pre-existing failure**
  - `test_setup_dry_run_is_read_only_even_when_host_is_not_linux` — the setup script's NVIDIA GPU precondition (`nvidia-smi`) aborts before the dry-run logic on any GPU-less host. Reproduces identically on GPU-less GitHub runners; pre-existing, unrelated to this branch; Unsloth skill logic intentionally left unchanged (out of scope for P1).
- `MANIFEST.json` parses as JSON (`python -m json.tool`).

## Workflow correction (narrow — plan Gap 01)

`.github/workflows/unsloth-workflows.yml` inherited `npx -y skills-ref validate …`, which attempts to fetch `skills-ref` from npm; it is a Python distribution and is not published there. Replaced with the pinned route:

- `astral-sh/setup-uv@v10.2.0` pinned to uv `0.11.18`, then `uv sync --project tools/skill-validation --locked` + `uv run --project tools/skill-validation skills-ref validate …`
- Removed the now-unused `setup-node` step; added `tools/skill-validation/**` to the push/PR path triggers.
- No other workflow behavior rewritten. The pre-existing test failure above is expected to surface in CI unchanged and is reported, not masked.
