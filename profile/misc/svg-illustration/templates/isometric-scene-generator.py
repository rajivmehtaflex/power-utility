#!/usr/bin/env python3
"""
Reusable isometric 3D SVG scene generator template.

USAGE:
  1. Copy this file: cp templates/isometric-scene-generator.py ~/my-scene.py
  2. Edit the BUILD SCENE section with your components
  3. Run: python3 ~/my-scene.py
  4. Output: ~/my-scene.svg

Customize UNIT, HUNIT, originX/Y, COLORS, and the component layout.
"""
import math
import sys

# ════════════════════════════════════════════════════════════
# PROJECTION CONSTANTS — tune these for your scene
# ════════════════════════════════════════════════════════════
ORIGIN_X = 400
ORIGIN_Y = 370
UNIT = 26           # horizontal grid spacing (px)
HUNIT = 20          # vertical height per level (px)
ISO_COS = math.sqrt(3) / 2
ISO_SIN = 0.5

# ════════════════════════════════════════════════════════════
# COLOR PALETTE — 3 shades each (top=lightest, right=medium, left=darkest)
# Add your own colors here. Darken ~15% per step.
# ════════════════════════════════════════════════════════════
COLORS = {
    "blue":   {"top": "#60a5fa", "right": "#3b82f6", "left": "#1d4ed8"},
    "red":    {"top": "#f87171", "right": "#ef4444", "left": "#b91c1c"},
    "yellow": {"top": "#fde047", "right": "#facc15", "left": "#ca8a04"},
    "green":  {"top": "#4ade80", "right": "#22c55e", "left": "#15803d"},
    "purple": {"top": "#a78bfa", "right": "#8b5cf6", "left": "#6d28d9"},
    "orange": {"top": "#fdba74", "right": "#fb923c", "left": "#c2410c"},
    "cyan":   {"top": "#38bdf8", "right": "#0ea5e9", "left": "#0369a1"},
    "white":  {"top": "#f8fafc", "right": "#e2e8f0", "left": "#cbd5e1"},
}

# ════════════════════════════════════════════════════════════
# PROJECTION FUNCTION
# ════════════════════════════════════════════════════════════
def proj(bx, by, bz):
    """Project 3D grid coords (bx, by, bz) to 2D screen 'sx,sy' string."""
    sx = ORIGIN_X + (bx - by) * ISO_COS * UNIT
    sy = ORIGIN_Y + (bx + by) * ISO_SIN * UNIT - bz * HUNIT
    return f"{sx:.1f},{sy:.1f}"

# ════════════════════════════════════════════════════════════
# SVG BUILDER HELPERS
# ════════════════════════════════════════════════════════════
def block(bx0, by0, bz0, bx1, by1, bz1, color, opacity=0.72):
    """Draw a solid 3D block. Three visible faces: top, right, left."""
    c = COLORS[color]
    parts = []
    # LEFT WALL (by=by1, darkest)
    pts = [proj(bx0,by1,bz0), proj(bx1,by1,bz0), proj(bx1,by1,bz1), proj(bx0,by1,bz1)]
    parts.append(f'<path d="M {pts[0]} L {pts[1]} L {pts[2]} L {pts[3]} Z" '
                 f'fill="{c["left"]}" fill-opacity="{opacity:.2f}"/>')
    # RIGHT WALL (bx=bx1, medium)
    pts = [proj(bx1,by0,bz0), proj(bx1,by1,bz0), proj(bx1,by1,bz1), proj(bx1,by0,bz1)]
    parts.append(f'<path d="M {pts[0]} L {pts[1]} L {pts[2]} L {pts[3]} Z" '
                 f'fill="{c["right"]}" fill-opacity="{opacity:.2f}"/>')
    # TOP FACE (bz=bz1, lightest)
    pts = [proj(bx0,by0,bz1), proj(bx1,by0,bz1), proj(bx1,by1,bz1), proj(bx0,by1,bz1)]
    parts.append(f'<path d="M {pts[0]} L {pts[1]} L {pts[2]} L {pts[3]} Z" '
                 f'fill="{c["top"]}" fill-opacity="{opacity+0.05:.2f}"/>')
    return "\n    ".join(parts)

