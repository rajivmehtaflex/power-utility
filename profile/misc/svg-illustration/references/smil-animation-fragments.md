# SMIL Animation Fragments for SVG Composites

Animation fragments are standalone `.svg` files containing only SMIL animation
elements (`<animate>`, `<animateTransform>`, `<animateMotion>`) — no `<svg>`
wrapper, no root `</svg>` close. They target element IDs defined in other
fragments and are merged into the final composite during assembly.

## File structure

```xml
  <!-- WHEEL SPIN: rear wheel (hub at cx, cy) -->
  <animateTransform
    attributeName="transform"
    type="rotate"
    from="0 cx cy"
    to="360 cx cy"
    dur="0.8s"
    repeatCount="indefinite"/>

  <!-- LEG IK: rear leg (12 keyframes, walking cycle) -->
  <animate
    attributeName="d"
    values="M...;M...;...;M..."
    keyTimes="0;0.083;0.167;...;1"
    calcMode="linear"
    dur="1.6s"
    repeatCount="indefinite"/>
```

Key rules:
- Multiple root elements are expected — do NOT wrap in `<svg>`. Passing through
  `xmllint --noout` will fail with "Extra content at the end of the document"
  for fragments; this is normal. Validate by wrapping in a temporary `<svg>` tag
  or by assembly verification.
- All `dur` values across rotating parts MUST match so they never phase-drift.
  Wheel spin, crank rotation, and leg cycles share one `dur` (typically 1.6s or
  0.8s depending on the mechanism).
- Animation fragments do NOT contain visual elements — only `<animate>`,
  `<animateTransform>`, and `<set>` elements. Visual geometry lives in
  structural fragments (02–06).

## Wheel spin animation

Both wheels rotate at the same rate about their hub centers:

```xml
<animateTransform attributeName="transform" type="rotate"
  from="0 200 510" to="360 200 510" dur="0.8s" repeatCount="indefinite"/>
```

The hub coordinates (200, 510) and (600, 510) correspond to the rear and front
wheel centers, respectively. `dur="0.8s"` makes wheels spin at 2× the crank
speed (crank dur=1.6s), so the pedals complete one full rotation per wheel
rotation — correct for a direct-drive bicycle.

## Crank rotation animation

The crank-pedals group rotates about the bottom bracket (430, 390):

```xml
<animateTransform attributeName="transform" type="rotate"
  from="0 430 390" to="360 430 390" dur="1.6s" repeatCount="indefinite"/>
```

This group must exist as `<g id="crank-pedals">` in a structural fragment before
the animation fragment targets it. The animation element is applied to the group
by the assembler or by the user explicitly adding it inside that `<g>`.

## Leg IK keyframe animation (phase-shifted front leg)

Rear and front legs use `<animate attributeName="d">` with 12 keyframe paths.
The front leg is phase-shifted by π (180°) — offset by 6 frames in the 12-frame
cycle — so the feet are always on opposite pedals.

### Computing the phase offset in Python

```python
rear_leg_values = [...]  # 12 path strings from rear leg
offset = len(rear_leg_values) // 2   # 6 for 12 frames = π offset
front_leg_values = rear_leg_values[offset:] + rear_leg_values[:offset]
```

Both legs share the same `keyTimes` string and `dur`. The `keyTimes` for N=12
frames are: `0;0.083;0.167;0.25;0.333;0.417;0.5;0.583;0.667;0.75;0.833;1`.

### Cyclic keyframe construction

The rear leg traces a walking cycle: the leg lifts (toe rises), swings forward,
and plants. The front leg is always in the opposite phase — when the rear foot
is planted, the front foot is lifted, and vice versa. The 6-frame offset
guarantees this mathematically: frame k of the rear leg equals frame (k+6) of
the front leg.

### Phase-shift verification

Validate the cyclic shift by asserting:
- `front_leg_values[0]` == `rear_leg_values[6]` (front frame 0 = rear frame 6)
- `front_leg_values[6]` == `rear_leg_values[0]` (front frame 6 = rear frame 0)
- `len(front_leg_values) == len(rear_leg_values)` (same count)

