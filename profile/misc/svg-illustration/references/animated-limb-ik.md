# Animated SVG: limbs that track a rotating mechanism (2-link Inverse Kinematics)

Problem that triggered this doc: a pelican's legs were drawn at FIXED coordinates while the
pedals ORBITED the crank. The moment the crank turned, the feet and pedals drifted apart —
the user called it "lag not align with paddle". Fix: the foot endpoint must coincide with
the pedal at every animation frame, and the knee must bend naturally.

## The core rule
If a body part (pedal, crank arm, wheel spoke, rotor) ROTATES about a fixed pivot, any limb
that touches it must NOT be drawn at fixed coordinates. Either:
  (a) make the limb part of the rotating group (rigid — only works if the joint is AT the pivot, e.g. a foot glued to a pedal), or
  (b) drive the limb with inverse kinematics so its distal end follows the rotating contact point.

For a limb hinged at a FIXED hip but touching a ROTATING pedal, use (b): 2-link IK.

## 2-link IK recipe (Python, run in execute_code)
Hip H fixed. Foot F = pedal position = pivot + r*(cos a, sin a). Knee K solved so
|H-K| = |K-F| = link length L, with K placed on the forward (+perpendicular) side so the knee
bends anatomically.

```python
import math
pivot = (370.0, 425.0); r = 28.0          # crank centre + pedal orbit radius
L = 80.0                                   # thigh==shin (isoceles leg)
hipH = (362.0, 298.0)                       # fixed hip

def pedal(a):  return (pivot[0]+r*math.cos(a), pivot[1]+r*math.sin(a))

def ik(H, F):
    hx,hy=H; fx,fy=F; dx,dy=fx-hx,fy-hy
    c=math.hypot(dx,dy); c=max(c,1e-6)
    ux,uy=dx/c,dy/c          # unit H->F
    px,py=-uy,ux             # perpendicular (knee side)
    x=c/2.0                  # isoceles -> projection at midpoint
    h=math.sqrt(max(0.0,L*L - x*x))   # guards against unreachable poses
    return (hx+ux*x+px*h, hy+uy*x+py*h)

N=12
frames=[]
start=math.radians(34.8)     # choose so frame 0 matches the static initial pedal pos
for k in range(N):
    a = start + 2*math.pi*k/N
    F=pedal(a); K=ik(hipH,F)
    frames.append(f"M{hipH[0]:.1f} {hipH[1]:.1f} L{K[0]:.1f} {K[1]:.1f} L{F[0]:.1f} {F[1]:.1f}")
keyTimes=";".join(f"{k/(N-1):.4f}" for k in range(N))
values=";".join(frames)
```

### Reachability Validation (essential pre-flight)

Before baking keyframes, validate EVERY frame: the hip-pedal distance must be ≤ 2L for all 12 frames. If any frame over-reaches (distance > 2L), the `h=sqrt(max(0, L²-x²))` guard produces `h=0`, forcing a straight leg — visually wrong and potentially disconnected.

Add after the keyframe loop:

```python
# Validate every frame
all_ok = True
for k in range(N):
    a = start + 2*math.pi*k/N
    F = pedal(a)
    d = math.hypot(F[0]-hipH[0], F[1]-hipH[1])
    flag = "OK" if d <= 2*L + 0.5 else "OVER-REACH!"
    if "OVER-REACH" in flag:
        all_ok = False
    print(f"Frame {k}: dist={d:.1f}/{2*L:.0f} {flag}")
print(f"All frames reachable: {all_ok}")
```

If any frame shows "OVER-REACH", increase L in 1-px increments until all pass. Typical starting L is 85%–90% of the maximum hip-pedal distance. **HARD GATE — treat OVER-REACH as a fatal error, not a warning.** A 2L value only ~0.02px below the max reach passes text validation but leaves ~1px slack; worse, if you misread the peak the leg silently cannot reach. Run this BEFORE baking:

```python
maxd = max(math.hypot(pedal(start+2*math.pi*k/N)[0]-hipH[0],
                      pedal(start+2*math.pi*k/N)[1]-hipH[1]) for k in range(N))
assert maxd <= 2*L, f"OVER-REACH: max dist {maxd:.2f} > 2L {2*L} — bump L"
```

Real example that bit a session: hip (410,260), crank pivot (460,380), r=35, L=82 → max hip-pedal distance was **164.98** while 2L=164, so the leg could NOT reach the pedal at crank angle 65°. The plan faked \"max 161 / slack 3px\". Fix: **L=83 (2L=166 ≥ 164.98)**, slack ~1px. Do NOT revert to 82. Verify the peak numerically; never hand-wave.

**PYTHON LIST-ALIASING TRAP (silent — doubles your frames).** Writing `left = right = []` makes both names alias the SAME list, so phase-A appends, then phase-B appends to the *same* object → 24 entries each (phase-B becomes phase-A+phase-B concatenated). The `<animate>` then has 12 keyTimes but 24 `values` → broken/blank leg. Always use distinct lists:

