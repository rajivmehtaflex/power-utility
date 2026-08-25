---
name: svg-illustration
description: Create hand-coded SVG illustrations (characters, scenes, icons) as standalone .svg files. No HTML wrappers, no decorative artifacts unless requested.
license: MIT
metadata:
  author: Hermes Agent
  hermes_related_skills: architecture-diagram, claude-design, html-artifact
  hermes_tags: svg, illustration, graphics, vector, creative, icons, characters
  platforms: linux, macos, windows
  version: 1.0.0
---

# SVG Illustration Skill

Create hand-coded SVG illustrations for characters, scenes, icons, and creative visual content as standalone `.svg` files.

## Scope

**Best suited for:**
- Characters and animals on objects (e.g., pelican on bicycle)
- Simple scenes and illustrations
- Icons and symbols
- Whimsical or playful visual content
- Flat or semi-flat illustration styles
- **Isometric 3D scenes** — buildings, castles, cities, LEGO-style models, product mockups. See `references/isometric-3d-projection.md` for projection math and reusable patterns.

**Look elsewhere first for:**
- Technical architecture diagrams → use `architecture-diagram`
- Interactive web components → use `html-artifact` or `claude-design`

**Animated SVG (SMIL) is in scope here** when it's a character/scene illustration that moves
(wheels spin, crank turns, limbs pump). Only offload to a dedicated animation tool if you need
timeline/keyframe UI or JS-driven sequencing. See `references/animated-limb-ik.md` for the
limb-tracks-rotating-mechanism technique and the frozen-frame verification loop.
See `references/smil-animation-fragments.md` for the animation fragment pattern (separate
`.svg` files containing only `<animate>`/`<animateTransform>` elements that target IDs in
structural fragments, with no `<svg>` wrapper — merged in at assembly time).

**HTML/CSS/JS animation is also in scope** when the user explicitly asks for HTML, CSS, JS, or
a `.html` deliverable instead of SMIL. The same coordinate contracts and IK math apply; only
the execution vehicle changes — a `requestAnimationFrame` loop drives `setAttribute` transforms
instead of `<animate>`/`<animateTransform>` elements. See the "HTML/CSS/JS animation variant"
section at the end of `references/animated-limb-ik.md` and the HTML implementation notes in
`references/seated-driver-example.md`. Browser is the canonical renderer for HTML artifacts;
`rsvg-convert` is not applicable.

## User Preferences

**Critical preference — ALWAYS follow:**
- **Pure SVG output only** — never wrap SVG in HTML `<html><body>` tags unless explicitly requested
- **Clean illustrations** — no decorative artifacts unless user specifically asks: no titles, no shadows, no ground effects, no grass tufts, no background gradients
- If user says "remove artifacts" or "clean up", strip all decorative elements and keep only the core subject

## Output Location

Save illustrations to user-specified path, or default to user home:
```
~/[subject]-illustration.svg
```

## Design Principles

### SVG Structure

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="800" height="600">
    <!-- Gradients and defs first -->
    <defs>
        <linearGradient id="name" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#fff;stop-opacity:0.5"/>
            <stop offset="100%" style="stop-color:#ccc;stop-opacity:0.5"/>
        </linearGradient>
    </defs>
    
    <!-- Background elements (if any) -->
    
    <!-- Main subject (z-order: back to front) -->
