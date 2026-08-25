# Pelican on Bicycle SVG Template

This is the complete SVG code from a successful illustration session. Use as a reference for character-on-object illustrations.

**Key patterns used:**
- Character body positioned on seat/structure
- Legs extending down to pedals/footrests
- Wings folded on sides (gray layering)
- Beak with gradient and pouch detail
- Bicycle frame with red color scheme
- 12-spoke wheels with proper spacing

**Coordinate system:** 800x600 viewBox, character centered at x=400

**User preference captured:** Pure SVG output, no HTML wrapper, no decorative artifacts (title/shadows/ground/grass).

> **Superseded for realism requests:** For requests requiring realistic pedaling, steering, or near-real-world physics, see `references/character-on-object-continuity.md`'s **Iterative Render-Review Loop**, and note that this example should be treated as a quick reference only. Its callback kinematics and wing/wing-contact geometry are not physically complete.

---

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="800" height="600">
    <!-- Wheels with spokes (12 each, rotated by 30°) -->
    <g id="rear-wheel" transform="translate(200, 420)">
        <circle cx="0" cy="0" r="70" fill="none" stroke="#2c2c2c" stroke-width="12"/>
        <circle cx="0" cy="0" r="64" fill="none" stroke="#4a4a4a" stroke-width="2"/>
        <circle cx="0" cy="0" r="58" fill="none" stroke="#888" stroke-width="3"/>
        <circle cx="0" cy="0" r="8" fill="#666" stroke="#444" stroke-width="1"/>
        <g stroke="#aaa" stroke-width="1.5">
            <line x1="0" y1="-58" x2="0" y2="-8"/>
            <line x1="0" y1="-58" x2="0" y2="-8" transform="rotate(30)"/>
            <line x1="0" y1="-58" x2="0" y2="-8" transform="rotate(60)"/>
            <line x1="0" y1="-58" x2="0" y2="-8" transform="rotate(90)"/>
            <line x1="0" y1="-58" x2="0" y2="-8" transform="rotate(120)"/>
            <line x1="0" y1="-58" x2="0" y2="-8" transform="rotate(150)"/>
            <line x1="0" y1="-58" x2="0" y2="-8" transform="rotate(180)"/>
            <line x1="0" y1="-58" x2="0" y2="-8" transform="rotate(210)"/>
            <line x1="0" y1="-58" x2="0" y2="-8" transform="rotate(240)"/>
            <line x1="0" y1="-58" x2="0" y2="-8" transform="rotate(270)"/>
            <line x1="0" y1="-58" x2="0" y2="-8" transform="rotate(300)"/>
            <line x1="0" y1="-58" x2="0" y2="-8" transform="rotate(330)"/>
        </g>
    </g>

    <!-- Front wheel (identical, different position) -->
    <g id="front-wheel" transform="translate(600, 420)">
        <!-- Same wheel structure -->
    </g>

    <!-- Bicycle frame (red, stroke-width 6) -->
    <g stroke="#e63946" stroke-width="6" stroke-linecap="round" fill="none">
        <line x1="200" y1="420" x2="400" y2="320"/>
        <line x1="400" y1="280" x2="600" y2="420"/>
        <line x1="400" y1="320" x2="400" y2="280"/>
        <line x1="400" y1="280" x2="200" y2="420"/>
        <line x1="400" y1="320" x2="200" y2="420"/>
        <line x1="600" y1="420" x2="580" y2="280"/>
        <line x1="400" y1="280" x2="580" y2="280"/>
    </g>

    <!-- Frame joints -->
    <g fill="#333">
        <circle cx="400" cy="320" r="6"/>
        <circle cx="400" cy="280" r="6"/>
        <circle cx="200" cy="420" r="6"/>
        <circle cx="600" cy="420" r="6"/>
        <circle cx="580" cy="280" r="6"/>
    </g>

    <!-- Fork, handlebars, seat, pedals, chainring -->
    <!-- See full SVG for details -->

    <!-- Pelican body (white/cream) -->
    <g id="pelican-body">
        <ellipse cx="400" cy="180" rx="55" ry="45" fill="#f5f5f5" stroke="#d3d3d3" stroke-width="2"/>
        <ellipse cx="400" cy="180" rx="55" ry="45" fill="url(#bodyGradient)" opacity="0.3"/>
        <ellipse cx="400" cy="195" rx="40" ry="30" fill="#fffaf0" stroke="#e8e8e8" stroke-width="1"/>
    </g>

    <!-- Pelican beak with pouch (orange) -->
    <g id="pelican-head">
        <path d="M 445 165 Q 520 155 540 175 Q 530 180 520 178 Q 480 170 445 175"
              fill="url(#beakGradient)" stroke="#e65100" stroke-width="1.5"/>
        <path d="M 445 170 Q 480 165 520 172" fill="none" stroke="#e65100" stroke-width="1"/>
        <path d="M 445 175 Q 480 180 515 175 Q 530 185 520 200 Q 500 215 460 200 Q 440 190 445 175"
              fill="#ffb74d" stroke="#e65100" stroke-width="1.5"/>
        <path d="M 455 185 Q 480 195 500 185" fill="none" stroke="#e65100" stroke-width="0.5" opacity="0.5"/>
        <path d="M 460 195 Q 480 205 490 195" fill="none" stroke="#e65100" stroke-width="0.5" opacity="0.5"/>
        <circle cx="538" cy="177" r="3" fill="#e65100"/>
    </g>

    <!-- Wings (gray, folded) -->
    <g id="pelican-wings">
        <!-- Left wing -->
        <path d="M 355 155 Q 330 170 340 200 Q 355 190 360 170 Q 365 160 355 155"
              fill="#666" stroke="#444" stroke-width="1"/>
        <path d="M 355 160 Q 340 175 345 195" fill="none" stroke="#555" stroke-width="1"/>
        <!-- Right wing -->
        <path d="M 445 155 Q 470 170 460 200 Q 445 190 440 170 Q 435 160 445 155"
              fill="#777" stroke="#555" stroke-width="1"/>
        <path d="M 445 160 Q 460 175 455 195" fill="none" stroke="#666" stroke-width="1"/>
    </g>

    <!-- Legs (orange, on pedals) -->
    <g id="pelican-legs">
        <path d="M 420 210 Q 430 250 435 300 Q 438 330 435 360"
              fill="none" stroke="#ff9800" stroke-width="4" stroke-linecap="round"/>
        <path d="M 425 365 Q 435 355 450 365 Q 455 370 450 375 Q 435 380 425 365"
              fill="#ffb74d" stroke="#e65100" stroke-width="1"/>
        <path d="M 380 210 Q 370 250 365 280 Q 362 300 360 320"
              fill="none" stroke="#ff9800" stroke-width="4" stroke-linecap="round" opacity="0.7"/>
        <path d="M 355 325 Q 345 315 330 325 Q 325 330 330 335 Q 345 340 355 325"
              fill="#ffb74d" stroke="#e65100" stroke-width="1" opacity="0.7"/>
    </g>

    <!-- Face with eye -->
    <g id="pelican-face">
        <ellipse cx="448" cy="158" rx="8" ry="7" fill="#fff" stroke="#ccc" stroke-width="1"/>
        <circle cx="450" cy="158" r="4" fill="#1a1a1a"/>
        <circle cx="452" cy="156" r="1.5" fill="#fff"/>
        <circle cx="448" cy="158" r="8" fill="none" stroke="#ffa726" stroke-width="1.5"/>
        <ellipse cx="430" cy="150" rx="20" ry="12" fill="#e8e8e8" opacity="0.5"/>
    </g>

    <!-- Gradient definitions (at top) -->
    <defs>
        <linearGradient id="bodyGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#fff;stop-opacity:0.5"/>
            <stop offset="100%" style="stop-color:#ccc;stop-opacity:0.5"/>
        </linearGradient>
        <linearGradient id="beakGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" style="stop-color:#ffcc80"/>
            <stop offset="100%" style="stop-color:#ffa726"/>
        </linearGradient>
    </defs>
</svg>
```

**Reusable techniques:**
1. Character-on-object: Position body on structure, extend limbs to contact points
2. Depth: Use opacity on "behind" elements (left leg/wing)
3. Detail: Add feather lines, pouch details with thin strokes
4. Structure: Group related parts with `<g id="name">` for organization
5. Colors: Cream body, gray wings, orange accents works well for birds