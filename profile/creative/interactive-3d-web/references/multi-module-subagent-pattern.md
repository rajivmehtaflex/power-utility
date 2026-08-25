# Multi-Module Subagent Pattern for Three.js Scenes

## Problem

Building a complex 3D scene (e.g., a furniture model with lighting, ground, UI) as a single monolithic HTML file is inherently sequential — only one person/agent can work on it at a time. When using `delegate_task` to parallelize, all subagents would be editing the same file → conflicts.

## Solution: Decompose by concern, contract the API

### 1. Create a config module first (Wave 0 — sequential)

This is the **contract** that all parallel tasks depend on. It defines shared constants (dimensions, colors, camera/light options) as plain data exports — no THREE dependency needed.

```javascript
// js/config.js
export const DIMS = { WIDTH: 45, HEIGHT: 86, ... };
export const COLORS = { WOOD: 0x8B5E3C, BG: 0x0a0a12, ... };
export const CAMERA_OPTS = { FOV: 45, INITIAL_POS: [90, 75, 120], ... };
```

### 2. Create independent feature modules (Wave 1 — parallel)

Each module exports a single factory function that receives `THREE` as a parameter. This is the critical design choice — modules don't import THREE from CDN, so they can be syntax-checked with `node --check` without a browser.

```
config.js       →  export const DIMS, COLORS, OPTS
environment.js  →  export function createEnvMap(THREE) → THREE.CanvasTexture
lighting.js     →  export function createLighting(scene, THREE) → { keyLight, ... }
model.js        →  export function createModel(envMap, THREE) → THREE.Group
ground.js       →  export function createGround(scene, THREE) → { shadowPlane, floor }
ui.js           →  export function setupUI(controls, camera, THREE) → { btnRotate, ... }
```

### 3. Assemble in index.html (Wave 2 — sequential, depends on all modules)

The integrator imports THREE from CDN + all local modules, creates the scene/camera/renderer, calls each factory, and wires results together.

### 4. Dependency graph for dispatch

```
Wave 0:  config.js (sequential — all modules import this)
             │
    ┌────────┼─────────────────┐
    ▼        ▼                 ▼
Wave 1:  environment.js  lighting.js  model.js  ground.js  ui.js
    (all parallel, each writes a DIFFERENT file — zero conflict)
             │
             ▼
Wave 2:  index.html (sequential — imports all modules)
```

### 5. Verification

```bash
# Syntax check all modules without a browser
for f in js/*.js; do node --check "$f" && echo "✓ $f"; done

# Local testing requires HTTP server (file:// blocks ES module imports)
python3 -m http.server 8080
open http://localhost:8080
```

## Subagent dispatch tips

- Give each subagent the **exact file path** and the **complete function signature** it must export
- Include relevant constants from config.js in the goal description so the subagent knows the parameter names
- The integrator subagent should **verify all module files exist** and **read their export names** before writing index.html
- Each subagent writing a different file = zero merge conflict risk
- If a subagent fails to produce its file, create it directly — the factory function pattern makes the code deterministic

## Real-world scale considerations

When 1 unit = 1 cm (real-world scale), several defaults from the compact-scene pattern must be adjusted:

| Setting | Compact scene (units ~1-20) | Real-world scale (units ~1-100) |
|---------|-----------------------------|--------------------------------|
| Shadow camera bounds | ±18 | ±80 (match scene bounding box) |
| Camera distance | 8–60 | 50–400 |
| OrbitControls target Y | ~4 | ~40 (seat height) |
| Fog near/far | 30–100 | 120–350 |
| Ground plane size | 28 radius | 600×600 |
| Shadow map size | 2048×2048 | 2048×2048 (same, just larger bounds) |