</svg>
```

### Z-Order (Rendering Order)

Elements defined later render on top. Order matters:
1. Gradients/defs
2. Background elements
3. Main subject (back to front within subject)
4. Details and highlights

### Coordinate System

- `viewBox="0 0 width height"` defines the coordinate space
- Origin (0,0) is top-left
- Positive Y goes down
- Use reasonable dimensions (e.g., 800x600, 1024x768)

### Common SVG Elements

**Shapes:**
- `<circle cx="x" cy="y" r="radius"/>`
- `<ellipse cx="x" cy="y" rx="rx" ry="ry"/>`
- `<rect x="x" y="y" width="w" height="h" rx="corner-radius"/>`
- `<line x1="x1" y1="y1" x2="x2" y2="y2"/>`
- `<path d="M x y Q cx cy x y ..."/>`

**Styling:**
- `stroke="#color"` — border color
- `stroke-width="N"` — border thickness
- `fill="#color"` — fill color
- `fill-opacity="0.5"` — transparency
- `stroke-linecap="round"` — rounded line ends
- `stroke-dasharray="a,b"` — dashed lines

**Transforms:**
- `transform="translate(x,y)"` — move element
- `transform="rotate(deg)"` — rotate around origin
- `transform="scale(s)"` — scale

**Groups:**
- `<g id="name">...</g>` — group related elements
- Apply styles to group to affect all children

### Color Palette Suggestions

**Natural subjects (animals, characters):**
- Skin/feathers: `#f5f5f5` (cream), `#fffaf0` (ivory), `#e8e8e8` (light gray)
- Accents: `#ff9800` (orange), `#ffb74d` (light orange), `#e65100` (dark orange)
- Details: `#666`, `#777`, `#888` (grays)

**Objects/vehicles:**
- Frames: `#e63946` (red), `#2a9d8f` (teal), `#264653` (dark blue)
- Metal: `#333`, `#444`, `#666`
- Highlights: `#aaa`, `#888`

## Isometric 3D Projection

For 3D-looking objects (buildings, LEGO models, product mockups), use **30° isometric projection**. Every 3D grid point `(bx, by, bz)` maps to screen `(sx, sy)` via a deterministic formula — no guessing coordinates by hand.

```
sx = originX + (bx - by) × 0.866 × UNIT
sy = originY + (bx + by) × 0.500 × UNIT - bz × HUNIT
```

Where `UNIT` = horizontal grid spacing (~26px), `HUNIT` = vertical height per level (~20px).

**Each solid block** has 3 visible faces (top=lightest, right=medium, left=darkest). This creates the 3D illusion even with flat shapes.

**For complex isometric scenes** (many blocks, studs, details), use a **Python generator script** (`templates/isometric-scene-generator.py`) to compute all coordinates programmatically. This is far more reliable than hand-coding hundreds of `<path>` coordinate pairs.

See `references/isometric-3d-projection.md` for the complete formula, three-face block pattern, stud/crease details, and translucent material tuning.

### Translucency Tuning

When layering translucent fills (`fill-opacity < 1.0`), watch for **muddy color blending** where overlapping layers mix. Key lessons:

- **0.50 opacity** is too low for stacked structures — colors blend into muddy purples/grays where 3+ layers overlap
- **0.62–0.77** is the sweet spot for "translucent plastic/glass" — readable but still see-through
- Use a **dark background** (`#0f172a` / `#0a0f1e`) so translucency pops visually
- Pre-compute **3 shade variants per color** (top/right/left = lightest/medium/darkest) for face differentiation

## Workflow for New Illustrations

