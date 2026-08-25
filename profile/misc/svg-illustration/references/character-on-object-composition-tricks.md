# Character-on-Object Composition Tricks

Session-derived techniques from building a frog on a penny-farthing bicycle.
These complement the IK/animation patterns in `animated-limb-ik.md` but focus on
**static composition and frozen-frame verification** — the things that make the
illustration look structurally sound even when you can't see the SMIL animation.

---

## 1. Foreground Frame Overlay (Backbone Visibility)

### Problem
When a character sits on a bicycle (or any two-point vehicle), the backbone frame
passes behind the character's body. If the backbone continues from the saddle area
to the handlebars, that segment is hidden behind the character. Visually, the frame
appears to "stop at the saddle" and the handlebars seem to float.

### Fix
Add a **second copy** of the backbone segment from saddle-to-handlebars that renders
**in front of** the character group.

```svg
<!-- Original backbone (behind character) -->
<g id="frame-back">
  <path d="M150,490 Q250,430 375,365 Q410,310 415,255 L485,215"/>
  <line x1="485" y1="215" x2="460" y2="380"/>
</g>

<!-- ... character body here ... -->

<!-- Foreground overlay (on top of character) -->
<g id="frame-front" stroke="#5C3A1E" stroke-width="7" fill="none" stroke-linecap="round">
  <path d="M415,255 L485,215"/>
  <line x1="485" y1="215" x2="460" y2="380"/>
</g>
```

This gives the viewer a continuous visual line: rear hub → behind character → reappears → handlebars → front hub.

### When NOT to use
- The character is translucent. The single backbone shows through already.
- A 3/4 or perspective view where the backbone naturally passes beside the character.

---

## 2. Saddle Extension Below Character Body

### Problem
The saddle sits at the character's seat junction. If the character's body bottom
exactly meets the saddle bottom (e.g., both at y=266), the saddle is completely
hidden behind the character's stroke/fill. The character appears to float.

### Fix
Extend the saddle **10–12px below** the character's body bottom.

```
Character body bottom:   cy + ry = 232 + 34 = 266
Saddle bottom (before):  same = 266 → invisible
Saddle bottom (after):   278 → 12px visible lip
```

```svg
<!-- BEFORE (invisible behind body) -->
<path d="M390,248 Q415,242 440,248 Q435,264 415,266 Q395,264 390,248 Z" fill="#8B5E3C"/>

<!-- AFTER (visible lip below body) -->
<path d="M385,248 Q415,242 445,248 Q440,276 415,278 Q390,276 385,248 Z" fill="#8B5E3C"/>
```

The saddle also benefits from a **lighter/brighter brown** (e.g., `#8B5E3C` instead of `#222`)
so it contrasts with the dark frame.

---

## 3. Glued-Element Centering Rule (Rigid-Glue Math)

### Problem
When a character's foot is "rigid-glued" to a rotating pedal (both inside the same
`<g>` with `animateTransform type="rotate"`), the foot and pedal must share the
**exact same center coordinate**. Even a 3–4px offset at t=0 causes visible separation
(6–8px) at 90° rotation because the offset vector rotates too.

### Math

```
At t=0, the foot is offset from the pedal center by (dx, dy).
When the group rotates by θ, the offset becomes:
  dx' = dx·cos(θ) - dy·sin(θ)
  dy' = dx·sin(θ) + dy·cos(θ)

A (dx, dy) = (3, -4) offset at t=0 becomes (dx', dy') ≈ (5, 1) at θ=90° — a 5px gap.
```

### Fix
Both the pedal platform AND the foot path must center on the **same coordinate** —
ideally the crank arm endpoint.

```svg
<!-- Crank arm endpoint = (489, 400) — this is the anchor -->
<line x1="460" y1="380" x2="489" y2="400" stroke="#555" stroke-width="5"/>

<!-- Pedal centered on endpoint -->
<rect x="486" y="396" width="14" height="6" rx="1" fill="#444"/>
<!--         center = (486+7, 396+3) = (493, 499) — wait, check --->
<!--         rect center = (486+7, 396+3) = (493, 399) -->
<!--         But endpoint is (489,400). These are 4px apart! Bad! -->

<!-- FIX: Make pedal center = endpoint -->
<!-- Pedal: x=482, y=397, width=14, height=6 → center = (489, 400) ✓ -->
<rect x="482" y="397" width="14" height="6" rx="1" fill="#444"/>

<!-- Foot: center also at (489, 400) -->
<path d="M484,398 L494,406 L484,405 Z" fill="#3D7B40"/>
```

