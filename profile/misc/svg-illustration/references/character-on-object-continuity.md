# Character-on-Object SVG Continuity Lessons

Use this reference when drawing a character riding, sitting on, holding, or otherwise interacting with an object.

## Failure Pattern Observed

A first pass at a pelican riding a bicycle was recognizable but visually broken:

- Body, neck, and head were separate shapes/groups and looked detached.
- Legs and feet were placed approximately, so the feet appeared to float near the pedals rather than rest on them.
- The wing reached toward the handlebars, but its origin made it look attached to the wrong body region.
- Visual inspection caught issues that XML validation could not catch.

## Durable Fix Pattern

For connected anatomy, prefer a unified silhouette path:

```xml
<path id="body-neck-head" class="ink" fill="url(#bodyGradient)"
      d="M350 365 C298 366 272 318 286 270
         C298 226 338 205 382 229
         C415 199 456 175 494 164
         C527 155 558 168 560 190
         C562 212 528 225 490 214
         C458 233 431 270 421 312
         C411 354 385 365 350 365 Z"/>
```

This avoids seam/gap problems caused by separate body, neck, and head groups with different transforms or strokes.

## Z-Order Pattern

For a riding pose, draw back-to-front:

1. Object/vehicle base.
2. Rear/behind limbs, e.g. `<g id="legs-behind-body">`.
3. Unified body/neck/head silhouette.
4. Tail or rear details if they should overlap the body edge.
5. Front limbs/wings/hands interacting with controls.
6. Beak/face/details.
7. Feet/hands exactly on top of pedals/handles/contact points.

## Contact-Point Alignment

Approximate contact points are the most common source of a "floating" look. Instead:

- Define pedal/handle/seat coordinates first.
- Reuse those exact coordinates for limb endpoints and foot/hand center points.
- Match rotation between object contact surfaces and body parts.

Example pedal alignment:

```xml
<line class="thin" x1="410" y1="430" x2="385" y2="397"/>
<rect x="358" y="390" width="54" height="14" rx="7" fill="#27313d" transform="rotate(-15 385 397)"/>

<path class="leg" d="M335 345 C350 375 368 392 385 397"/>
<ellipse cx="385" cy="397" rx="25" ry="10" fill="#e8912d"
         stroke="#27313d" stroke-width="3" transform="rotate(-15 385 397)"/>
```

## Verification Checklist

After XML validation, always visually inspect for:

- The character reads as one connected body, not floating parts.
- Limbs originate from anatomically plausible places.
- Feet/hands/paws sit exactly on pedals/handles/surfaces.
- Object interaction is clear: steering, pedaling, sitting, holding, etc.
- No clipping and no unwanted decorative background artifacts.
- For cyclic motion cues like bicycling: opposite crank arms are ~180° apart, not overlapping by accident.
- For steering/grip interactions: one limb must make explicit contact with the control point; otherwise the scene implies non-functional control.

If any connected anatomy looks detached, rewrite the main silhouette as one continuous path rather than trying to patch gaps with small overlap shapes.

## Iterative Render-Review Loop

A first SVG can pass XML validation and still be physically implausible. The durable fix is an iterative loop:

1. Generate SVG.
2. Render to PNG with `rsvg-convert -o <path> <svg>`.
3. Review the render against user-stated realism/physics constraints.
4. Patch SVG until the render satisfies those constraints.
5. Only then deliver.

This loop worked for a pelican-on-bicycle request where the first two passes failed visual review on pedaling alignment and handlebar grip, then succeeded on the third pass.