def studs(bx0, by0, bx1, by1, bz, color, size=0.9):
    """Place LEGO-style studs on a visible top surface."""
    c = COLORS[color]
    parts = []
    r = 7 * size
    for gx in range(int(bx0), int(bx1)):
        for gy in range(int(by0), int(by1)):
            s = proj(gx + 0.5, gy + 0.5, bz)
            cx, cy = float(s.split(",")[0]), float(s.split(",")[1])
            parts.append(f'<ellipse cx="{cx:.1f}" cy="{cy+2:.1f}" rx="{r:.1f}" ry="{r/2:.1f}" '
                         f'fill="{c["left"]}" fill-opacity="0.55"/>')
            parts.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{r:.1f}" ry="{r/2:.1f}" '
                         f'fill="{c["top"]}" fill-opacity="0.75"/>')
            parts.append(f'<ellipse cx="{cx-2:.1f}" cy="{cy-1:.1f}" rx="{r*0.45:.1f}" ry="{r*0.25:.1f}" '
                         f'fill="#ffffff" fill-opacity="0.35"/>')
    return "\n    ".join(parts)

def cone_roof(bx0, by0, bx1, by1, bz_base, bz_apex, color, opacity=0.65):
    """Conical roof from square base to apex point."""
    c = COLORS[color]
    apex = proj((bx0+bx1)/2, (by0+by1)/2, bz_apex)
    ax, ay = apex.split(",")
    fr, rb = proj(bx1,by0,bz_base), proj(bx1,by1,bz_base)
    fl, lb = proj(bx0,by0,bz_base), proj(bx0,by1,bz_base)
    parts = []
    parts.append(f'<path d="M {fr} L {ax} L {rb} Z" fill="{c["right"]}" fill-opacity="{opacity:.2f}"/>')
    parts.append(f'<path d="M {fl} L {ax} L {lb} Z" fill="{c["left"]}" fill-opacity="{opacity:.2f}"/>')
    parts.append(f'<path d="M {fl} L {ax} L {fr} Z" fill="{c["top"]}" fill-opacity="{opacity+0.05:.2f}"/>')
    return "\n    ".join(parts)

def flag(ax_s, ay_s, height=35, color="red"):
    """Flag on a pole at position (ax, ay)."""
    c = COLORS[color]
    ax, ay = float(ax_s), float(ay_s)
    ptop = ay - height
    parts = []
    parts.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{ax:.1f}" y2="{ptop:.1f}" '
                 f'stroke="#fbbf24" stroke-width="2" opacity="0.85"/>')
    parts.append(f'<path d="M {ax:.1f},{ptop:.1f} L {ax+20:.1f},{ptop+7:.1f} L {ax:.1f},{ptop+14:.1f} Z" '
                 f'fill="{c["right"]}" fill-opacity="0.75"/>')
    parts.append(f'<circle cx="{ax:.1f}" cy="{ptop:.1f}" r="2.5" fill="#fde047" opacity="0.85"/>')
    return "\n    ".join(parts)

# ════════════════════════════════════════════════════════════
# BUILD SCENE — customize this section for your illustration
# ════════════════════════════════════════════════════════════
output_path = sys.argv[1] if len(sys.argv) > 1 else "~/my-scene.svg"
if output_path.startswith("~"):
    import os
    output_path = os.path.expanduser(output_path)

svg = []
svg.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800" width="800" height="800">')
svg.append("")

# Defs
svg.append('  <defs>')
svg.append('    <radialGradient id="bgGlow" cx="50%" cy="42%" r="55%">')
svg.append('      <stop offset="0%" stop-color="#1e293b"/>')
svg.append('      <stop offset="100%" stop-color="#0a0f1e"/>')
svg.append('    </radialGradient>')
svg.append('  </defs>')
svg.append('')

# Background
svg.append('  <rect x="0" y="0" width="800" height="800" fill="url(#bgGlow)"/>')
svg.append('')

# ── ADD YOUR COMPONENTS HERE (back to front z-order) ──
# Example: a simple building
svg.append('  <!-- EXAMPLE BUILDING -->')
svg.append('  <g id="building">')
svg.append('    ' + block(3, 3, 0, 9, 9, 6, "blue", opacity=0.72))
svg.append('    ' + studs(3, 3, 9, 9, 6, "blue"))
svg.append('    ' + cone_roof(3, 3, 9, 9, 6, 9, "orange"))
svg.append('  </g>')
svg.append('')

svg.append('</svg>')

# Write output
result = "\n".join(svg)
with open(output_path, "w") as f:
    f.write(result)
print(f"✓ SVG written: {output_path} ({len(result)} bytes)")
