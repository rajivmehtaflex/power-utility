# Seated-Driver Example: Giraffe Driving a Tiny Car

Condensed knowledge bank from a working "giraffe driving a tiny car" animated SVG (viewBox 0 0 800 500, SMIL animation). Use as a starting template for any "X is the driver of a small vehicle" illustration.

## Coordinate Contract (shared anchors across parallel subagents)

| Anchor | Value | Why |
|---|---|---|
| Canvas | `viewBox="0 0 800 500"` | whole scene |
| Ground top | `y=400` | wheels rest here |
| Rear wheel | center `(320,372)` r=`28` | bottom = 400 ✓ |
| Front wheel | center `(480,372)` r=`28` | wheelbase 160 |
| Chassis | `x=296 y=338 w=212 h=34` rx=14 | bottom 372 meets wheel centers |
| Cockpit walls | open-roof path `M348,340 L352,300 Q352,294 360,294 L452,294 Q460,294 460,300 L464,340 Z` | torso top pokes above rim |
| Windshield | `M464,338 L470,316 L486,318 L488,338 Z` fill `#bfe3ff` opacity 0.85 | front of cockpit |
| Steering wheel | center `(432,322)` r=12 | arms grip here |
| Torso | ellipse `(405,312)` rx=28 ry=26 | CoM over wheelbase midpoint (400) |
| Neck base | `(405,290)` | overlaps torso top (312-26=286) |
| Head pivot | `(452,150)` | nod rotates about this |

Z-order (back→front, inside one `#rig` group): `wheels → car → steering → torso → neck → arms`.
The `#rig` carries the suspension-bounce `<animateTransform type="translate" values="0 0; 0 -3; 0 0; 0 -1; 0 0" dur="0.5s">`. `#scenery` (sun + scrolling landscape) sits OUTSIDE `#rig` and scrolls left `dur=4s` for parallax.

## Animation timing (all `repeatCount="indefinite"`)
- Wheels spin: `rotate 0→360` about own center, `dur=1s` (both same direction).
- Scenery scroll: `translate 0 0 → -800 0`, `dur=4s`.
- Suspension bounce: `dur=0.5s`.
- Neck bob: `rotate` about `(405,290)`, `values="0; 2; 0; -2; 0"`, `dur=2s`.
- Head nod: `rotate` about `(452,150)`, `values="0; 3; 0; -3; 0"`, `dur=2.4s`.

## Neck S-curve path (passes visual QA — NOT a straight tube)
```
M404,300 C390,262 398,228 414,206 C430,184 446,176 450,170
L466,166 C460,186 444,212 430,234 C418,254 414,280 420,300 Z
```
Two opposing cubic segments give the shoulder-dip → head-rise S. Mane stroke follows the back edge.

## Visible shoulders above the cockpit rim
Add to the torso group so the body reads as present (not hidden in the chassis):
```
<path d="M386,316 Q388,292 408,294 Q430,296 424,318 Q410,326 386,316 Z" fill="#f4c430"/>
```
plus the spotted torso ellipse.

## QA loop that caught the real defects (rsvg-convert is first-frame only!)
1. `xmllint --noout file.svg` — well-formedness.
2. `rsvg-convert -w 800 -h 500 file.svg -o file.png` — static render.
3. `vision_analyze(file.png, ...)` against the contract. Caught: (a) neck↔torso GAP, (b) torso hidden in a "pickup bed" not a cockpit, (c) straight stiff neck. rsvg does NOT run SMIL, so motion is verified by source inspection; only LAYOUT is verified by the PNG.
4. Patch and re-render until vision says "seamless, no blocker".

## Assembler rules (Wave 2)
- Extract each group BY ID (a fragment can contain 2+ top-level `<g>`, e.g. `#wheels`+`#steering` — that file is NOT standalone-valid; extract, don't concatenate raw).
- EMIT in a hard-coded z-list so order + dedup are explicit. A duplicate `#steering` once slipped through blind concatenation.
- After assembly: `grep -c 'id="steering"' file.svg` should equal 1 for every id.

## HTML/CSS/JS implementation variant

The entire seated-driver scene above was also successfully built as a self-contained `.html`
file (no SMIL). Same coordinate contract, same neck/torso/cockpit paths. Key differences:

**Structure:** One `.html` with inline `<style>`, inline `<svg>`, inline `<script>`. No CDN,
no external fonts, no build step. Opens from `file://` directly.

**Z-order (back→front, as DOM order in the SVG):**
```
background → wheels → car-lower → cockpit → leg-rear → crank+pedals → torso → leg-front → neck → head → steering-wheel → arms
```
Note: steering wheel is drawn BEFORE arms so hooves sit on top (correct grip read). Both legs
straddle the torso: rear leg before torso, front leg after.

**Animation:** Single `requestAnimationFrame` loop. All transforms via `setAttribute('transform', ...)`.
- Wheels + crank: continuous `rotate(angle, cx, cy)` from one elapsed clock.
- Legs: 12-frame IK paths with linear interpolation between frames (parse `d` coordinates,
  lerp, rebuild path string). See `animated-limb-ik.md` → "HTML/CSS/JS animation variant".
- Neck bob ±2°, head nod ±3°, steering oscillation ±8° — all `Math.sin` driven.
- Scenery + road dashes: `setAttribute('transform', 'translate(...)')` at different speeds.
- NO suspension bounce on the whole rig (keeps wheels on ground). Omit entirely; scrolling
  + wheel spin is sufficient motion.

**Controls:** Pause/Restart buttons. Pause stores elapsed time; resume restores it so legs
don't jump. `prefers-reduced-motion` renders one static frame.

**Verification protocol (HTML-specific):**
- `xmllint --html --noout file.html` — structure check (SVG tag warnings are expected/cosmetic).
- `browser_navigate` to `file://` path → `browser_vision` for visual QA.
- `browser_console` for JS errors (check for runtime exceptions).
- `rsvg-convert` is NOT applicable — it cannot render HTML. Browser is the only canonical renderer.
