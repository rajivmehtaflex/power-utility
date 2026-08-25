# Isometric 3D Projection for SVG Illustrations

Technique for rendering 3D-looking objects (buildings, LEGO models, cities, products) as flat SVG using deterministic 30° isometric projection.

## Projection Formula

Every 3D grid point `(bx, by, bz)` maps to 2D screen `(sx, sy)`:

```python
ISO_COS = 0.8660  # √3/2
ISO_SIN = 0.5000

sx = originX + (bx - by) * ISO_COS * UNIT
sy = originY + (bx + by) * ISO_SIN * UNIT - bz * HUNIT
```

**Axes:**
- `bx` = grid column — increases right-and-back on screen
- `by` = grid row — increases left-and-back on screen
- `bz` = height level — increases upward on screen

**Constants (tune per scene):**
- `UNIT` = horizontal stud/brick spacing (~26px for medium scenes)
- `HUNIT` = one height level (~20px; a plate = HUNIT/3)
- `originX, originY` = center of the scene on canvas (~400, 370 for 800×800 viewBox)

## Three-Face Block Pattern

Every solid rectangular block from `(bx0,by0,bz0)` to `(bx1,by1,bz1)` has exactly **3 visible faces**:

| Face | Located at | Shade | Visibility |
|------|-----------|-------|------------|
| Top | `bz = bz1` (max) | Lightest | Always visible |
| Right wall | `bx = bx1` (max) | Medium | Faces right-down |
| Left wall | `by = by1` (max) | Darkest | Faces left-down |

```xml
<!-- LEFT WALL (darkest) -->
<path d="M p(bx0,by1,bz0) L p(bx1,by1,bz0) L p(bx1,by1,bz1) L p(bx0,by1,bz1) Z"
      fill="{leftColor}" fill-opacity="0.72"/>

<!-- RIGHT WALL (medium) -->
<path d="M p(bx1,by0,bz0) L p(bx1,by1,bz0) L p(bx1,by1,bz1) L p(bx1,by0,bz1) Z"
      fill="{rightColor}" fill-opacity="0.72"/>

<!-- TOP FACE (lightest) -->
<path d="M p(bx0,by0,bz1) L p(bx1,by0,bz1) L p(bx1,by1,bz1) L p(bx0,by1,bz1) Z"
      fill="{topColor}" fill-opacity="0.77"/>
```

**Draw order within a single block:** left wall → right wall → top face (top renders on top).

## Z-Order (Scene-Level)

Objects with higher `bx + by` are further back → drawn first. For a castle/building scene:

1. Base plate
2. Back-left corner structures (max bx, max by)
3. Back-right structures (max bx, min by)
4. Back connecting walls
5. Central/tall structures
6. Front-left wall + front-left corner
7. Front-right wall + front-right corner
8. Front-most structures (gatehouse, entrance)
9. Roofs (on top of all walls)
10. Flags/decorative peaks (highest elements)

## Color Shading Table

For each base color, pre-compute 3 hex shades. Darken ~15% per step:

| Color | Top (lightest) | Right (medium) | Left (darkest) |
|-------|---------------|----------------|----------------|
| Blue | `#60a5fa` | `#3b82f6` | `#1d4ed8` |
| Red | `#f87171` | `#ef4444` | `#b91c1c` |
| Yellow | `#fde047` | `#facc15` | `#ca8a04` |
| Green | `#4ade80` | `#22c55e` | `#15803d` |
| Purple | `#a78bfa` | `#8b5cf6` | `#6d28d9` |
| Orange | `#fdba74` | `#fb923c` | `#c2410c` |
| Cyan | `#38bdf8` | `#0ea5e9` | `#0369a1` |
| White | `#f8fafc` | `#e2e8f0` | `#cbd5e1` |

## Translucency Tuning

| Element Type | Recommended opacity | Notes |
|-------------|-------------------|-------|
| Base plate | 0.60–0.65 | Most transparent — just a plate |
| Walls | 0.68–0.75 | Need to read as solid-ish |
| Towers | 0.70–0.75 | Structural definition |
| Roofs | 0.60–0.68 | Slightly more transparent |
| Flags/fabric | 0.75–0.80 | Least transparent |

**Critical lesson:** 0.50 opacity causes muddy purple/gray blending where 3+ translucent layers overlap. Bumping to 0.62+ dramatically improves readability while maintaining the glass/plastic aesthetic.

**Background:** Use dark (`#0f172a` or darker) so translucency visually pops. A radial gradient (`#1e293b` center → `#0a0f1e` edge) adds depth.

## LEGO-Specific Details

### Studs (on visible top surfaces)

Each stud at grid position `(gx+0.5, gy+0.5)` on a top face:

```xml
<!-- Base ring (darker) -->
<ellipse cx="{sx}" cy="{sy+2}" rx="7" ry="3.5" fill="{darkColor}" fill-opacity="0.55"/>
<!-- Stud top -->
<ellipse cx="{sx}" cy="{sy}" rx="7" ry="3.5" fill="{lightColor}" fill-opacity="0.75"/>
<!-- Highlight glint -->
<ellipse cx="{sx-2}" cy="{sy-1}" rx="3" ry="1.5" fill="#ffffff" fill-opacity="0.35"/>
```

Only place studs on **visible** top surfaces. For a castle interior covered by walls, studs are invisible — skip them to reduce file size.

### Brick Seam Lines (on wall faces)

Horizontal course lines every `HUNIT` px vertically:

```xml
<line x1=".." y1=".." x2=".." y2=".." stroke="{color}" stroke-width="0.5" opacity="0.4"/>
```

Keep seams subtle (`opacity=0.3–0.4`) so they read as texture, not grid overlay.

## Cone Roofs

For conical/spire roofs from a square base to an apex point, draw two visible triangular slopes + one front-facing triangle:

```xml
<!-- Right slope (lighter) -->
<path d="M p(bx1,by0,bz_base) L {apex} L p(bx1,by1,bz_base) Z" fill="{medium}"/>
<!-- Left slope (darker) -->
<path d="M p(bx0,by0,bz_base) L {apex} L p(bx0,by1,bz_base) Z" fill="{dark}"/>
<!-- Front face (lightest) -->
<path d="M p(bx0,by0,bz_base) L {apex} L p(bx1,by0,bz_base) Z" fill="{light}"/>
```

Apex = projection of center point `( (bx0+bx1)/2, (by0+by1)/2, bz_apex )`.

## Python Generator Pattern

For complex isometric scenes (50+ elements), **always use a Python generator script** rather than hand-coding SVG coordinates. Benefits:

- Deterministic projection — no arithmetic errors
- Easy to adjust `UNIT`, `HUNIT`, `originX/Y` globally
- Reusable helper functions (`block()`, `studs_on_top()`, `cone_roof()`, etc.)
- Output is clean, consistent SVG every time

See `templates/isometric-scene-generator.py` for a reusable starter template.

## Verification Workflow

1. Run generator: `python3 generate.py`
2. Validate XML: `xmllint --noout output.svg`
3. Open in browser: `open output.svg`
4. Use `browser_vision` or `vision_analyze` to evaluate:
   - Does it read clearly as the intended subject?
   - Are z-order overlaps correct (back behind front)?
   - Are colors readable or muddy?
   - Any floating/misaligned elements?
5. Iterate on opacity values and positions, regenerate
