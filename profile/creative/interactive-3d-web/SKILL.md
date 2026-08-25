---
name: interactive-3d-web
description: "Build self-contained interactive 3D scenes with Three.js: orbit controls, translucent materials, lighting rigs, procedural environment maps. Single HTML file from CDN, no build step."
license: MIT
metadata:
  author: Hermes Agent
  hermes_related_skills: svg-illustration, html-artifact, claude-design
  hermes_tags: 3d, threejs, webgl, interactive, orbit, visualization, creative
  platforms: linux, macos, windows
  version: 1.0.0
---

# Interactive 3D Web Scenes

Build self-contained interactive 3D scenes using Three.js + OrbitControls. User can drag to rotate, scroll to zoom, right-drag to pan around 3D objects. Single HTML file loaded from CDN — no npm, no bundler, no dependencies to install.

## When to Use

- "Make it 3D" / "orbit view" / "rotatable" / "let me view it from all angles"
- Converting a 2D illustration (SVG, isometric art) into a true 3D interactive scene
- Interactive product visualizers, architectural models, game asset previews
- Any request for WebGL/Three.js 3D content in the browser

**Look elsewhere for:**
- Static SVG illustrations → `svg-illustration`
- 2D interactive demos → `html-artifact` or `p5js`
- Animated math videos → `manim-video`

## Output Location

Save to user-specified path, or default to:
```
~/<subject>-3d.html
```

## Architecture Pattern

Every scene follows this structure:

1. **HTML skeleton** — `<canvas>` filling viewport, UI overlay divs, Three.js CDN via import map
2. **Scene setup** — Scene, PerspectiveCamera, WebGLRenderer with shadows + tone mapping
3. **Lighting rig** — Ambient + directional (key) + directional (fill) + point (rim) + hemisphere
4. **Environment map** — Procedural canvas-generated gradient for realistic reflections
5. **Geometry builders** — Reusable functions that create meshes from data arrays
6. **OrbitControls** — Damped orbit, zoom, pan with angle constraints
7. **UI controls** — Auto-rotate toggle, reset view button
8. **Animation loop** — `requestAnimationFrame` with `controls.update()` + `renderer.render()`

## CDN Setup (ES Modules)

```html
<script type="importmap">
{
  "imports": {
    "three": "https://unpkg.com/three@0.160.0/build/three.module.js",
    "three/addons/": "https://unpkg.com/three@0.160.0/examples/jsm/"
  }
}
</script>
<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
// ... scene code ...
</script>
```

Always use ES module imports via import map — the old `three.min.js` global script approach is deprecated.

## Translucent / Glass-Plastic Material

For LEGO, glass, crystal, or any translucent plastic look:

```javascript
function brickMaterial(hex, opacity = 0.72) {
  return new THREE.MeshPhysicalMaterial({
    color: hex,
    metalness: 0.0,
    roughness: 0.38,
    transmission: 0.35,        // glass-like refraction
    transparent: true,
    opacity: opacity,
    thickness: 0.6,            // volume for refraction depth
    ior: 1.3,                  // plastic refractive index (glass = 1.5)
    clearcoat: 0.35,
    clearcoatRoughness: 0.2,
    side: THREE.DoubleSide,    // visible from inside when orbiting
    envMap: envMap,
    envMapIntensity: 0.85,
  });
}
```

**Pitfall:** `transmission` is expensive. If FPS drops, set `transmission: 0` and rely on `opacity` alone.

**Pitfall:** `DoubleSide` doubles fragment cost but is REQUIRED so the scene looks correct when orbiting behind/inside objects.

## Grid → World Coordinate Mapping

When porting 2D grid-based designs to 3D:

```javascript
const GRID_CENTER = 7;       // grid spans 0–14, center at 7
const HEIGHT_RATIO = 0.8;    // height units shorter than width

function gridToWorld(bx, by, bz) {
  return {
    x: bx - GRID_CENTER,          // X axis: right
    y: bz * HEIGHT_RATIO,         // Y axis: up
    z: -(by - GRID_CENTER)        // Z axis: forward (negated for Three.js convention)
  };
}
```

## Lighting Rig (Always Use This Setup)

```javascript
// Ambient — fills shadows so translucency reads
const ambient = new THREE.AmbientLight(0x4a5a8a, 0.55);

// Key light — warm directional from upper-right, casts shadows
const keyLight = new THREE.DirectionalLight(0xfff4e0, 1.4);
keyLight.position.set(15, 26, 15);
keyLight.castShadow = true;
keyLight.shadow.mapSize.set(2048, 2048);
keyLight.shadow.camera.left = -18;
keyLight.shadow.camera.right = 18;
keyLight.shadow.camera.top = 18;
keyLight.shadow.camera.bottom = -18;
keyLight.shadow.bias = -0.0004;

// Fill light — cool blue from opposite side
const fillLight = new THREE.DirectionalLight(0x6080ff, 0.45);
fillLight.position.set(-14, 14, -10);

// Rim light — magenta accent from behind
const rimLight = new THREE.PointLight(0xff4080, 1.0, 55);
rimLight.position.set(0, 8, -18);

// Hemisphere — subtle sky/ground bounce
const hemi = new THREE.HemisphereLight(0x8899ff, 0x080820, 0.25);
```

