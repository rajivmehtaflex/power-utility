# Isometric SVG Illustration Techniques

## When to Use

Isometric projection for LEGO-style 3D objects, buildings, game assets, or any scene needing a 3D look in flat SVG. Verified building a translucent LEGO castle (800px canvas, ~800 lines, 9/10 visual quality).

## Core Principle: Use a Code Generator, Not Hand-Coding

For any isometric illustration with more than ~10 blocks, **write a Python (or JS) generator script** that computes coordinates via a projection function. Hand-coding hundreds of `<path d="M x,y L x,y ...">` coordinates is error-prone and unmaintainable.

Pattern:
1. Define all objects in 3D grid coordinates `(bx, by, bz)`
2. A single `proj(bx, by, bz) → "sx,sy"` function converts to screen coords
3. Helper functions (`block()`, `studs_on_top()`, `cone_roof()`) emit SVG strings
4. Assemble in z-order (back to front), write to `.svg` file

## 30° Isometric Projection Formula

```python
import math

ORIGIN_X = 400   # canvas center X
ORIGIN_Y = 370   # canvas center Y (slightly above middle for headroom)
UNIT = 26        # horizontal grid spacing in pixels
HUNIT = 20       # vertical height unit in pixels
ISO_COS = math.sqrt(3) / 2   # ≈ 0.8660
ISO_SIN = 0.5

def proj(bx, by, bz):
    sx = ORIGIN_X + (bx - by) * ISO_COS * UNIT
    sy = ORIGIN_Y + (bx + by) * ISO_SIN * UNIT - bz * HUNIT
    return f"{sx:.1f},{sy:.1f}"
```

- `bx` = grid column (increases right-and-back on screen)
- `by` = grid row (increases left-and-back on screen)
- `bz` = height level (increases upward on screen)

## Three-Face Visible Block Pattern

Every solid block from `(bx0,by0,bz0)` to `(bx1,by1,bz1)` has exactly 3 visible faces:

| Face | Position | Shade | Visibility |
|------|----------|-------|------------|
| Top | `bz = bz1` (max height) | Lightest | Always visible |
| Right wall | `bx = bx1` (max X) | Medium | Faces right-down |
| Left wall | `by = by1` (max Y) | Darkest | Faces left-down |

The 3 hidden faces (bottom, min-bx, min-by) are never drawn.

## 3-Shade Color Technique (Critical for 3D Depth)

Define each color as 3 shades — this creates the 3D illusion with flat shapes:

```python
COLORS = {
    "blue":   {"top": "#60a5fa", "right": "#3b82f6", "left": "#1d4ed8"},
    "red":    {"top": "#f87171", "right": "#ef4444", "left": "#b91c1c"},
    "green":  {"top": "#4ade80", "right": "#22c55e", "left": "#15803d"},
    # ... top = base+20% lightness, right = base, left = base-20%
}
```

Rule of thumb: top shade = +20% lightness, right shade = base color, left shade = -20% lightness. This is what makes flat SVG paths look 3D.

## Translucency

Use `fill-opacity` per face. Recommended ranges for "glass LEGO" look:
- Base plates: 0.55–0.65 (most transparent)
- Walls: 0.65–0.75
- Towers/structures: 0.65–0.75
- Roofs: 0.55–0.65
- Flags/decorative: 0.70–0.80

**Pitfall:** Below 0.55, overlapping translucent layers turn muddy-purple where colors blend. 0.65–0.72 is the sweet spot for readability + translucency.

Dark background (`#0a0f1e` or `#0f172a`) makes translucent colors pop.

## LEGO Studs (Top Surface Detail)

Each stud = 3 ellipses at grid center `(gx+0.5, gy+0.5, bz)`:

```python
# Base ring (darker, offset down)
ellipse(cx, cy+2, rx=7, ry=3.5, fill=dark_shade, opacity=0.55)
# Stud top (lighter)
ellipse(cx, cy, rx=7, ry=3.5, fill=light_shade, opacity=0.75)
# Highlight glint (white, upper-left)
ellipse(cx-2, cy-1, rx=3, ry=1.5, fill=#ffffff, opacity=0.35)
```

Place studs only on visible top surfaces. For large plates, place studs along visible front edges only (not the full grid) to keep file size manageable.

## Cone Roofs (Towers/Spires)

A cone from square base to apex point = 3 visible triangles:

```
Right slope: front-right corner → apex → right-back corner (lighter)
Left slope:  front-left corner → apex → left-back corner (darker)
Front face:  front-left corner → apex → front-right corner (lightest)
```

## Z-Order (Draw Order — Critical)

Draw back-to-front. Objects with higher `(bx + by)` are further back → drawn first.

General rule for a building on a grid:
1. Base/foundation
2. Back corner structures (highest bx+by)
3. Back walls
4. Central structures
5. Front walls
6. Front corner structures (lowest bx+by)
7. Roofs (on top of all structures)
8. Flags/decorative (highest elements)

## Gate Arch (Curved Opening)

Use a `<path>` with quadratic bezier for the arch curve, projected onto the isometric wall face:

```
M arch_left_bottom L arch_right_bottom L arch_right_top Q arch_apex arch_left_top Z
```

Add a second inner arch (darker, slightly smaller) for depth/recession effect.

## Verification

```bash
xmllint --noout ~/illustration.svg     # validate XML
open ~/illustration.svg                 # visual check (macOS)
```

Iterate by regenerating from the script — adjust opacities/colors, re-run, re-check in browser.