This catches Python list-aliasing bugs where `front = rear` (same reference) or
`front[:] = rear` was intended but `front = rear` was written instead.

## Assembly into composite SVG

Animation fragments are appended AFTER all structural fragments and BEFORE the
closing `</svg>` tag. The concat order is:

```
01-header-bg.svg  (defs, style, <svg> open tag)
02-rear-layer.svg
03-mid-layer.svg
...
07-animations.svg (FX layer - may hold both animation + final FX)
08-animations.svg (SMIL animations — wheels, crank, legs)
</svg>  (closing tag, echoed separately)
```

Multiple animation fragments are OK — they all contribute animation elements to
the same `<svg>` namespace. The assembler concatenates them in numeric order.

## Pitfalls

- **Fragment without `<svg>` wrapper fails xmllint as standalone** — expected,
  not broken. The assembler handles this; do not add a wrapper "just to make
  xmllint happy".
- **Mismatched `dur` across rotating parts causes phase drift** — wheel spin
  (0.8s) and crank (1.6s) share a 1:2 ratio intentionally, but ALL leg keyframe
  animations and the crank MUST share the same `dur` (`1.6s`) so they stay
  synchronized.
- **Animation targets non-existent IDs** — if `crank-pedals` or leg path IDs
  don't exist yet (their structural fragment hasn't been assembled), the
  animation will have no effect. Always verify target IDs exist in the assembled
  SVG before testing.
- **Keyframe count / keyTimes count mismatch** — `values` has N semicolons
  (N-1 separators for N keyframes) but `keyTimes` must have exactly N entries
  separated by N-1 semicolons. Mismatch silently breaks the animation.
- **`animateTransform` with existing `transform` on target group** — the
  animation replaces the `transform` attribute at render time; do not add a
  static `transform="..."` to the target group alongside the animation, or the
  static value is overridden.
- **REPLACE-semantics orbit bug (real defect class, user-visible):** a wheel group
  with `transform="translate(hub)"` + `<animateTransform type="rotate" from="0 hubx huby">`
  loses the translate during live playback — the wheel (drawn at local 0,0) ORBITS the
  hub point across the scene. Fix: nest — outer `<g transform="translate(hub)">`, inner
  `<g>` carrying `rotate from="0 0 0" to="360 0 0"`. **Frozen-frame QA cannot catch this:**
  snapshots strip animations, silently restoring the static transform and looking perfect.
  Always add a LIVE browser-render check (screenshot mid-animation) for any animated
  transform before sign-off. A real session shipped this bug past 4 frozen-frame vision
 checks; the user caught it ("wheel rotates around the cycle").
 - **Frozen-freezer regex must handle non-self-closing paths** — a leg path that
 wraps an `<animate>` child (`<path d="..."> <animate .../> </path>`) is NOT
 matched by `<path\b[^>]*/>`-style regexes; the d-substitution silently no-ops
 and every snapshot shows the leg frozen at frame 0 while gates "pass". Fix:
 substitute `d="..."` directly with `re.subn` and hard-fail when the match
 count != 1. A fresh-eyes review flagged "frozen far leg" that was purely this
 QA artifact — always verify the snap file's own `d` attribute changed per
 frame before trusting pixel probes. Related: when freezing opposed cranks,
 derive the freeze rotation from the static arm's ACTUAL angle — if the 180°
 opposition is already baked into the far arm's static endpoint, adding +180
 to the freeze rotation double-counts and freezes the pedal antipodal to the
 IK foot (live SMIL stays correct; only snapshots lie).

## Verification

1. **XML well-formedness:** wrap fragment in temporary `<svg>` tags, run
   `xmllint --noout`. If invalid, fix syntax.
2. **Assembly validation:** after concatenation, run
   `xmllint --noout assembled.svg` on the full file.
3. **Visual QA:** open in browser, verify wheels spin, crank turns, legs cycle
   in opposite phase.
4. **Phase check:** screenshot at t≈0.4s and t≈1.2s — rear and front feet
   should be on opposite pedals at both times.