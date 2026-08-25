# Render verification and `<use>` scaling notes

Session-derived lessons for SVG illustration work:

## Why text review was not enough
A solar-panel cluster looked correct in SVG source but rendered as a large sky-blue grid because the repeated `<use>` instances lacked explicit sizing and scale control. The raster output revealed a composition bug that code inspection alone missed.

## What to do
1. **Render every complex SVG to PNG** before delivery when visual realism matters.
2. **Inspect the raster output** for accidental dominance, misleading scale, or wrong z-order.
3. When reusing symbols with `<use>`:
   - set explicit `width` / `height`, or
   - apply a deliberate `transform="scale(...)"`
4. Recheck after every patch; the bug may be fixed in code but still wrong in the rendered image.

## Failure pattern to watch for
- A technically correct symbol becomes a visual artifact because it is too large or placed too low/high.
- The scene reads as a UI overlay or grid instead of a physical object.
- The issue is often easiest to spot in the PNG, not the XML.
