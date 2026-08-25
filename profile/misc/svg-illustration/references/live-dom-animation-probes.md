# Live-DOM Animation Probes for SMIL SVGs

How to prove a *running* SMIL scene animates correctly — wheels spin in place, grips hold,
nothing orbits — when screenshot pixel-probes fail. Proven on two full builds
(pelican-on-bicycle, giraffe-in-tiny-car).

## Why not screenshots

Pixel-probing a browser screenshot of an animated SVG fails for three compounding reasons:

1. **Unknown chrome offset/scale** — the capture includes browser UI; the SVG's (0,0) is
   not the image's (0,0), and scale isn't inferable from image size alone. (Landmark
   calibration helps but still drifted: sun centroid gave offset (8,4) at 1:1, yet probes
   kept missing.)
2. **Animation phase is unknown** — every coordinate on a moving part (muzzle under nod,
   pedal under crank) is sampled at a random phase; expected values become tolerance
   envelopes, weakening the test.
3. **Anti-aliasing + overlapping layers** — a tire bottoming ON its shadow band blends
   toward the shadow color; strict color-match probes false-fail (real case: #333333 tire
   read as (90,90,90) over the shadow band).

Use screenshots only for gestalt vision checks ("does it look like a giraffe driving"),
never for transform-conflict proofs.

## The probe: browser_console getBoundingClientRect, sampled twice

After `browser_navigate(file://...svg)` (console runs on the ACTIVE tab of that session —
if it answers from `about:blank`, re-navigate first):

```js
(async () => {
  const svg = document.querySelector('svg');
  if (!svg) return 'NO SVG: ' + location.href;
  const grab = () => {
    const out = {};
    svg.querySelectorAll('circle[r="28"]').forEach((c,i) => {
      const r = c.getBoundingClientRect();
      out['wheel'+i] = {left:+r.left.toFixed(1), bottom:+r.bottom.toFixed(1)};
    });
    svg.querySelectorAll('ellipse[fill="#3d3d3d"]').forEach((e,i) => {
      const r = e.getBoundingClientRect();
      out['hoof'+i] = {cx:+(r.left+r.width/2).toFixed(1), cy:+(r.top+r.height/2).toFixed(1)};
    });
    return out;
  };
  const t0 = grab();
  await new Promise(res => setTimeout(res, 450));
  const t1 = grab();
  return JSON.stringify({t0, t1}, null, 1);
})()
```

Read the result against these signatures:

| Check | Healthy signature | Bug signature |
|---|---|---|
| Wheel orbit (SMIL replace-semantics) | wheel left/bottom IDENTICAL t0→t1 (sub-px bbox jitter only) | position changes every sample |
| Ground contact maintained | both wheels' `bottom` equal each other and constant | bottoms differ, or lift during bounce |
| Grip holds | hoof cx/cy constant at contract coords | drifting away from rim points |
| Part genuinely animating | bbox w/h oscillates while center stays pinned (steering wheel w 27↔25 at ±8°) | nothing changes = animation dead |

Notes:
- `getBoundingClientRect` returns VIEWPORT coordinates — absolute values include page
  offset; only DIFFERENCES between samples are meaningful. Don't assert absolute px.
- Rotating elements report axis-aligned bounding boxes: a spinning circle's w/h jitters
  sub-pixel while its center stays fixed — that jitter is itself evidence of rotation.
- If a selector matches nothing, diagnose with
  `{svgs: document.querySelectorAll('svg').length, ids: ['wheels','steering'].map(id=>!!document.getElementById(id))}`
  before concluding anything about the artwork.

## Layered QA doctrine (where this fits)

1. Static gates on source (coords, id dedup, timing anchors, rig-scope translate ban).
2. Frozen-frame renders (fixed freezer: direct attribute substitution with hard-fail;
   freeze rotation derived from the static arm's actual angle) + pixel probes for poses.
3. **Live DOM probes (this file)** — the only check that catches replace-semantics
   transform conflicts; frozen frames strip animations and silently restore base
   transforms, masking exactly this bug class.
4. Vision pass on the live render for gestalt only; settle vision-vs-math disputes with
   math/DOM, never the narrative.
