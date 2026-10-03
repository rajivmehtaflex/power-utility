# Ring attention explainer video — verification record

Run directory: `explainify-output/ring-attention-20261003-083306/` (repo: `power-utility`, branch `main`, uncommitted tree)
Produced: 2026-10-03. Evaluation case C1, PART B (`explainer-video` format). Source: topic `ring attention`, model-knowledge origins, no retrieval.

Artifacts in this directory:

- `ring-attention-storyboard.json` — storyboard with embedded teaching brief (8 scenes, 39.50 s total).
- `ring-attention-render.py` — adapted copy of `repo-owned/explainify/scripts/render_video.py`
  (EMBEDDED_SCHEMA untouched; CLI, validation, encoding, and output guard unchanged; added a
  pre-render guard that checks every scene id has a handler and dry-draws all scenes at five
  progress values before encoding).
- `ring-attention-explainer.mp4` — the delivered video (silent).
- `frames/` — 14 extracted verification PNGs (post-repair render).
- `ring-attention-explainer-attempt1.mp4` + `frames-attempt1/` — first-attempt render and its
  frames, retained as repair diagnostics (see §5).

## 1. Teaching checks

- **Learning objective met?** Yes. The video shows, in order: attention needs every query to
  meet every key and value → the whole sequence's keys/values outgrow one device's memory →
  cut the sequence into shards, one per device, devices linked in a ring → queries stay put,
  key/value blocks travel → centerpiece: blocks hop around the ring in lockstep; every device
  attends to each visiting block (coverage dots fill, partial-result bars grow, arrival
  flashes) → after one loop every device has full coverage with nothing replicated → closing:
  attention itself is unchanged, only the arrangement changes. That is the one mechanism the
  brief selected (KV blocks travel the ring while queries stay local).