## Procedural Environment Map (No HDRI File Needed)

Generate a gradient environment from a canvas — gives realistic reflections without loading external HDRI files:

```javascript
function createEnvMap() {
  const c = document.createElement('canvas');
  c.width = 512; c.height = 256;
  const ctx = c.getContext('2d');
  const g = ctx.createLinearGradient(0, 0, 0, 256);
  g.addColorStop(0, '#2a3a5a');
  g.addColorStop(0.5, '#5a6a8a');
  g.addColorStop(1, '#080c18');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, 512, 256);
  // Light blobs for reflection highlights
  ctx.fillStyle = 'rgba(255,240,200,0.35)';
  ctx.beginPath(); ctx.arc(380, 50, 35, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = 'rgba(100,160,255,0.22)';
  ctx.beginPath(); ctx.arc(110, 80, 45, 0, Math.PI * 2); ctx.fill();

  const tex = new THREE.CanvasTexture(c);
  tex.mapping = THREE.EquirectangularReflectionMapping;
  return tex;
}
const envMap = createEnvMap();
scene.environment = envMap;
```

## OrbitControls Setup

```javascript
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;           // smooth rotation
controls.dampingFactor = 0.08;
controls.minDistance = 8;                // prevent zoom-through
controls.maxDistance = 60;
controls.maxPolarAngle = Math.PI * 0.48; // prevent going below ground
controls.target.set(0, 4, 0);            // look at scene center
controls.autoRotate = true;              // cinematic spin by default
controls.autoRotateSpeed = 1.2;
```

Must call `controls.update()` every frame in the animation loop when damping or auto-rotate is enabled.

## Shadow Ground Plane

```javascript
const groundGeo = new THREE.CircleGeometry(28, 64);
const groundMat = new THREE.ShadowMaterial({ opacity: 0.4 });
const ground = new THREE.Mesh(groundGeo, groundMat);
ground.rotation.x = -Math.PI / 2;
ground.position.y = -0.01;
ground.receiveShadow = true;
```

Every brick mesh must have `castShadow = true` and `receiveShadow = true`.

## UI Overlay Pattern

Fixed-position divs with `pointer-events: none` on containers, `pointer-events: auto` on interactive elements. Dark semi-transparent buttons with backdrop blur:

```css
button {
  background: rgba(30,41,59,0.85);
  border: 1px solid rgba(99,102,241,0.4);
  border-radius: 8px;
  backdrop-filter: blur(8px);
  /* ... */
}
```

## Renderer Settings

```javascript
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.15;
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));  // cap at 2 for perf
```

## Common Pitfalls

- **Missing `controls.update()` in animation loop** → damping and auto-rotate silently stop working
- **`maxPolarAngle` too high** → camera goes under the ground plane, showing the scene from below
- **No `ShadowMaterial` on ground** → shadows invisible; ShadowMaterial makes ground transparent except where shadows fall
- **Cone roofs look like pyramids** → use `ConeGeometry(radius, height, 8)` for 8-sided (octagonal) instead of default 4-sided
- **Flags invisible from one side** → `ShapeGeometry` is single-sided; use `DoubleSide` material or duplicate geometry
- **Z-fighting on overlapping faces** → offset coplanar meshes by 0.01–0.05 units
- **Forgetting `window.resize` handler** → canvas doesn't fill viewport after window resize

## Verification

```bash
# Open in browser
open ~/scene-3d.html          # macOS
xdg-open ~/scene-3d.html      # Linux

# Check console for errors (DevTools)
```

Check:
- [ ] No console errors
- [ ] Mouse drag rotates camera (orbit)
- [ ] Scroll wheel zooms in/out
- [ ] Right-drag pans
- [ ] Auto-rotate toggle works
- [ ] Reset View returns to default camera
- [ ] Shadows visible on ground
- [ ] Translucency reads correctly from all orbit angles
- [ ] 60fps performance (check DevTools Performance tab)

## Multi-Module Architecture (for Parallel / Subagent Development)

The default pattern above keeps everything in one HTML file. When the scene is complex or you want to parallelize development (especially via `delegate_task` subagents), split into independent JS modules that each export a factory function.

**Key principle:** Each module receives `THREE` as a **parameter** — it does NOT import from CDN. Only the integrator `index.html` imports THREE from CDN and passes it down. This lets each module be syntax-checked standalone (`node --check`) without a browser.

### Module API contract pattern

```
config.js       →  export const DIMS, COLORS, OPTS (plain data, no THREE needed)
environment.js  →  export function createEnvMap(THREE) → THREE.CanvasTexture
lighting.js     →  export function createLighting(scene, THREE) → { keyLight, ... }
geometry.js     →  export function createModel(envMap, THREE) → THREE.Group
ground.js       →  export function createGround(scene, THREE) → { shadowPlane, floor }
ui.js           →  export function setupUI(controls, camera, THREE) → { btnRotate, ... }
```

