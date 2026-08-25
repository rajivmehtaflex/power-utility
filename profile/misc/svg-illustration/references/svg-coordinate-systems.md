# SVG Coordinate Systems and Transforms

## Key Pitfall: Transformed Groups Use Relative Coordinates

**Problem:** When using `transform="translate(x, y)"` on a `<g>` element, all child coordinates are relative to that transformed origin, not the global SVG coordinate system.

**Example bug:**

```svg
<g transform="translate(400, 320)">
  <!-- Body centered at (0, -20) relative to group origin at (400, 320) -->
  <ellipse cx="0" cy="-20" rx="60" ry="70" fill="purple" />
  
  <!-- WRONG: Uses global coordinates inside transformed group -->
  <ellipse cx="380" cy="-50" rx="25" ry="20" fill="white" opacity="0.15" />
  
  <!-- CORRECT: Uses coordinates relative to group origin -->
  <ellipse cx="-20" cy="-50" rx="25" ry="20" fill="white" opacity="0.15" />
</g>
```

## Rules

1. **Transformed groups create a new coordinate system**: All `x`, `y`, `cx`, `cy` attributes inside a `<g transform="...">` are relative to that group's transformed origin.

2. **Think locally**: When working inside a transformed group, ask "where is this relative to the group origin?" not "where is this on the canvas?"

3. **Debug by checking**: If an element appears at the wrong location, verify whether its parent group has a `transform` attribute.

4. **Nested transforms**: When groups are nested, transforms compose:
   ```svg
   <g transform="translate(100, 100)">
     <g transform="translate(50, 50)">
       <!-- Elements here are at (150, 150) in global coordinates,
            but use (0, 0) in their local coordinates -->
     </g>
   </g>
   ```

## Best Practices

- Keep transformed groups small and purposeful
- Document the transform intent in comments
- For complex compositions, consider flattening transforms if possible
- Use browser tools or SVG viewers to debug positioning visually

## Verification

```bash
# Validate SVG syntax
xmllint --noout file.svg

# Open in browser for visual verification
open file.svg  # macOS
xdg-open file.svg  # Linux
```

## Related Examples

See `references/octopus-organ-example.md` for a real-world illustration where this pitfall occurred (highlight ellipse positioning).