### Verification
Check at t=0 in the browser. Then check at 90° rotation (frozen frame). If the foot
sits on the pedal at BOTH angles, the centering is correct. If only at t=0, re-center.

### Webbed-foot shape sizing
Keep webbed feet small relative to the pedal — they should sit ON TOP of the pedal,
not extend far beyond it. A path like `M488,398 L496,406 L487,405 Z` (8×8px bounding
box) on a 14×6px pedal is a good proportion.

---

## 4. `animateTransform` → `transform` Replacement Pitfall (Frozen Frames)

### Problem
When creating a frozen-frame snapshot, you replace `<animateTransform>` with a static
`transform` attribute. A naive string replacement produces INVALID SVG:

```svg
<!-- WRONG — transform is a text node, not an attribute -->
<g>
  transform="rotate(90 460 380)"
  <line .../>
</g>
```

The SVG parser interprets `transform="rotate(90 460 380)"` as a text node, not an
attribute of `<g>`. The rotation is silently ignored. The crank appears unrotated,
and the foot-pedal check at a non-zero angle looks broken.

### Fix
Replace the ENTIRE `<g>` opening tag (including the `<animateTransform` inside it)
with a single `<g transform="rotate(...)">` tag:

```python
# WRONG — replaces only the animateTransform line
content = content.replace(
    '<animateTransform attributeName="transform" type="rotate"\n    from="0 460 380" to="360 460 380" dur="1.6s" repeatCount="indefinite" />',
    'transform="rotate(90 460 380)"'
)
# Result: '<g>\n  transform="rotate(90 460 380)"' → INVALID

# CORRECT — replace the whole <g> opening
content = content.replace(
    '<g>\n  <animateTransform attributeName="transform" type="rotate"\n    from="0 460 380" to="360 460 380" dur="1.6s" repeatCount="indefinite" />',
    '<g transform="rotate(90 460 380)">'
)
# Result: '<g transform="rotate(90 460 380)">' → VALID
```

### Verbal check
After replacement, grep for `transform=`. You should see:
```
<g transform="rotate(90 460 380)">   ← ONE line, in the <g> tag
```
NOT:
```
<g>
  transform="rotate(90 460 380)"     ← orphaned on its own line
```

---

## 5. Rendering Engine Discrepancy (rsvg-convert vs Browser)

### Problem
`rsvg-convert` and browsers can render the same SVG differently, especially for:
- Gradient fills near stroke edges
- Stacked translucent elements
- Fine lines (1–2px stroke-width)
- Text layout

A `vision_analyze` on an `rsvg-convert` output may report misalignments that don't
exist in the browser. The browser is the canonical renderer.

### Protocol
1. Generate frozen frame SVG snapshots
2. Rasterize with `rsvg-convert` → `vision_analyze` for QUICK feedback (catching
   obvious coordinate errors)
3. Open in BROWSER → `browser_vision` for FINAL sign-off
4. If the two disagree, trust the browser. The frozen frame snapshots serve to
   catch coordinate bugs in the SVG (wrong anchor, missing rotation), not visual
   perfection in rsvg.

---

## Summary Cheat Sheet

| Problem | Symptom | Fix |
|---------|---------|-----|
| Backbone hidden by character | Handlebars appear to float | Add foreground frame overlay after character group |
| Saddle invisible | Character appears to float | Extend saddle 10–12px below character body bottom |
| Foot drifts from pedal at rotation | Foot-pedal gap at non-zero angles | Center foot and pedal on same (dx,dy)=0 anchor |
| Frozen frame shows wrong angle | Crank appears unrotated | Replace `<g>` opening tag, not just `<animateTransform>` |
| rsvg/browser disagree | False misalignment reports | Final sign-off in browser, not rsvg |