### Integrator (index.html) wiring

```javascript
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { COLORS, CAMERA_OPTS } from './js/config.js';
import { createEnvMap } from './js/environment.js';
// ... other imports

const envMap = createEnvMap(THREE);       // pass THREE down
createLighting(scene, THREE);
const model = createModel(envMap, THREE);
scene.add(model);
```

### When to use multi-module vs single-file

| Factor | Single HTML | Multi-Module |
|--------|-------------|-------------|
| Scene complexity | Simple (1-2 objects) | Complex (furniture, architecture, multi-part) |
| Parallel development | Not needed | Subagent dispatch (5+ files simultaneously) |
| Local testing | `open file.html` works | **Must use HTTP server** (see pitfall below) |
| Deployment | Drag-drop anywhere | Needs directory structure preserved |

See `references/multi-module-subagent-pattern.md` for the full dependency-graph and API-contract design used to decompose a chair model into 5 parallel subagent tasks.

## Common Pitfalls (additional)

- **`file://` protocol fails for local ES module imports** → Browsers block `import` from `file://` URLs due to CORS. When using multi-module architecture, start a local HTTP server: `python3 -m http.server 8080`, then open `http://localhost:8080`. Single-file HTML (all code inline) works fine with `file://`.
- **Shadow camera bounds too small** → At real-world scale (1 unit = 1 cm), shadow camera bounds must be much larger. A chair ~86cm tall needs `shadow.camera.left/right/top/bottom = ±80`, not the ±18 shown in the compact-scene defaults above. Scale shadow bounds to your scene's bounding box.
- **TorusGeometry wheel orientation** → A `TorusGeometry` default lies in the XY plane facing +Z. For a wheel that rolls forward (spins on the X axis, faces the Z direction of travel), you must rotate it: `tire.rotation.y = Math.PI / 2`. Forgetting this makes wheels face sideways. Similarly, spokes inside the wheel must rotate around the axle axis (X), not Z. Test visually before committing.
- **Cylinder axis confusion** → `CylinderGeometry` defaults along the Y axis. To make a horizontal axle along X: `rotation.z = Math.PI / 2`. To make it horizontal along Z: `rotation.x = Math.PI / 2`. When building frames from cylinders, use `quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0), direction.normalize())` for arbitrary angles instead of guessing Euler rotations.
- **Subagent-produced geometry is syntactically valid but visually wrong** → `node --check` passes but wheels float, parts detach, or handlebars appear in mid-air. After any subagent-generated geometry, ALWAYS run `browser_vision` with a specific question like "are all parts attached, any floating geometry?" before accepting the work. See "Visual Verification" below.

## Visual Verification (Mandatory for Complex Geometry)

Syntax checks (`node --check`) catch import/parse errors but NOT spatial bugs — floating wheels, detached handlebars, clipping meshes, wrong-facing beaks. For any scene with more than ~5 meshes, always verify visually before accepting:

1. Start local server: `python3 -m http.server 8080`
2. Navigate browser to `http://localhost:8080`
3. Run `browser_console` to confirm no JS errors
4. Run `browser_vision` with a **specific question** — not "does it look OK?" but "are all 3 wheels attached to the frame? Are handlebars at the top of the fork, not floating? Is the pelican seated, not clipping through the seat?"
5. Click each UI button and re-check console for errors

### Visual verification question patterns

Ask about **specific spatial relationships**, not general appearance:
- ✅ "Are all wheels touching the ground plane? Are any parts floating or detached?"
- ✅ "Is object A sitting on top of object B, not clipping through it?"
- ✅ "Is the beak pointing in the direction of travel (+Z)?"
- ❌ "Does it look good?" (too vague — vision model may rubber-stamp)

### Fix loop for subagent geometry

When `browser_vision` reports floating/detached parts:
1. Read the offending module file to identify positioning math
2. Common causes: wrong rotation axis, wrong position coordinate, cylinder/torus not oriented
3. Rewrite the specific mesh positions, re-`node --check`, re-verify visually
4. The factory-function pattern means you only need to fix one module, not the whole scene

See `references/procedural-character-vehicle-geometry.md` for worked examples of building multi-part organic + mechanical objects from Three.js primitives.

## Converting from 2D Isometric SVG

When a 2D isometric SVG already exists (see `svg-illustration` skill):

1. Extract grid coordinates from the generator script — they map directly to 3D
2. Each SVG `<path>` block becomes a `BoxGeometry` mesh
3. Each SVG stud becomes a `CylinderGeometry` mesh
4. Each SVG cone roof becomes a `ConeGeometry` mesh
5. `fill-opacity` values carry over as `material.opacity` (add `transmission: 0.35` for extra glass effect)
6. The 3-shade color trick (top/right/left) is no longer needed — real 3D lighting handles shading automatically

See `references/isometric-svg.md` in the `svg-illustration` skill for the projection math and block patterns.
