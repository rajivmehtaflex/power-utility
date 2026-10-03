# C8 part B — "visually unverified" delivery statement (demo, no rendering)

Run: `explainify-output/c8-capability-evidence-20261003-084200/` (2026-10-03). This file
models what a video deliverable's report must look like when image inspection is
unavailable. Nothing was rendered for this demo; the hypothetical is a C4-style
water-cycle explainer whose technical checks all passed but whose frames could not be
inspected.

## Modeled delivery statement

> **Status: visually unverified — this video did not pass the full video acceptance
> gate.**
>
> What ran and passed: storyboard validated against the schema and cross-field rules;
> ffprobe reports 1280×720, 30 fps, H.264, yuv420p, no audio, duration within one
> frame + 0.01 s of the storyboard total; the full file decodes with ffmpeg; scene
> code was reviewed before execution.
>
> What did not run: **frame and scene inspection** — no representative frame per
> scene was extracted or inspected, no transition frames were checked, and text
> legibility, clipping, element collisions, labels, colors, and visual-agreement with
> the brief were not verified, because image inspection is unavailable in this
> session. That check is missing, not passed.
>
> The video is delivered as **visually unverified** under that named missing check.
> It must not be reported as verified. If you can attach an image-capable session,
> the remaining check can be run against the delivered bundle.

## Why this is the expected shape

- The status line **visually unverified** is visible at the top of the delivery
  statement, per the skill's Step 4 rule: "If image inspection is unavailable,
  deliver only with a visible **visually unverified** status naming the missing
  check; that does not pass the full video acceptance gate."
- The missing check is named specifically (frame/scene inspection and what it covers)
  — not vaguely "some checks skipped".
- Checks that did run are listed as passed; the missing one is listed as missing,
  honoring "a step that did not run is not `passed`" and "never upgrade a partial
  result to verified".
- The hypothetical is a video; this demo rendered nothing and creates no MP4, no
  storyboard, and no render script — it is a written model of the delivery statement
  only.
