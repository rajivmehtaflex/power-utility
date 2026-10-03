# Finding longitude at sea — explainer video verification record

Run directory: `explainify-output/longitude-20261003-083500/` (repo `power-utility`,
branch `main`, uncommitted tree). Produced 2026-10-03. Case C3 of the explainify §9
evaluation suite: UTF-8 `.md` file input, `explainer-video` format. Silent video.

Artifacts in this directory:

- `longitude-storyboard.json` — storyboard with embedded teaching brief (8 scenes, 37.50 s).
- `longitude-render.py` — adapted copy of `repo-owned/explainify/scripts/render_video.py`
  (EMBEDDED_SCHEMA byte-identical; CLI, validation, encoding, output guard unchanged; added
  topic scenes + pre-render handler/mathtext guard).
- `longitude-explainer.mp4` — the delivered video (repair attempt 1 retained below).
- `longitude-explainer-attempt1.mp4` — the first render, kept as the diagnostic file for the
  one repair cycle (a coin overlapped the "Jamaica" label in scene `trial-1761-1773`).
- `frames/` — 12 final verification PNGs + the pre-repair scene-6 frame
  (`attempt1-frame-trial-1761-1773.png`).

## Provenance (Step 1)

| Field | Value |
|---|---|
| source kind | `file` (UTF-8 `.md` file input) |
| requested_location | `/tmp/c3-fixture.md` |
| resolved_location | `/tmp/c3-fixture.md` |
| source_title | "Finding longitude at sea" (the fixture's own H1) |
| retrieval_status | `not-applicable` |
| retrieved_at | `null` |

- `retrieval_status` rationale: the file was read locally, in full — there was no retrieval
  step. The schema's `retrieval_status` describes how much of a *retrieved* source was
  obtained and `retrieved_at` is defined for *web* material; `cases.md` §2(a) prescribes
  `not-applicable` for the analogous fully-supplied pasted-text case. The same reasoning is
  applied here; nothing was partial.
- The input is a **frozen evaluation fixture** inlined in
  `docs/superpowers/verification/explainify/cases.md` case C3 (not a live user file). The
  materialized copy `/tmp/c3-fixture.md` (1,505 bytes) is byte-identical to the frozen block
  (`diff` clean against `cases.md` lines 82–106). A copy is stored at
  `docs/superpowers/verification/explainify/longitude-fixture.md`.
- **Fixture SHA-256:** `9f3ad6bb60ec76ba5a2735cddc20b7f5d119b35155fd7c66f2bd38a31b703aae`
- Claim origins in the storyboard: 9 claims `provided-source` (everything the fixture
  states), 1 claim `model-knowledge` (`claim-sea-motion-hard` — the pendulum contrast, not
  stated in the fixture, qualification says so and the scene carries an "illustrative"
  note), 1 claim `illustrative` (`claim-worked-example` — the 2-hour toy value). No
  invented citations; nothing is presented as a quotation.

## 1. Teaching checks

- **Learning objective met?** Yes. The one takeaway — knowing longitude = knowing time — is
  built step by step: scene `time-to-longitude` shows the reference-meridian clock vs the
  ship's clock with the red "time difference" arrow and the rule `1 hour = 15 degrees`
  (frame-verified); scene `payoff` closes the chain keep time → compare → turn the
  difference into degrees, with the worked example and the check line
  `360° / 24 h = 15° per hour` (frame-verified, equations transcribed exactly).
- **Prerequisites introduced before use?** Yes. Clock faces appear (scenes 3, 5, 8) before
  any hour arithmetic; the check line stating `360° / 24 h` supplies the "full circle 360°,
  24 hours" prerequisite at the moment the 15°-per-hour rule is used.
- **Qualifications preserved?** Yes — see the preserved-elements tables below. The
  uncertainty is NOT flattened: scene `uncertainty` shows "Decades of service: still not
  known" / "may vary with oil, temperature, and care" (frame-verified); scene
  `trial-1761-1773` keeps "the largest reward / was not paid at once" in red
  (frame-verified).
- **Mechanism correct?** Yes. Brief mechanism steps 1–3 (keep the reference meridian's time
  at sea → compare with the ship's time → turn the difference into degrees at 15°/hour)
  match the scene order and the fixture's own recipe ("keep time at sea, compare it with
  the reference meridian, and turn the difference into degrees").
- **Worked-example arithmetic checked?** Yes, by hand and on screen: 360 ÷ 24 = 15 (the
  fixture's own rule, restated); 2 × 15 = 30. The on-screen forms
  `$2 \times 15^\circ = 30^\circ$ west` and `360° / 24 h = 15° per hour` were transcribed
  from the rendered frame and match exactly.
- **Values labeled illustrative?** Yes. `example.value_origin: "illustrative"` in the brief;
  the payoff scene shows the label "illustrative example" above the panel and the corner
  note "illustrative example · silent video" (frame-verified); the pendulum contrast in
  scene `sea-clock` carries the corner note "pendulum contrast — illustrative".
- **Every added factual claim has an honest origin?** Yes — the only added claims are
  `claim-sea-motion-hard` (model-knowledge, flagged as not-in-fixture) and
  `claim-worked-example` (illustrative). Everything else is `provided-source`.

### Dates on screen vs fixture (must match exactly)

| Fixture statement | On-screen rendering (frame-verified) | Frame | Match |
|---|---|---|---|
| "In 1714 the British Parliament passed the Longitude Act." | Scene title "1714: the Longitude Act offers rewards"; act box "Longitude Act" with large "1714" | `frame-act-1714.png` @ 8.2 s | Exact |
| "H4, sailed toward Jamaica in 1761" | Scene title "1761: H4's trial error is small enough"; timeline year "1761"; "H4 sails toward Jamaica" + "Jamaica" label | `frame-trial-1761-1773.png` @ 28.8 s | Exact |
| "payments continued in stages until 1773" | Scene title "not paid at once — in stages until 1773"; timeline year "1773"; "payments continued in stages" | `frame-trial-1761-1773.png` @ 28.8 s | Exact |

### Negations and uncertainty on screen vs fixture

| Fixture phrase | On-screen rendering (frame-verified) | Class |
|---|---|---|
| "could not find their longitude at sea reliably" | Scene `problem`: "For centuries: latitude found — longitude not" + red label "longitude / could not be found reliably" | negation |
| "never convenient for every navigator" | Scene `lunar-distances` footer "never convenient for every navigator" (red, italic) | negation |
| "did not pay the largest reward at once" | Scene `trial-1761-1773`: "the largest reward / was not paid at once" (red) + title "not paid at once — in stages until 1773" | negation |
| "does not depend on the weather" | Scene `payoff` footer "does not depend on the weather — probably decisive" | negation + uncertainty |
| "is still not known" | Scene `uncertainty` title "Decades of service: still not known" | uncertainty |
| "may vary with oil, temperature, and care" | Scene `uncertainty` subtitle "may vary with oil, temperature, and care" + tags "oil" / "temperature" / "care" | uncertainty |
| "within half a degree" | Scene `act-1714` box line "within half a degree" (green, bold) + "half-degree band" around the West Indies destination | condition |

### Illustrative-arithmetic check (shown on screen)

- Fixture rule (provided-source): one hour of difference equals fifteen degrees.
- Check: Earth turns 360° in 24 h → 360 / 24 = 15 degrees per hour. On screen:
  `360° / 24 h = 15°` (scene 3) and `360° / 24 h = 15° per hour` (scene 8).
- Worked example (illustrative, labeled): ship clock 2 h behind the reference meridian →
  2 × 15° = 30° west. 2 × 15 = 30 is correct; the 2-hour value is a toy value, not from
  the fixture, and is labeled illustrative on screen.

## 2. Scene-check table (12 frames extracted from the delivered MP4, 12 inspected)

| Scene (id) | Span (s) | Frame inspected | Finding |
|---|---|---|---|
| problem | 0.0–4.0 | `frame-problem.png` @ 3.8 s | PASS. Title, blue hook, solid blue latitude line with label, sun + stars, ship on horizon, red dashed longitude line with "?" and two-line red label; no clipping/overlap. |
| act-1714 | 4.0–8.5 | `frame-act-1714.png` @ 8.2 s | PASS. Act box with "Longitude Act" and large "1714"; three condition lines including green bold "within half a degree"; route arc Britain → West Indies with green half-degree band; year is exactly 1714; no defects. |
| time-to-longitude | 8.5–14.5 | `frame-time-to-longitude.png` @ 14.1 s | PASS. Earth circle with spokes; green reference meridian + clock reading 12; ship on yellow meridian + clock reading 1 (a 1-hour difference); red "time difference" arrow; right panel with `1 hour = 15 degrees` and `360° / 24 h = 15°` transcribed exactly. Minor observation (not a defect): the red arrow crosses the Earth circle's upper-left spokes without covering any text. |
| lunar-distances | 14.5–18.5 | `frame-lunar-distances.png` @ 18.2 s | PASS. Moon with crater, stars, lens icon + "hours of calculation", clouds + "needs a clear sky", cloud over the Moon, red italic footer "never convenient for every navigator" fully visible; no defects. |
| sea-clock | 18.5–23.5 | `frame-sea-clock.png` @ 23.2 s | PASS. Green land clock with near-vertical steady pendulum; blue waves, tilting ship, red sea clock with pendulum thrown wide (contrast reads clearly); Harrison captions; corner note "pendulum contrast — illustrative"; no defects. |
| trial-1761-1773 | 23.5–29.0 | `frame-trial-1761-1773.png` @ 28.8 s (re-inspected after repair 1) | PASS after repair. Years exactly 1761 and 1773; green "recorded error small enough / to meet the Act's condition"; staged coins with "in stages"; red "the largest reward / was not paid at once"; ship + fully legible "Jamaica". |
| uncertainty | 29.0–32.5 | `frame-uncertainty.png` @ 32.3 s | PASS. H4 box with yellow bezel, grey "?", faint years axis labeled "years of ordinary service", tags exactly "oil" / "temperature" / "care"; no defects. |
| payoff | 32.5–37.5 | `frame-payoff.png` @ 37.2 s | PASS. Three chained boxes; example panel labeled "illustrative example" with clock "2 h behind" and `2 × 15° = 30° west`; check line `360° / 24 h = 15° per hour`; footer "does not depend on the weather — probably decisive"; corner note "illustrative example · silent video"; no defects. |
| transition 1 (problem → act) | ~4.0 | `frame-trans1a-problem-out.png` @ 3.95 s, `frame-trans1b-act-in.png` @ 4.15 s | PASS. End state complete and stable; 0.15 s into scene 2 the background is clean with no residual scene-1 content; only furniture + title visible, act elements popping in later by design. |
| transition 2 (sea-clock → trial) | ~23.5 | `frame-trans2a-seaclock-out.png` @ 23.45 s, `frame-trans2b-trial-in.png` @ 23.65 s | PASS. Sea-clock end state fully populated and stable (wide red pendulum visible); 0.15 s into scene 6 no residue, timeline arrow already drawn, year markers not yet popped (matches the 1.0 s stagger). |

Minor observation (not a defect): the small grey run-title header, scene tags, and progress
bar are intentionally low-contrast furniture inherited from the template's style guide; all
learner-facing primary text is white/yellow/green/red and large.

## 3. Repair cycles

- **Repair 1 (of at most 2) — used.** First render: in scene `trial-1761-1773`, a staged
  payment coin overlapped the end of the "Jamaica" label (read as "Jamaic"); found by frame
  inspection (`attempt1-frame-trial-1761-1773.png`). Cause fixed in
  `longitude-render.py`: ship icon moved (5.05, 4.18) → (4.55, 4.35) and the "Jamaica"
  label (5.05, 3.68) → (4.55, 3.95), clear of the coins at x = 5.3/6.6/7.9 and of the
  "1761"/"in stages" labels. The first attempt was retained as
  `longitude-explainer-attempt1.mp4`; the repaired video was rendered to the fresh path
  `longitude-explainer.mp4` (no implicit overwrite). Re-checks run after the repair:
  storyboard `--check-only` (unchanged), full ffprobe (§4), full decode (§4), and fresh
  frame extraction + visual inspection of the repaired scene (PASS, "Jamaica" fully
  visible, no new collisions). Scene durations were untouched, so other scenes' spans and
  drawings are unchanged.

## 4. Stream and decode checks

| Check | Expected | Observed | Result |
|---|---|---|---|
| Codec | h264 | `codec_name=h264` | PASS |
| Dimensions | 1280×720 | `width=1280`, `height=720` | PASS |
| Frame rate | 30/1 | `r_frame_rate=30/1` | PASS |
| Pixel format | yuv420p | `pix_fmt=yuv420p` | PASS |
| Audio streams | none | 0 audio streams | PASS |
| Duration | 37.50 s ± 1 frame + 0.01 s | `duration=37.500000`, `nb_frames=1125` (storyboard total 37.50 s) | PASS |
| Full decode | empty stderr | `ffmpeg -v error -i … -f null -` → exit 0, empty output | PASS |

Pre-render checks passed before encoding: `check_env.py --format explainer-video` preflight
exit 0; `--check-only` on both the installed template and the adapted copy (8 scenes,
37.50 s); `--self-test`; and the adapted copy's guard (every scene id has a handler; every
scene draws cleanly at progress 0/0.25/0.5/0.75/1 without errors). The adapted copy was
inspected before execution: diff against the template shows changes only in the module
docstring, the patch imports, the topic scene-drawing section, and the pre-render guard;
EMBEDDED_SCHEMA and the entire CLI/validation/encoding section are byte-identical; a scan
for file writes, network calls, and shell execution found only the template-inherited
read-only JSON loading, the `ffmpeg -encoders` preflight, and the single `animation.save`
to the chosen output path.

## 5. Runtime versions (exact, from the render environment)

- uv 0.12.22 (Homebrew 2026-10-01 aarch64-apple-darwin)
- Python 3.13.14 (uv-managed, resolved from the script's inline PEP-723 metadata)
- numpy 2.5.3 (constraint `>=1.26,<3`)
- matplotlib 3.11.2 (constraint `>=3.8,<4`)
- jsonschema 4.26.0 (constraint `>=4,<5`)
- ffmpeg version 9.0.2 (`/opt/homebrew/bin/ffmpeg`); encoder selected by preflight:
  `h264_videotoolbox`
- ffprobe from the same ffmpeg 9.0.2 build (`/opt/homebrew/bin/ffprobe`)

## 6. Reproduction

From the repository root (or from this bundle directory — the script embeds the schema and
declares its dependencies, and imports nothing from the installed skill):

```text
uv run explainify-output/longitude-20261003-083500/longitude-render.py \
  --storyboard explainify-output/longitude-20261003-083500/longitude-storyboard.json \
  --output <new-path>.mp4
```

The output path must not already exist (the renderer refuses implicit overwrites; pass
`--overwrite` only for an explicit replacement).

## 7. Limitations

- **Silent video.** This version produces no narration and no audio track, by design for
  v0.1. No narration service is implied or required.
- **Illustrative values.** The 2-hour ship-clock offset, the resulting 30°, the wave and
  pendulum motions, and the schematic Sun/stars/Moon/Earth drawings are teaching aids, not
  measurements; the example and the pendulum contrast are labeled illustrative on screen.
- **Omissions** (stated in the brief): Harrison's biography and H1–H3; the lunar-distance
  calculation itself; reward amounts and Board of Longitude politics; how H4 was built and
  the exact size of its recorded 1761 error; other period methods.
- Scene inspection used 12 still frames from the delivered file (one per scene after key
  content appeared, plus two pairs around the 4.0 s and 23.5 s transitions); motion quality
  was assessed from the staggered/fade design, the pendulum/wave animation model, and the
  transition end-states, not from playback.
- Teaching-quality checks are reviewer-confirmed accuracy, sequencing, and legibility; no
  user-comprehension study was performed.
