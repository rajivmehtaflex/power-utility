# Physics-coherent environmental SVG scenes

Use this reference when the SVG request asks for weather, storms, vehicles, structures under load, technical overlays, or "near to ground reality" physical coherence.

## Plan the scene as a single physical model

Before drawing, write a short model and keep every visual cue consistent with it:

- **Coordinate convention:** SVG screen coordinates have +Y downward. A real-world vector that is "rightward and slightly upward" should use a negative rotation angle such as `rotate(-8 ...)`, not positive.
- **Wind:** Pick one wind vector and apply it to every dependent element: flags, snow/rain streaks, smoke, balloon/tether lean, drone attitude/trails, turbine yaw, HUD arrows, snow drift placement.
- **Lee-side accumulation:** If wind blows left-to-right, drifts should bulge on the right/downwind side of buildings, barriers, masts, and terrain breaks. Windward faces are scoured.
- **Lightning:** Route strikes to conductive high points only: rods, grounded masts, turbine hubs/nacelles, towers. Add visible impact rings/crosshairs/glow at the exact contact points and show grounding cables if relevant.
- **Structures under load:** Use buttresses, X-bracing, guy wires, anchored bases, and cable sag differences. Guy wires should be taut straight lines; data/power cables can sag.
- **Turbines:** Nacelles/rotor planes should face into the wind. Use sweep arcs/dashed circles for implied rotation, but keep the tower vertical and grounded.
- **Drones/balloons:** Balloons and tethers drift downwind. Hovering drones may tilt upwind into the wind while their downwash/trails drift downwind; label this visually if ambiguity is possible.

## Complex technical overlays

For semi-transparent dashboards/HUDs:

- Use a `clipPath` for the panel boundary and, if fading/vignetting is needed, a real SVG `mask` (not just opacity) so it satisfies mask requirements.
- Keep HUD arrows aligned to the same environmental vector as the scene.
- Place HUD after scene geometry but before final labels if labels must remain readable. Final labels/callouts usually belong in the last group.
- Avoid label boxes under translucent overlays. If the HUD covers an instrument, move the label outside the HUD and reroute the leader.

## Render-backed QA checklist

After rendering to PNG, ask vision to inspect for these specific failure modes:

1. Do all direction cues agree with the declared physical vector? Remember +Y-down angle signs.
2. Are strike/glow endpoints exactly on conductive targets, not visually in empty air or behind objects?
3. Are callout dots and leaders attached to their targets without crossing turbines, tethers, lightning, or dashboard borders?
4. Are repeated assets actually plural and visible, not hidden behind panels or mountains?
5. Did transforms, scaling, or `<use>` references create orphaned or mis-sized elements?
6. Does text contain accidental artifacts/typos introduced during patches?

## Lightweight text validation before final

In addition to XML parsing, run a reference check conceptually or with a small script:

- collect all `id="..."`
- collect all `href="#..."` and `url(#...)`
- report missing refs
- verify the exact `viewBox` requested
- grep/count required plural elements if the prompt asks for plurals

Do not rely on XML validity alone; visually correct physical coherence needs at least one render-backed pass.