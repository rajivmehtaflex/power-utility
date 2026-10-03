# Explainify — implementation results

- **Implemented:** 2026-10-02 → 2026-10-03, from `docs/superpowers/plans/2026-10-02-explainify-skill-plan.md`
- **Base revision:** `2fbc06ba41a12aa7320e1ac15db636b53f5f3921` (main); working tree carries the
  changes below, **nothing committed** (commit/push/PR follow the user's separately authorized scope)
  — *superseded 2026-10-03: this change-set was committed, reviewed (PR #8), and merged; see §8 and §9*
- **Method:** task-by-task subagent-driven development (per the plan's required execution style;
  20 subagents across 7 dependency-ordered waves, each task spec'd + independently verified)
- **Scope:** milestones M1–M3 complete; M4 (diagram/HTML/narration) intentionally untouched

## 1. Package (repo-owned/explainify/) — delivered files

| File | Content | Evidence |
|---|---|---|
| `SKILL.md` | 257 lines, dispatch table (2 live + 2 reserved formats), 5-step workflow, verification gates, output contract, 12 non-negotiable rules | `skills-ref validate` PASS ×2 (post-M1 and final); T13 FrontmatterTests 8/8 |
| `references/asd-ste100.md` | 84-line approximate STE-inspired writing profile with official-standard attribution | T04 checks; audit D1 |
| `references/video-style.md` | 132-line visual style guide (palette, scene grammar, timing, §7 verification recipe) | T04 checks; audit D1 |
| `assets/storyboard.schema.json` | draft-2020-12, schema_version 1.0, topic-neutral, cross-field rules documented as renderer-enforced | 11-case validation matrix all-correct (T03) |
| `scripts/check_env.py` | stdlib-only preflight; `--format asd-ste100` exits 0 without video probes; `--format explainer-video` checks uv/Python-3.11+/ffmpeg/ffprobe/H.264 | pass + sandboxed-FAIL + JSON outputs verified (T09); reproduced by audit E |
| `scripts/render_video.py` | 1,167-line template: stable CLI (`--check-only`/`--output [--overwrite]`/`--self-test`), `validate_storyboard`/`draw_scene`/`main` contract, embedded schema, PEP-723 deps, guard-before-render, encoder preflight | contract tests 24/24 GREEN (T08, RED-first in T07); `--self-test` OK |
| `tests/test_video_contract.py` | 24 tests over the three public interfaces | 24/24 OK (final re-run) |
| `README.md` (99 lines) + `LICENSE` (MIT, © 2026 rajivmehtapy) | usage, requirements, documented-vs-tested install paths, reproduction command | T06 checks; canonical-MIT diff clean |

## 2. Monorepo integration

- **MANIFEST.json:** one `explainify` entry (`repo-owned`, category `creative`, full 305-char
  single-line description equal to the regex-extracted frontmatter line, populated
  `original_fields`, `warnings: []`). `rebuild_catalog()` run as an implementation step; seeded
  fields survived. Counts: `len(skills) == 75 == rglob("SKILL.md")`.
  - *Deliberate post-processing:* the helper's single-line regex degraded 11 unrelated entries'
    descriptions (one to literal `">-"` garbage) and rewrote historical `Total:` lines; both were
    restored to HEAD values to keep this change-set scoped to explainify (the helper limitation
    is recorded here for a future sanctioned pass; unrelated entries were NOT hand-edited beyond
    the restoration).
- **README.md (root):** counts `· 75 skills` / `Install ALL 75 skills`; index row + maintainer
  section prose + `npx skills add rajivmehtaflex/power-utility --skill explainify` block.
- **VALIDATION_REPORT.md:** historical totals preserved (73 baseline, 74 addenda); new
  `## 2026-10-02 addendum — explainify` with `Total: 75 skills; 75 spec-compliant; 0 failed`.
- **tests/test_explainify_package.py:** 32 tests (frontmatter/resources/links/catalog/portability
  + refresh-preservation + name-collision rejection). Full root suite: **58/58 OK**
  (pre-existing suites still green).
- **.github/workflows/explainify.yml:** pins byte-match siblings (checkout@v4, setup-python@v5
  py3.12, setup-uv@v10.2.0 uv 0.11.18), `contents: read`, 11 path filters, locked validator +
  installer, contract tests via the separate uv runtime, deterministic 2-s encode/decode smoke
  (ffprobe CSV `h264,1280,720,yuv420p,30/1` + full decode + no-audio asserts), compileall.
  The smoke chain was validated locally end-to-end against a contract-equivalent render;
  **the workflow itself first runs in GitHub Actions only after push** (not yet executed).
- **.gitignore:** `explainify-output/` appended; changed-file review clean (no mp4s/frames/envs;
  `git status` shows exactly the expected new/modified paths).

## 3. Toolchain (pinned)

`skills-ref 0.1.0` @ agentskills git `f130f348f502d9804278a617f86929846896d2e9` (uv.lock rev 3,
validator env Python 3.13.14) · npm `skills 1.7.0` (node v26.10.0) · render runtime: uv 0.12.21
(2026-10-02 runs) / 0.12.22 (2026-10-03 runs; Homebrew updated mid-suite — recorded), Python
3.12.10 or 3.13.14 per run, numpy 2.5.3, matplotlib 3.11.2, jsonschema 4.26.0, ffmpeg/ffprobe
9.0.2 with `h264_videotoolbox` on macOS arm64.

## 4. §9 evaluation suite — case results

| Case | Result | Key evidence |
|---|---|---|
| C1 ring attention (both) | **pass** | Writing: 64 sentences, max 20, 0 over target; numeral scan: no performance claims. Video: 39.5 s, 14/14 frames PASS, 1 repair, on-screen-number audit clean (D1–D4 + "illustrative layout" only) |
| C2 URL article (both) | **pass** | Provenance complete (Spolsky 2003-10-08, retrieved 2026-10-03, source SHA-256 `e2c91236…eafe`, ~3,660 words); 27/27 claims verbatim-verified by audit; video 39.0 s, 11/11 frames PASS, 0 repairs; 26/26 on-screen essay-facts verified |
| C3 .md fixture (both) | **pass** | Fixture byte-identical to frozen block (SHA-256 `9f3ad6bb…3aae`); 3/3 dates, 4/4 negations, 3/3 uncertainty preserved; video 37.5 s, 12 frames, 1 repair (Jamaica-label collision), re-verified |
| C4 water cycle (both) | **pass** | Video: 40.0 s, 16 frames, 1 repair, 11/11 inspected PASS, zero ML artifacts (anti-stale-assumption case). Writing: 5/5 must-preserve groups, 0 sentences >20 words |
| C5 date/negation/uncertainty + embedded instruction | **pass** | 3/3 dates, 4/4 negations, 3/3 uncertainty; instruction quoted as content, before/after listings prove nothing deleted |
| C6 blocked URL | **pass** | Real DNS failure (`.invalid`), `retrieval_status: unavailable` stated, two documented paths offered, **no explanation file created — no silent substitution**. `retrieval_status: partial` was **not observed** in any run and is recorded as not observed per the case's own rule (schema 1.1 now enforces the same provenance discipline programmatically) |
| C7 long input + reserved format | **pass** | 2,116-word source → focused brief + full omission record (11 sections listed); `diagram` request refused with both supported formats offered |
| C8 capability handling | **pass (partly modeled)** | Writing completed with zero video-tool invocations (`check_env --format asd-ste100` exit 0). The visually-unverified delivery statement was **modeled, not executed** — every producing agent on this host has image inspection, so an uninspected video could not occur here; the modeled statement (`c8-visual-unverified-demo.md`) shows the exact wording a real delivery would carry |
| C9 invalid storyboard + existing output | **pass** | Contract tests reject malformed storyboards before rendering; overwrite guard verified in tests + live (T12: existing file untouched, exit 1) |
| C10 listing + copied installation | **pass** | `skills add … --list`: exactly one `explainify` of 75; `--skill explainify --agent claude-code --copy -y` in a temp project → byte-identical 9-file copy, preflights exit 0 from foreign cwd; no live/global installs |
| C11 refresh + name collision | **pass** | Normal refresh: owned bytes + manifest entry identical after; staged `explainify` duplicate → `ValueError: duplicate skill name(s)` before any group replaced; disposable copies only |
| C12 manifest/README/totals | **pass** | One owned entry, real description, 75==75==75 counts, historical evidence preserved |

**Independent audit (T21+T22): PASS on all 16 items** — claims-vs-source (A1–A5), recomputed
arithmetic (B1–B4: softmax rows, 15°/h, 981 MJ→272.5 kWh, UTF-8 bytes), illustrative labels (C,
three layers), links/frontmatter/catalog/script-independence (D1–D4), claimed-vs-actual ffprobe
spot checks + consistency sweep (D5, E). Findings: **F1** — cosmetic 3-dp rounding inconsistency
(`0.021` vs `0.020`) inside the self-attention storyboard's internal calculation text; the
viewer-visible 2-dp value is correct and the deviation (0.00052) is inside tolerance; left as-is
because evidence files record what was actually verified. **F2** — this file's earlier absence
made the README's evidence pointer forward-looking; resolved by this file.

## 5. Verification totals (final re-run, 2026-10-03)

- `skills-ref validate repo-owned/explainify` → **Valid skill** (exit 0)
- Contract tests → **24/24 OK** · Root suites → **58/58 OK** · `MANIFEST.json` parses
- Five delivered videos: all h264/1280×720/30fps/yuv420p/silent, durations 42.0/40.0/39.5/39.0/37.5 s
  matching storyboard totals within one frame + 0.01 s, full-decode clean, ≥1 visually-inspected
  frame per scene + transitions (66 frames inspected total across the five)
- External reproduction (T12): self-attention bundle re-rendered from a bare temp dir with only
  the two bundle files → **bit-identical SHA-256** (`28eeec1a…e9822ec`) on the recorded runtime
  set (encoder-dependent; VideoToolbox on this host)

## 6. Honest limitations

1. **Cross-client discovery: NOT verified.** Claude Code CLI present but logged out; Codex has no
   safe non-interactive probe; Cursor/Gemini not installed; ZCode user-scope dir is live
   (installs forbidden during verification) and project-scope loading is undocumented. All
   clients recorded UNTESTED with reasons (`discovery-evaluation.md` is design-level only).
2. **CI workflow not yet executed** — it requires a push to GitHub Actions; local validation
   covered YAML, pins, and the smoke chain's commands against a contract-equivalent render.
3. **Installer overwrite semantics:** `skills 1.7.0` under `-y` *announces* ("overwrites:") then
   auto-replaces an existing destination skill (sentinel-tested). Pre-install existence checks
   remain a procedural requirement documented in the package README.
4. **Public install command untested** against a published ref (package not yet pushed).
5. **Video outputs are silent** (v0.1 has no narration path; no TTS-service claims made).
6. **Audit depth:** the independent auditor re-inspected 5 frames pixel-wise and re-ran 2 ffprobe
   checks; the remaining ~70 frame inspections are the producing agents' evidence, accepted on
   internal consistency (auditor's scope note).
7. **STE output is approximate** by design; no ASD-STE100 conformity is claimed anywhere.

## 7. Deliverable inventory (this change-set)

New: `repo-owned/explainify/**` (9 files), `tests/test_explainify_package.py`,
`.github/workflows/explainify.yml`, `docs/superpowers/plans/2026-10-02-explainify-skill-plan.md`,
`docs/superpowers/verification/explainify/**` (cases.md + per-case evidence, this results.md).
Modified: `MANIFEST.json`, `README.md`, `VALIDATION_REPORT.md`, `.gitignore`.
Ignored: `explainify-output/**` (13 run dirs: 5 video bundles with frames, 5 writing runs, and
the C6/C7/C8 workflow-evidence dirs). Nothing committed.

## 8. Post-push CI finding (2026-10-03, branch feat/explainify-skill)

First push (`cee610a`) exposed a test-portability bug: the sibling workflows
(unsloth-workflows, hf-generative-model-converter) also run the full root suite, and
`PortabilityTests.test_video_preflight_json_passes_from_foreign_cwd` asserted exit 0 from the
video preflight — which requires uv/ffmpeg on the host. Their bare runners correctly reported
"preflight: FAIL (4 missing)", failing that one test (all other 57 passed). Fix: the test now
asserts the preflight's contract — returncode ∈ {0,1}, valid JSON, `pass` consistent with the
exit code and with the per-check booleans, "preflight: PASS|FAIL" line present, and actionable
"install with" hints on the fail path — so it verifies accurate reporting on tool-rich hosts
(pass path exercised locally) and bare runners alike, matching the plan's §8 principle that
capability reporting must work without the video toolchain. Verified on both paths locally
before pushing the fix.

A second, related CI finding from the same run: the `python-3.11+-via-uv` probe used
`uv python find 3.11`, which matches only 3.11.x — so hosts with just 3.12/3.13 (the GitHub
runner) were falsely reported as missing Python despite satisfying the skill's declared
"Python 3.11+" requirement. The probe now requests `>=3.11` (still read-only discovery, no
installs), so any 3.11-or-newer interpreter passes and the runner preflight is fully green.


## 9. 2026-10-03 review round — v0.1.1 (`fix/explainify-review-round-1`)

An external code review raised 8 P2 and 3 P3 gaps; all 11 were confirmed against the code
(two were worse than reported) and fixed on this branch. Version 0.1.0 → **0.1.1**;
storyboard schema 1.0 → **1.1** (1.0 documents remain valid; all five delivered bundles
re-validated against the new schema, PASS).

| Gap | Fix | Verification |
|---|---|---|
| P2 frame rounding accumulated (0.30 s → 0.40 s, reproduced as 6×0.05 s → 12 frames) | `_frame_schedule` allocates boundaries from cumulative timing; total = round(total×fps) exactly | 6×0.05 s → 9 frames (0.30 s); 100-trial fractional property test; regression render 1.5 s → exactly 45 frames |
| P2 supplied scenes never drawn before encoding (malformed math produced partial MP4s) | `_prerender_check` rasterizes every scene at two progress values and measures all text extents before the output figure exists | broken-mathtext storyboard → nonzero exit, scene named, no output file; `--check-only`/`--self-test` unchanged |
| P2 `libx264`-only builds rejected ("h264" ∉ "libx264"); writer ignored the discovered encoder | `_select_encoder` matches h264/x264 variants with software-first preference; writer gets the selected codec; per-encoder `-crf`/`-q:v` args (conservative minimum for unknowns) | table tests incl. libx264-only, videotoolbox-only, none; Mac regression render used the selected encoder end-to-end |
| P2 long text drew past the frame (≈4,810 px overflow) | `_fit_scene_text` wraps (hard-breaking unbreakable tokens), steps 27→16 pt by line budget, truncates with ellipsis + warning; pre-render extent check rejects any residual overflow before encoding | 1,200-char text → wrapped/truncated, render exit 0; extent measurement enforced in `_prerender_check` |
| P2 duplicate claim IDs accepted | `validate_storyboard` rejects duplicate `brief.claims[].id`, naming the id | rejection test; ambiguous-reference scenario gone |
| P2 URL provenance unenforced | schema 1.1 `allOf` conditionals: url+complete/partial requires non-null `resolved_location`+`retrieved_at`; url+unavailable requires `requested_location` | 8-case behavioral matrix; topic/text/file inputs unaffected (test-pinned) |
| P2 broken `ffprobe` passed preflight (existence check only) | `check_ffprobe` now executes `ffprobe -version` and checks the exit code, mirroring `check_ffmpeg` | code inspection + sandboxable fail path (same technique as T09) |
| P2 SKILL.md said the storyboard embeds the schema (rejected by `additionalProperties: false`) | wording corrected: the render script embeds the schema as its validation default (as the plan §7 assigns) | `skills-ref validate` PASS; link/frontmatter tests green |
| P3 results.md stale (said "nothing committed", CI unexecuted) | header annotated as superseded with pointers; this section records commits/PR/CI | this section |
| P3 coverage gaps (visually-unverified modeled not executed; html-page refusal; partial not observed) | C8 row relabeled "partly modeled" with reason; dedicated `html-page-refusal.md` added; partial-not-observed recorded on the C6 row | this section + new evidence file |
| P3 preflight "never writes anywhere" inaccurate (uv cache metadata) | docstring reworded: no user/project writes; uv probe may refresh uv's own cache | wording review |

Post-fix suite state on this branch: contract tests 42/42 (24 original + 16 new + adjusted
wrap assertion), root suite 58/58 (version assertions moved to 0.1.1, schema-version
assertion moved to the 1.0/1.1 enum), `skills-ref validate` PASS, five delivered 1.0
storyboards re-validated PASS, regression render (fractional durations + 1,200-char text)
→ exactly 45 frames/1.500000 s, h264/yuv420p/30 fps/no audio, full decode clean.


## 10. 2026-10-03 speed round — v0.2.0 (`feat/explainify-preview-mode`)

Four performance suggestions (preview step, renderer caching, within-task reuse, keep the
final checks) were measured against the code before anything was changed, and the
measurements are why three of them landed differently from the suggestion.

| Suggestion | Outcome | Verification |
|---|---|---|
| 1. Preview the scenes before rendering all frames | **Shipped.** `--preview PATH` validates, runs the same `_prerender_check` as `--output`, then draws every scene once at progress 1.0 into one labeled PNG contact sheet (one 12.8×7.2 in, dpi-100 cell per scene; no ffmpeg, no encoder, no video) | 7 new contract tests: PNG written and no MP4 (`no video was encoded` in output); 3 scenes tile as 3 cells across one row; works with `ffmpeg`/`ffprobe` removed from `PATH`; invalid storyboard and broken-mathtext rejection write nothing; existing-path guard; mode exclusivity. 3-scene 21 s storyboard: preview 0.44 s vs render 10.36 s |
| 2. Cache static artwork instead of redrawing | **Deferred, not shipped.** `draw_scene` is 3.4 ms of an 8.1 ms frame (37%); the rasterize/PNG/pipe/x264 remainder (63%) is untouched by any drawing cache, so the realistic saving is ≈1 s on a 10 s render. Also structural: SKILL.md has each run replace `draw_scene` in its own copy, so a template-level cache stays inert until every adapter opts in | per-frame cost decomposition measured on the merged template; decision recorded here rather than coded |
| 3. Reuse retrieved pages and the brief within a task | **Shipped as workflow text.** Step 1 gains a `refresh_sources` request field and a one-task-retrieves-once rule; no delivery-contract change (writing still ships one file unless `retain_brief`, video still four) | SKILL.md review; `skills-ref validate` PASS; no test change required |
| 4. Keep storyboard/scene/format/decode checks | **Kept and pinned.** Step 4's five checks are textually unchanged; one new sentence and a clause in non-negotiable rule 9 state that a preview is not frame inspection | Step 4 diff is additive only; preview output says "no video was encoded"; `references/video-style.md` verification recipe leads with the same rule |
| (found while measuring) `_prerender_check` measured `ax.texts` only | `_overflow_message` now covers patches and lines too, respecting clipping: unclipped artists that escape are reported, clipped ones only when they miss the frame entirely, so a deliberate full-bleed background still passes | rejection test for an unclipped patch past the edge; acceptance test for full-bleed and half-past-edge clipped patches; manual probe over unclipped / clipped / alpha-0 / invisible cases |

Template version 0.1.1 → **0.2.0** (SKILL.md frontmatter, MANIFEST `metadata_version`, three
root-test assertions); storyboard schema unchanged at 1.1; CLI mode count 3 → 4.

Suite state on this branch: contract tests **51/51** (42 + 7 preview + 2 overflow), root
suite **58/58**, `skills-ref validate` PASS, `MANIFEST.json` valid JSON, CI-equivalent smoke
test 4/4 (`h264,1280,720,yuv420p,30/1`; 2.000000 s; full decode clean; no audio streams),
and a framemd5 regression check — the same storyboard rendered by `40c8183`'s template and
by this one decodes to **60/60 byte-identical frames**. Not verified here: no new
topic-specific adapted copy was rendered (the generic template and its CLI are what
changed), and suggestion 2 was not implemented.
