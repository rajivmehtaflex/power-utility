# Water-cycle explainer — verification record

Run directory: `explainify-output/water-cycle-20261002-221531/` (rendered 2026-10-02).
Workflow: explainify `explainer-video` format, source = pasted text (frozen case C4 fixture in
`docs/superpowers/verification/explainify/cases.md`), provenance `kind: text`,
`retrieval_status: not-applicable`, all 7 claims `origin: provided-source`.

## Deliverables

- `water-cycle-explainer.mp4` — 558,851 bytes, SHA-256 `ef1bd974c1c4610ab0791be9b524dcb97c7bb1e3c9d2552ac3f78e10ff48a7f5`
- `water-cycle-render.py` — topic-adapted copy of `scripts/render_video.py` (inline PEP-723 deps, embedded schema, guard behavior preserved)
- `water-cycle-storyboard.json` — 7 scenes, full teaching brief, 40.0 s total
- `water-cycle-verification.md` — this file

## Stream and decode checks (§7)

| Check | Expected | Observed | Result |
|---|---|---|---|
| Codec | h264 | h264 | pass |
| Dimensions | 1280×720 | 1280×720 | pass |
| Frame rate | 30/1 | 30/1 | pass |
| Pixel format | yuv420p | yuv420p | pass |
| Audio streams | 0 | 0 | pass |
| Duration | 40.0 s ± 1 frame + 0.01 s | 40.000000 s (1200 frames) | pass |
| Full decode | no errors | `ffmpeg -v error -f null -` exit 0, empty stderr | pass |

## Scene and frame inspection (§7)

16 frames extracted (one representative per scene after key information appeared, early/late
pairs for scene 3, pre-rain and rain states for scene 4, and two transition pairs). Every
frame inspected visually; verdicts **11/11 PASS** across the final inspected set, with the
programmatic audit covering all 16:

- All on-screen text legible, nothing clipped at frame edges (edge-margin audit: all four
  bands at background level in every frame).
- No overlapping or colliding elements (one cosmetic case: the formed cloud overlaps the
  dashed "colder air" box boundary in scene 3 — cosmetic, no text impact).
- No machine-learning artifacts anywhere (no token boxes, attention matrices, or equations) —
  this is the anti-stale-assumption proof case.
- Visuals match each scene's teaching intent: sun + evaporation, cloud formation from
  droplets, drops merging then falling as rain AND snow (disjunction preserved on screen),
  ground soak + river return, closed loop diagram, ice + underground storage.
- Transitions are clean fades: end states fully drawn while dimming, new scenes fade in with
  content (not blank).

Repair cycles used: 1 (scene-1 fade timing adjusted; `s1-*-v2` frames are post-repair).

## Teaching checks (§7)

- Learning objective met: the seven-step cycle is presented in order with prerequisites
  (states of water implied by vapor/drops/rain/snow) introduced before use.
- Preserved meaning vs the C4 source (side-by-side):
  - "it does not have a starting point" → scene 6 verbatim. 
  - "never perfectly closed, because water can stay stored in ice and underground for long
    periods" → scene 7 verbatim (three-line layout).
  - "fall as rain or snow" → scene 4 keeps the disjunction (labels `rain` and `snow` both shown).
  - "Some of this water soaks into the ground, and some flows back to the ocean in rivers" →
    scene 5 keeps the partial split ("Some … Some …") with both paths drawn.
- Rendered captions equal the storyboard `on_screen_text` byte-for-byte for all inspected scenes.
- No added factual claims beyond the source; omissions field lists what the paragraph does not
  cover and the video excludes.

## Runtime versions

uv 0.12.21 · Python 3.12.10 · numpy 2.5.3 · matplotlib 3.11.2 · jsonschema 4.26.0 ·
ffmpeg 9.0.2 with `h264_videotoolbox` encoder (rendered on macOS arm64).

## Reproduction

```text
uv run explainify-output/water-cycle-20261002-221531/water-cycle-render.py \
  --storyboard explainify-output/water-cycle-20261002-221531/water-cycle-storyboard.json \
  --output <new-path>.mp4
```

Output path must not already exist unless `--overwrite` is explicitly passed (guard verified:
exit 1 with a readable error, existing file untouched).

## Limitations

This version produces silent video. Source coverage = the pasted C4 paragraph only; anything
outside it is out of scope by design. Bit-exact reproduction is encoder/machine-dependent
(VideoToolbox H.264 on this host); the recorded version set above is the reproducibility record.