```python
left = []   # phase A (front leg, drawn on top)
right = []  # phase B (rear leg, drawn behind; pedal = a+pi)
```

After building, assert counts AND the phase relationship:

```python
assert len(left) == N and len(right) == N, f"len L={len(left)} R={len(right)}"
# Invariant: phase-B frame 0 == phase-A frame N/2 (180° offset)
assert right[0] == left[N//2], "phase B not 180° out of phase with phase A"
```

Also validate the OPPOSITE leg (phase a+π) with the same reachability check — it orbits a different part of the circle and may peak at a different k. (In the L=83 example both legs peaked at 164.98 but at different indices.)

Emit the limb as a single `<path>` with `<animate attributeName="d" values=... keyTimes=... calcMode="linear"/>`.
Meanwhile the PEDAL + WEBBED FOOT live inside the rotating crank group
(`<animateTransform type="rotate" from="0 px py" to="360 px py" .../>`) so the foot stays
glued to the pedal. Both animations MUST share the same `dur` so they never phase-drift.

## Verification loop for SMIL animations (rsvg-convert can't seek time)
`rsvg-convert` renders only t=0, so it cannot show an animation mid-cycle. To verify the foot
stays glued at an arbitrary angle:
1. Pick a frame index k; rotation = degrees(2*pi*k/N) from the start.
2. Write a STATIC snapshot SVG: same scene, but the crank group gets
   `transform="rotate(<rot> px py)"` (no <animate>), and the leg path uses `frames[k]` directly.
3. `rsvg-convert -o snap_k.png snap_k.svg`; `vision_analyze` it asking "does the foot sit
   exactly on the pedal?".
4. Check at least 2 angles (e.g. ~90° and 180°). If the foot lands on the pedal at those, the
   baked keyframes are correct for every frame.

This catches the exact "lag" defect the user reported, which a t=0 render never would.

## HTML/CSS/JS animation variant (instead of SMIL)

When the user asks for HTML/CSS/JS instead of SMIL, or the deliverable is a self-contained
`.html` file, the same IK math applies but the execution model changes:

- **No `<animate>` / `<animateTransform>` elements.** All transforms are driven by a single
  `requestAnimationFrame` loop using `element.setAttribute('transform', ...)`.
- **Generate IK in Python, then emit to JS.** Write the 12-frame paths as a JSON or JS array.
  **CRITICAL: never hand-transcribe keyframes from Python output into JS.** A real session
  corrupted frame 5's foot coordinates because the value was misread during manual copy,
  producing a visible leg snap. Always generate the JS arrays programmatically — either write
  the JS from Python or dump JSON and read it in the build step.
- **Crank + legs share one elapsed-time clock.** Derive both `crankAngle` and `legProgress`
  from the same `now - state.start` value. Never compute them independently or they drift.
- **Leg path interpolation:** snap-to-nearest at 12fps looks choppy. Smooth it by parsing
  each frame's `d` attribute coordinates (`path.match(/-?[\d.]+/g).map(Number)`) and linearly
  interpolating between adjacent frames' coordinate arrays. This gives fluid motion while
  keeping the IK-solved keyframes as the ground truth.
- **Rotation helper:** `el.setAttribute('transform', 'rotate(' + angle + ' ' + cx + ' ' + cy + ')')`
  — use `setAttribute`, NOT CSS `style.transform`, because SVG `transform` attributes with
  explicit center coordinates are more reliable across browsers than CSS transform-origin.
- **Pause/Resume:** store `pauseElapsed = performance.now() - state.start` on pause, then on
  resume set `state.start = performance.now() - pauseElapsed`. This preserves the animation
  phase so legs don't jump when un-paused.
- **Reduced motion:** check `window.matchMedia('(prefers-reduced-motion: reduce)')`. If true,
  render one valid static frame and skip the RAF loop entirely.
- **Verification:** `rsvg-convert` cannot render HTML. Use `browser_navigate` to the
  `file://` URL, then `browser_vision` for screenshot-based QA. Check `browser_console` for
  JS errors. The browser is the ONLY canonical renderer for HTML/CSS/JS artifacts.

## Pitfalls
- Fixed-coordinate legs + rotating pedal = the lag the user complained about. Always IK or rigid-glue.
- Opposite leg must use a = a + pi (180° out of phase) so the two feet are always on opposite pedals.
- Keep link lengths >= half the hip-to-pedal distance or the pose becomes unreachable (guard with max(0,...)).
- All rotating parts (wheels, crank, feet) must share one `dur` or they desync.
- **Hand-transcribing IK keyframes into JS corrupts values silently.** Always generate JS arrays from Python programmatically — see "HTML/CSS/JS animation variant" above.
- **CSS `style.transform` on SVG groups can conflict with existing `transform=` attributes.** Prefer `setAttribute('transform', ...)` for all animated SVG transforms in JS-driven animations.