- **Prerequisites introduced before use?** Yes. Attention/query-key-value is introduced in
  scene 2 (caption "attention: every query must meet every key and every value" plus all-pairs
  arcs) before the memory problem (scene 3) and the ring mechanism (scenes 4–6). "One device's
  memory" is introduced in scene 3 before devices appear in scene 4; Q/K/V role letters appear
  from scene 3 onward ("Q", "K", "V") and are anchored by the scene-5 legend ("queries — stay
  on their device", "key/value blocks — travel the ring").
- **Qualifications preserved?** Yes. On screen: scene 3 footer "qualitative — no sizes
  claimed"; scene 4 footer "illustrative layout: 4 devices"; scene 8 caveat "communication
  costs, schedules, and implementations not covered" and footer "layout illustrative · silent
  · rendered locally". In the brief: all 9 claims carry `origin: model-knowledge`; the
  single-device equivalence claim keeps its "exact arithmetic / floating-point rounding"
  qualification; the four-device layout is marked illustrative in `claim-shard`, the example,
  `must_preserve`, and `omissions`.
- **Mechanism correct?** Yes. Scene order matches brief mechanism steps 1–8: all-to-all
  requirement → KV outgrows one device → shard per device → ring layout with neighbor-only
  links → queries local → lockstep send/receive each step → attend-and-accumulate per visit →
  one full loop gives every device every block. The storyboard example arithmetic checks:
  4 shards; each device sees its own 1 + 3 received = 4 blocks; each block makes 3 hops
  (`hops: 3` in scene data) — one full loop suffices.
- **Example arithmetic consistent?** The worked example is the illustrative four-device
  layout (value_origin `illustrative`); its calculation (1 + 3 = 4, 3 hops) is consistent
  with the animation, which performs exactly three hops and fills four coverage dots per
  device. No numeric outputs (scores, weights, timings) exist to check.
- **Values labeled illustrative?** Yes — in the brief (`example.value_origin`,
  `claim-shard`/`claim-visit` qualifications, `must_preserve`) and on screen (scene 3 and
  scene 4 footers; closing footer "layout illustrative").

### On-screen number audit (the C1 guard: no unsupported numerical or performance claims)

Every numeral that appears anywhere in the 39.5 s video, with justification:

| # | Numeral(s) | Where | Justification |
|---|---|---|---|
| 1 | `1`–`4` inside device labels `D1`…`D4` | scenes 4, 5, 6, 7 | Illustrative layout identifiers for the four-device ring. Declared illustrative: `claim-shard` qualification, `must_preserve` item 3, example `value_origin: illustrative`, and the on-screen scene-4 footer "illustrative layout: 4 devices". Not a measurement, recommendation, or benchmark. |
| 2 | `4` in the scene-4 footer "illustrative layout: 4 devices" | scene 4 footer | Same illustrative-layout declaration; names the made-up layout value on screen as required. |

No other digits appear in any inspected frame (each frame report enumerated all visible
numerals; only D1–D4 and the scene-4 footer digit exist). There are **no** context-window
multipliers, FLOPs, memory-savings figures, throughput numbers, benchmark results, or counts
of tokens/parameters anywhere. All size statements are qualitative ("a long sequence… outgrow
one device's memory", "no single device can hold", "nothing replicated"). Ordinal words
("one loop", "one shard per device") are qualitative counts of the mechanism, not
performance claims.

## 2. Scene-check table (14 frames extracted, 14 inspected)

Frame times are stream times; scene spans are cumulative from the storyboard.

| Scene (id) | Span (s) | Frame inspected | Finding |
|---|---|---|---|
| title | 0.0–4.0 | `frame-title.png` @ 3.6 s | PASS. Large white "Ring attention", blue two-line hook with correct em-dashes, decorative four-dot ring with arrows complete; footer note "silent · rendered locally"; no clipping/overlap. |
| attention-needs-all | 4.0–9.0 | `frame-attention-needs-all.png` @ 8.4 s | PASS (after repair 1). All-pairs arcs now fan ABOVE the box row, below the caption with no contact on either side; ellipsis end-boxes render; note "one query must reach every key and every value" clear of the arcs; row centered. |
| kv-too-big | 9.0–13.5 | `frame-kv-too-big.png` @ 13.0 s | PASS. Dashed "one device's memory" boundary; yellow "Q" + "queries fit" inside; six blue KV bars inside the boundary; three red bars fully outside to the right with red "too large for one device" tag; footer "qualitative — no sizes claimed"; no overlap, nothing clipped. |
| shard-ring | 13.5–19.0 | `frame-shard-ring.png` @ 18.5 s | PASS (re-checked after arrowhead tweak). Four-segment "one long sequence" bar with dashed cut lines; each colored segment's K/V chip sits inside its matching-color device; D1–D4 labels clear; ring arrows form a closed loop with visible arrowheads; footer "illustrative layout: 4 devices". |
| queries-local | 19.0–23.0 | `frame-queries-local.png` @ 22.5 s | PASS (re-checked). Q tiles inside all four device boxes; K/V chips between devices without touching boxes or tiles; legend at lower left legible, no collision with the ring; arrowheads visible; digits only in D1–D4. |
| shard-journey | 23.0–30.0 | `frame-journey-hop.png` @ 25.0 s | PASS (after repair 1). Mid/late-hop state: chips on the ring path, tracked white-bordered chip identifiable; per-device dot counts match the schedule (top/right 1, bottom/left 2 filled at this instant); no chip covers a Q tile or label; nothing clipped. |
| shard-journey (arrival) | — | `frame-journey-arrival.png` @ 26.55 s | PASS (after repair 1). Post-arrival: each device holds exactly one resting chip beside its Q tile with a clear 6–10 px gap (repair verified on all four devices); yellow arrival flash present; dot counts stepped correctly; bars partially green. |
| shard-journey (complete) | — | `frame-journey-complete.png` @ 29.4 s | PASS (after repair 1). All coverage dots filled with white glow edges, all partial bars fully green, chips seated with gaps, yellow line "after one loop: every query has met every block" clear of caption and top device box. |
| full-loop | 30.0–35.0 | `frame-full-loop.png` @ 34.5 s | PASS (re-checked). Compact ring complete; three payoff lines stacked, centered, separated: white "full attention over the whole sequence", yellow "no device ever held the whole key/value data", grey italic "queries stayed home; the key/value blocks made one loop"; faded chips between devices; no overlap with ring or labels. |
| closing | 35.0–39.5 | `frame-closing.png` @ 38.8 s | PASS. "attention itself is unchanged —" / "only the arrangement changes" (em-dash renders, no missing glyphs); caveat and footer "layout illustrative · silent · rendered locally" legible; no clipping/overlap. |
| transition 1 (title → attention) | ~4.0 s | `frame-trans1a-out.png` @ 3.95 s, `frame-trans1b-in.png` @ 4.15 s | PASS. End state complete and stable; 0.15 s into scene 2 the background is clean, caption readable, boxes popping in staggered, no title-scene residue. (Scenes 1 and early 2 are unchanged code from attempt 1; appearance identical.) |
| transition 2 (journey → full-loop) | ~30.0 s | `frame-trans2a-out.png` @ 29.93 s, `frame-trans2b-in.png` @ 30.13 s | PASS (post-repair render). Scene-6 end state complete and stable; 0.13 s into scene 7 no residue (no yellow line, no dot rows, no large boxes), caption and staggered pop-in under way. |

Frame-inspection method note: in this session the image-reading path surfaces each extracted
frame through the environment's image pipeline; every frame was inspected at full 1280×720
resolution through that pipeline with the checklist above (legibility, clipping, collisions,
label correctness, numeral audit, agreement with the brief). All 14 frames were inspected;
scenes 1, 3, and 8 were verified on attempt 1 and are byte-identical code paths in the
repaired render (the repair touched only scene-2 arc sign, Q-tile/block offsets in scenes
5–7, and ring-arrow head size), so those inspections carry over.

Minor observations (not defects): the small grey run-title header, scene tags, and progress
bar are intentionally low-contrast furniture inherited from the template style; one arrowhead
on the left ring segment reads faintly at one instant — the circulation direction remains
clear from the other three arrowheads and the block motion.

## 3. Stream and decode checks (§7.2, §7.3) — final render

| Check | Expected | Observed | Result |
|---|---|---|---|
| Codec | h264 | `codec_name=h264` | PASS |
| Dimensions | 1280×720 | `width=1280`, `height=720` | PASS |
| Frame rate | 30/1 | `r_frame_rate=30/1` | PASS |
| Pixel format | yuv420p | `pix_fmt=yuv420p` | PASS |
| Audio streams | none | 0 audio streams | PASS |
| Duration | 39.50 s ± 1 frame + 0.01 s | `duration=39.500000`, `nb_frames=1185` (storyboard total 39.50 s) | PASS |
| Full decode | empty stderr | `ffmpeg -v error -i … -f null -` → empty output, exit 0 | PASS |

Pre-render checks (both renders): `--check-only` on the installed template and on the adapted
copy (8 scenes, 39.50 s), `--self-test` in-memory fixture, and the adapted copy's pre-render
guard (every scene id has a handler; every scene dry-draws at progress 0/0.25/0.5/0.75/1
without errors). The adapted copy was diffed against the template before first execution:
only the module docstring, the patches import, the topic drawing section, and the pre-render
guard call differ; a scan for file writes, network calls, and shell execution found only the
template-inherited read-only JSON load, the `ffmpeg -encoders` preflight, and the single
`animation.save` to the chosen output path. Storyboard fields are used only as data.

## 4. Runtime versions (exact, from the render environment)

- uv 0.12.22 (Homebrew 2026-10-01 aarch64-apple-darwin)
- Python 3.12.10 (uv-managed)
- numpy 2.5.3 (constraint `>=1.26,<3`)
- matplotlib 3.11.2 (constraint `>=3.8,<4`)
- jsonschema 4.26.0 (constraint `>=4,<5`)
- ffmpeg version 9.0.2 Copyright (c) 2000-2026 the FFmpeg developers (`/opt/homebrew/bin/ffmpeg`); encoder selected by preflight: `h264_videotoolbox`
- ffprobe from the same ffmpeg 9.0.2 build (`/opt/homebrew/bin/ffprobe`)

## 5. Repair cycles: 1 of at most 2

Attempt 1 passed all stream/decode checks and taught the content, but frame inspection found
two cosmetic defects:

1. Scene 2: the all-pairs arcs bowed BELOW the token row, while the storyboard's
   `visual_intent` says "above the row" (no overlap resulted, but the render disagreed with
   the storyboard data).
2. Scenes 5–7: at rest, the traveling K/V chip touched or slightly overlapped the corner of
   the adjacent yellow Q tile inside the device boxes (~6–10 px), violating the no-collision
   rule; ring-arrow heads were also small enough that one report missed them.

Repairs (single cycle): flipped the arc curvature sign in scene 2; moved/shrank the Q tile
(0.40 → 0.36 at x−0.32) and shifted the resting chip offset (+0.18 → +0.21) with tracked
scale 1.12 → 1.06 and normal 1.0 → 0.95; enlarged ring-arrow heads (mutation scale 11 → 13).
The first attempt was retained as `ring-attention-explainer-attempt1.mp4` with
`frames-attempt1/`; the repaired render went to the canonical path as a new file (no implicit
overwrite; `--overwrite` was never used). Post-repair re-verification: ffprobe + full decode
re-run (§3), and every frame the repair could affect re-extracted and re-inspected — arcs now
above the row with caption clearance; Q-to-chip gaps verified on all four devices in both the
arrival and end states; arrowheads visible in scenes 4, 5, 6, and 7; transitions 2a/2b
re-checked clean. Both defects are resolved; result: PASS.

## 6. Reproduction

From the repository root (or from this bundle directory — the script embeds the schema and
its dependencies):

```text
uv run explainify-output/ring-attention-20261003-083306/ring-attention-render.py \
  --storyboard explainify-output/ring-attention-20261003-083306/ring-attention-storyboard.json \
  --output <new-path>.mp4
```

The output path must not already exist (the renderer refuses implicit overwrites; pass
`--overwrite` only for an explicit replacement).

Replay actually performed 2026-10-03 from the repository root (outside the run directory and
the installed skill) with the bundle's embedded schema and inline dependencies: rendered to a
temporary path, ffprobe duration 39.500000 s, and the decoded frames were md5-identical to
`ring-attention-explainer.mp4`. The temporary replay file was deleted afterward.

## 7. Limitations

- **Silent video.** This version produces no narration and no audio track, by design for
  v0.1. Narration is not tied to any particular service or API key.
- **Model-knowledge origin.** No external source was retrieved; every claim is
  `origin: model-knowledge` with qualifications in the storyboard brief, and no citation is
  claimed.
- **Illustrative layout.** The four devices, four shards, and three hops are made-up teaching
  values, declared illustrative in the brief and on screen; they are not a recommended or
  measured configuration.
- **Omissions** (stated in the brief; the closing scene names them on screen): training and
  load balancing for unequal shards; overlapping vs non-overlapping communication schedules
  and their costs; the exact partial-result merge arithmetic (online rescaling of attention
  weights); concrete implementations, hardware, benchmarks, or performance figures; causal
  masking for text-generation models.
- Scene inspection used 14 still frames (one or more per scene after key information
  appeared, plus two pairs around the 4.0 s and 30.0 s transitions); motion quality was
  assessed from the staggered/fade/hop design and the transition states, not from playback.
- Teaching-quality checks are reviewer-confirmed accuracy, sequencing, and legibility; no
  user-comprehension study was performed.