1. **Plan the composition:**
   - Identify main subject and supporting elements
   - Determine coordinate space (viewBox)
   - Plan z-order (what's behind/in front)
   - **For isometric 3D:** lay out a grid map of all components with `(bx, by, bz)` bounds before drawing anything

2. **Create basic shapes first:**
   - Start with large simple shapes
   - Build up complexity layer by layer
   - Test as you go (open SVG in browser frequently)
   - **For complex scenes (50+ elements):** write a Python generator script instead of hand-coding. See `templates/isometric-scene-generator.py`.

3. **Add details and styling:**
   - Apply gradients for depth
   - Add strokes for definition
   - Use opacity for layering

4. **Refine and test:**
   - Open in browser to verify
   - Adjust coordinates as needed
   - Remove artifacts if user requests clean output
   - **For isometric:** verify visually using `browser_vision` or by taking a screenshot and reviewing with `vision_analyze` — check z-order overlaps, color readability, and that no elements float or misalign

## Physics-Aware Verification

When the request asks for “realistic”, “near to real world”, or includes physics/biomechanical constraints, add a pre-generation planning pass and a post-generation render check.

For physics-coherent environmental/weather scenes — wind, lightning, snow drifts, structural loads, turbines, drones/balloons, and technical HUD overlays — see `references/physics-coherent-environmental-scenes.md` for the single-model approach, SVG +Y-down rotation convention, render-backed QA checklist, and lightweight reference validation.

### Planning Pass
1. Identify stated constraints: anatomy, object interaction, balance, reach, weight distribution.
2. Sketch a short physics thought experiment: center of mass, leg/pedal reach, grip feasibility.
3. Translate constraints into coordinate choices before coding: seat height vs leg length, pedal angle, torso lean.
4. Reject impossible poses explicitly and choose a slightly stylized but plausible alternative.
5. Build a **Coordinate Alignment Table** — list every interface where two SVG components touch (e.g., wheel rim→ground, frame→hub, character→saddle, foot→pedal, hand→handlebar). For each interface, record the exact shared coordinate. This serves as the zero-tolerance contract for all downstream drawing; any coordinate drift causes visible disconnection. Example from a composite scene:
   ```
   | Interface           | Shared Coordinate        | Verified? |
   |---------------------|--------------------------|-----------|
   | Front wheel→ground  | y=550 (hub_y + r = 550)  |           |
   | Frame→rear hub      | (150, 490)               |           |
   | Frame→saddle        | (415, 255)               |           |
   | Character→handlebar | (485, 215)               |           |
   ```

### Render-Backed Verification Loop
After generating SVG, validate it visually, not just as text:
1. Render to PNG with `rsvg-convert -o <path> <svg>`.
2. Review the render with `vision_analyze` against the stated constraints.
3. Check **scale, z-order, and accidental dominance** of repeated assets; a symbol can be technically present but visually wrong if `<use>` sizing or placement is off.
4. If issues are found, patch the SVG and rerender; repeat until clean.
5. For animated SVG with character limbs touching a rotating part (pedals, crank, wheel), verify foot-pedal alignment at MULTIPLE crank angles — not just t=0. Create frozen-frame snapshots at 2+ angles (e.g. ~90° and ~180° from start) by replacing `<animateTransform>` with `transform="rotate(angle cx cy)"` and `<animate>` with the static keyframe path. Render each with `rsvg-convert`, then `vision_analyze` asking "does the foot sit exactly on the pedal platform?" at each angle. **Aim for 3 angles (e.g. k=3,6,9 of a 12-frame cycle) so a single lucky alignment can't mask a drift.** Reuse a shared `_shell.txt` (defs+style) for both the master assembler and the snapshot generator so the frozen frames match the live SVG exactly. A ready-to-run generator lives at `scripts/make_frozen_snapshots.py`.
6. Only then hand the image/SVG to the user.

This loop catches pedaling misalignment, floating limbs, missing grips, z-order problems, and symbol-scaling artifacts that XML inspection misses. **Note on rendering engines:** `rsvg-convert` and browsers can disagree on fine details (gradient edges, 1-2px lines). Use rsvg for quick feedback but the **browser for final sign-off**. See `references/character-on-object-composition-tricks.md` for the rsvg-vs-browser protocol. Also see `references/render-verification-and-use-scaling.md` for the solar-panel/grid example and the exact `<use>` sizing lesson.

**Vision model reliability on SVG renders:** `vision_analyze` can give **contradictory or hallucinated** results on the same rendered PNG — one call may pass all checks while another on the same render reports "decapitated head, floating parts". Mitigations:
- Run at least 2 rounds of vision QA on the same render; if they disagree, the SVG **coordinate math** is the ground truth, not the narrative.
- For contact-point verification (wheels→ground, foot→pedal, arms→wheel), re-verify with the **coordinate contract** (`cy + r == ground_y`) — a failing vision pass means the testing method is unreliable, not that the geometry is wrong.
- `browser_vision` (local screenshot, uses the active model) tends to be more consistent than standalone `vision_analyze` because it renders from the actual browser engine.
- When a vision model repeatedly flags the same defect across multiple render rounds, take it as a real pattern. A one-off contradictory hallucination is noise.

### Render-Specific Pitfall
When reusing symbols with `<use>`, do **not** assume the browser will infer the intended size. Set explicit `width` / `height` or apply an intentional scale/transform, then verify the raster output. This prevents oversized grids, panels, or icons from hijacking the composition.

### Animated SVG: limbs that track a rotating mechanism
When animating a character whose limbs touch a ROTATING part (pedals on a crank, hands on a
wheel, feet on a treadmill), fixed-coordinate limbs will visibly DRIFT from the part — the
"lag not aligned with paddle" defect. Two correct options:
- **Rigid glue:** put the distal joint (e.g. webbed foot) inside the rotating group so it orbits
  with the part. Use when the contact point is exactly on the rotation pivot offset.
- **2-link inverse kinematics:** hip fixed, foot endpoint = pedal position `pivot + r*(cos a, sin a)`,
  knee solved so thigh==shin and bends forward. Bake N frames into `<animate attributeName="d">`.
  Full recipe + a frozen-frame verification loop (since `rsvg-convert` can't seek SMIL time) in
  `references/animated-limb-ik.md`. Both legs use opposite phase (`a + pi`).
All rotating parts (wheels, crank, glued feet) MUST share one `dur` or they desync.

## Critical IK Pitfall: Over-Reach and Silent Straight-Leg Failure

When computing 2-link IK for character limbs tracking rotating mechanisms, the leg length MUST satisfy `max(hip_to_pedal_distance) <= 2L` for ALL crank angles. If even ONE frame over-reaches, the IK solver produces `h=0` (straight leg) for that frame — this passes text/XML validation and looks deceptively correct at t=0, but is visibly wrong at other crank angles.

**Always run reachability validation BEFORE baking keyframes:**
```python
maxd = max(math.hypot(pedal(start+2*math.pi*k/N)[0]-hip[0],
                      pedal(start+2*math.pi*k/N)[1]-hip[1]) for k in range(N))
assert maxd <= 2*L, f"OVER-REACH: max dist {maxd:.2f} > 2L {2*L} — bump L"
```
If over-reach is detected, increase L in 1px increments until all frames pass. Do NOT revert to the original L.

A real session used L=42 for a pelican leg with hip-to-pedal distance of ~131. All 12 frames over-reached. The solver silently produced straight legs per frame. Only a manual reachability check caught this. Fix: L=70 (thigh=shin), giving 2L=140 >= 131.

**PYTHON LIST-ALIASING TRAP** — see `references/animated-limb-ik.md`.

## Verification

After creating an illustration:

```bash
# Open in browser
open ~/illustration.svg
# or
xdg-open ~/illustration.svg
```

Check:
- All elements render correctly
- Z-order is right (things overlap properly)
- Colors match intent
- No unwanted artifacts (unless requested)

## Common Pitfalls

**Avoid:**
- HTML wrappers when user wants pure SVG (user will ask "only svg part")
- Decorative elements when user wants clean output (user will ask "remove artifacts")
- Overly complex paths — break into simpler shapes
- Forgetting stroke-width on thin lines (they disappear)
- **Transformed group coordinate errors** — coordinates inside `<g transform="...">` are relative to the group origin, not global. See `references/svg-coordinate-systems.md`
- **Disconnected character-on-object anatomy** — when drawing a character riding/sitting/holding an object, prefer a unified silhouette path for connected body/neck/head shapes and reuse exact contact-point coordinates for feet/hands. See `references/character-on-object-continuity.md`
- **Animated limbs drifting from a rotating part** — fixed-coordinate legs + a rotating pedal = visible lag ("not aligned with paddle"). Always rigid-glue the foot to the pedal OR drive the leg with 2-link IK so the foot endpoint follows the pedal every frame. See `references/animated-limb-ik.md`
- **Verify EMITTED IK coordinates, not just the reachability gate** — a real session's sub-agent passed `max dist <= 2L` but emitted knees ~359px from the hip (link length violated 3x); its report claimed PASS because it never asserted `|hip-knee| == L` on its own output. Before baking sub-agent keyframes into fragments, re-parse the emitted `M..L..L..` strings and assert `|hip-knee| == |knee-foot| == L` (±1e-6) plus the knee-forward side for EVERY frame. Coordinate math is ground truth; narrative reports are not evidence.
- **Hand-transcribing IK keyframes into JavaScript** — when building HTML/CSS/JS animations, never copy generated Python IK keyframe values into JS arrays by hand. A real session corrupted frame 5's foot coordinates during manual transcription, causing a visible leg snap mid-cycle. Always generate JS arrays programmatically from Python output (write the JS from Python, or dump JSON and load it). See `references/animated-limb-ik.md` → "HTML/CSS/JS animation variant".
- **Muddy translucency** — `fill-opacity` below 0.55 on stacked/layered elements causes colors to blend into muddy purples/grays. Use 0.62–0.77 for translucent materials. See `references/isometric-3d-projection.md` for a tuning table.
- **Hand-coding complex isometric coordinates** — for 50+ element scenes, use a Python generator script (`templates/isometric-scene-generator.py`) instead of computing coordinate pairs manually

- **Foreground frame overlay** — when the character hides the backbone, add a duplicate segment in front of the character. See `references/character-on-object-composition-tricks.md`.
- **Saddle extension** — extend the saddle 10–12px below the character body bottom so it's visible. Same reference.
- **Glued-element centering** — a foot glued to a rotating pedal must share the exact same center as the pedal, or rotation will separate them. See `references/character-on-object-composition-tricks.md`.
- **`animateTransform` → `transform` trap** — replacing `<animateTransform>` with `transform=` inside a `<g>` produces an orphaned text node, not an attribute. Replace the whole `<g>` opening tag. Same reference.

**Remember:**
- User preference: clean, artifact-free SVG by default
- Test frequently in browser to catch rendering issues
- Use groups (`<g>`) to organize complex subjects
- Gradients add depth but keep them simple
- When using transforms, all child coordinates are relative to the transformed origin

## Advanced: Parallel SVG Fragment Assembly

For complex single-SVG outputs (e.g., character on vehicle with IK animation), subagent parallelism is limited because only one file is produced. A reliable workaround: **write SVG layer fragments to separate files, then concatenate in z-order**.

### When to use

- The SVG has 6+ distinct z-layers (background, wheels, frame, crank, character, FX)
- You need to dispatch subagents in parallel (Wave 1 pattern)
- The IK/animation values are computed first (Wave 0) and shared via a contract file

### Wave structure

```
Wave 0 (1 subagent): Compute IK keyframes + write coordinate contract file
Wave 1 (parallel, 6+ subagents): Each writes one fragment file under _svg/
Wave 2 (1 subagent): Concatenate fragments in ascending z-order + close </svg>
Wave 3 (1 subagent): Verify with xmllint + frozen-frame snapshots + vision_analyze
```

### Fragment contract

Each fragment file:
- Is NOT a complete SVG — no `<svg>` wrapper, no `</svg>` close
- Contains only the `<g>` / element(s) for its z-layer
- Uses the coordinate contract exactly (no drift)

### Assembly order

Concatenate fragments in ascending z-layer (back to front):
```
01-header-bg.svg  (defs, sky, ground — also carries <svg> open tag)
02-rear-layer.svg (elements behind main subject)
03-main-subject.svg
04-foreground.svg
07-animations.svg (FX on top)
08-animations.svg (SMIL: wheel spin, crank rotation, leg IK — see references/smil-animation-fragments.md)
then: echo '</svg>' >> output.svg
```

### Key rules

1. **Header file approach**: Write a `_header.svg` containing `<svg>`, `<defs>`, gradients, and `<style>`. It ends with `</defs>` (NO closing `</svg>`). The assembler inserts groups between `</defs>` and `</svg>`. **PITFALL**: If using `rstrip('</svg>')` to strip a closing tag, `rstrip` strips individual characters — not the literal substring. `rstrip('</svg>')` on `</defs>` removes `e>` leaving `</d`. Use explicit string matching or ensure the header file does not end with `</svg>`. Also see: `references/smil-animation-fragments.md` for the animation fragment pattern and `references/character-on-object-composition-tricks.md` for the `animateTransform` → `transform` trap.

2. **One file per subagent** — no two subagents write the same fragment file
2. **Coordinate contract in Wave 0** — all fragments import from the same _CONTRACT.txt
3. **IK values in a shared text file** (e.g. `_svg/_IK_VALUES.txt`) — fragments that need animated path values read from it
4. **Verify file existence before assembly** — the assembler checks all fragments exist before concatenating
5. **`xmllint --noout` after assembly** — validates the concatenated result
6. **A fragment may hold MULTIPLE top-level `<g>` groups** (e.g. one subagent owns both `#wheels` and `#steering`). Such a fragment is NOT a valid standalone XML doc — `xmllint --noout fragment.svg` errors with "Extra content at the end of the document". This is expected and fine: the assembler must EXTRACT each group by `id` (regex split on `<g id="X">...</g>`, DOTALL), not concatenate the raw file, and never treat fragments as single-rooted. A Python `extract_all(text, gid)` that returns every `<g id="gid">…</g>` block handles this.
7. **Enforce z-order and DEDUPLICATE in Wave 2.** Blind concatenation can duplicate a group (a real bug once produced two `#steering` blocks, mis-ordered). After assembly, assert every `id` appears exactly once and the z-order is correct back→front. A reusable assembler pattern: extract each named group, then EMIT them in a hard-coded z-list (e.g. `background, wheels, car, steering, torso, neck, arms`), so order and dedup are explicit, not accidental.

### Z-ORDER TRAP: a fragment that must straddle the body
If one logical component renders on BOTH sides of another (classic case: character's REAR leg
behind the body, FRONT leg in front), you CANNOT hand the assembler a single "legs" fragment —
inserting it as one block puts the front leg behind the body too. Two fixes, either works:
- **Subagent emits TWO blocks in one file** (`legs.svg` with `<g id="legs_right_behind">` then
  `<g id="legs_left_front">`); the assembler SPLITS on those two `<g id>` tags (regex, DOTALL)
  and places `legs_right_behind` before `frog_body`, `legs_left_front` after it.
- **Two fragment files** (`legs_behind.svg`, `legs_front.svg`) in the correct z-slots.

Either way the assembly list reads back-to-front:
`background, wheels, frame, legs_right_behind, frog_body, legs_left_front, crank, fx`
— NOT `…, legs, frog_body, …`.

The master `<defs>`/`<style>` (gradients, CSS keyframes) live ONLY in the header fragment or a
reused `_shell.txt` (so the frozen-frame snapshot generator can share it). Fragments must
reference shared gradient ids (`url(#frogGreen)`) WITHOUT redefining them, or you get duplicate-id
XML errors.

See `references/pelican-on-bicycle-example.md` for the origin of this pattern, and `references/animated-limb-ik.md` for the IK computation that feeds into it. A reusable frozen-frame verifier that splits a combined `legs.svg` around the body and reuses `_shell.txt` lives at `scripts/make_frozen_snapshots.py` — run it to rasterize k=3/6/9 and vision-check foot-on-pedal at every angle. For the "character seated as the DRIVER of a vehicle" variant (open cockpit, S-curve neck, visible shoulders, grip layering), see `references/seated-driver-example.md`.

## Example: Character on Object Pattern

From the pelican on bicycle session, here's a reusable pattern for "X on Y" illustrations:

```xml
<!-- 1. Object base (bicycle, chair, etc.) -->
<g id="object">
    <!-- Structure shapes -->
    <!-- Details -->
</g>

<!-- 2. Character body -->
<g id="character-body">
    <!-- Main shape -->
    <!-- Shading -->
</g>

<!-- 3. Character features -->
<g id="character-features">
    <!-- Head -->
    <!-- Limbs positioned on object -->
    <!-- Details -->
</g>

<!-- 4. Gradients at top -->
<defs>
    <linearGradient id="bodyGradient"...>
    <linearGradient id="featureGradient"...>
</defs>
```

Key learnings:
- Position character body where it sits on object
- Extend limbs to object connection points
- Use opacity on "behind" elements to show depth
- Gradients defined once, referenced with `url(#id)`

### "X SEATED IN a vehicle" variant (giraffe driving a tiny car)

When the character must read as the DRIVER (not a rider perched on top, and not floating above a
block), the cockpit framing is the whole game. Lessons from a giraffe-in-go-kart build:

- **Open cockpit / go-kart body, not a closed cabin or a pickup bed.** A closed cabin hides the
  torso (looks like a neck poking out of an engine); a pickup bed reads as "in the truck bed, not
  driving". Use a LOW body with an OPEN-ROOF cockpit (two side walls + a windshield at the front)
  so the torso top pokes above the rim — that single exposed chest sells "seated driver".
- **Draw visible shoulders/chest ABOVE the cockpit rim.** If the whole torso is hidden, the neck
  appears to emerge from the chassis. Add a shoulder/chest path that rises just behind the neck
  base so the body is clearly present inside the seat.
- **S-curve the neck.** A giraffe (and most long-necked characters) neck must be an S-curve, not a
  straight diagonal tube — vision QA flags a straight neck as "stiff / mechanical crane arm".
  Build the path with two opposing curve segments (dip at the shoulder, rise toward the head).
- **Layering for gripping:** draw the STEERING WHEEL BEFORE the arms, and the arms' hooves AFTER,
  so the hooves sit on top of the wheel (correct grip read). The arms group is the LAST child of
  the rig for this reason.
- **Shared `rig` translate for the whole car+character** (suspension bounce), while the WORLD
  scrolls past (parallax: infinitely-far sun static, near trees scroll). This reads as "driving
  rightward" without moving the car off-frame.
- **Same-color limb visibility trap:** if arms/legs use the same `fill` color as the torso or
  background they overlap, they become INVISIBLE. Always give limbs a darker outline or a
  slightly different shade (`#dbb02a` vs `#f4c430` for giraffe yellow) so they contrast against
  the body. A two-tone approach (outer dark stroke + inner light fill) works best.
- **Geometric overlap for part connections, not just adjacency:** when connecting two SVG shapes
  (head→neck, neck→torso, arm→steering wheel), the bounding boxes must OVERLAP, not just touch
  edge-to-edge. A 10+ pixel gap between a neck-top boundary (y=170) and a head-bottom boundary
  (y=156) is invisible to coordinate math but visually obvious. Extend one shape into the other
  by several pixels to create a solid visual join.
- **Animation physics: `translate` animations lift the rig off contact points.** A rig-level
  `<animateTransform type="translate">` for suspension bounce moves the entire car+character
  unit. Even a 3px upward translate lifts wheel bottoms off the ground line, creating a
  "floating car" visual in most animation frames. If ground contact must be maintained through
  the entire cycle, EITHER: (a) remove the bounce animation entirely (scenery scrolling + wheel
  spinning is sufficient motion), OR (b) model the bounce as chassis-only compression inside the
  rig (spring compresses INTO the wheels, which stay ground-contact fixed). Do not apply
  `translate` to a shared `#rig` upward as bounce.

See `references/seated-driver-example.md` for the giraffe-car coordinate contract and the exact
neck/shoulder/cockpit markup that passed visual QA.

## When to Use This Skill

User asks for:
- "Draw an SVG of..."
- "Create an illustration of..."
- "Make a vector graphic of..."
- "Generate an SVG character/scene..."
- "Isometric view of..." / "3D-perspective..." / "LEGO-style..."

User corrections to watch for:
- "Only SVG part" → Remove HTML wrapper, output pure `<svg>...</svg>`
- "Remove artifacts" → Strip titles, shadows, decorative elements
- "Clean it up" → Same as above

## Isometric & 3D-Perspective Illustrations

For isometric/3D-perspective illustrations (buildings, LEGO, game assets, isometric scenes):

1. **Write a Python/JS generator script** — never hand-code coordinates for complex scenes. Define objects in 3D grid coords `(bx, by, bz)`, use a projection function to convert to 2D screen coords, emit SVG programmatically.
2. **Use the 3-face block pattern** — every solid has exactly 3 visible faces (top=lightest, right=medium, left=darkest). Define colors as 3-shade sets.
3. **Draw in strict z-order** — back-to-front by `(bx + by)` sum.
4. **Translucency sweet spot** — `fill-opacity` 0.65–0.75. Below 0.55 colors turn muddy.

See `references/isometric-svg.md` for the full projection formula, block/stud/roof patterns, and worked examples.