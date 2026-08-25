# Parallel Execution Planning — Worked Example

Complete reference for decomposing a project into parallel subagent waves, using the Three.js 3D Chair Viewer as the worked example.

## Project Overview

**Task:** Build a self-contained 3D chair viewer (Three.js + OrbitControls) deployable to Netlify.

**Original plan:** 10 sequential tasks writing into one monolithic `index.html` — no parallelism possible.

**Restructured:** Decomposed into 6 independent JS modules + 1 integrator, enabling 5 parallel Wave 1 subagents.

## File Structure (After Decomposition)

```
project/
├── index.html              ← Wave 2: integrator
├── netlify.toml            ← Wave 4: deploy
└── js/
    ├── config.js           ← Wave 0: shared constants (THE CONTRACT)
    ├── environment.js      ← Wave 1A: procedural env map
    ├── lighting.js         ← Wave 1B: 5-light rig
    ├── chair.js            ← Wave 1C: chair geometry builder
    ├── ground.js           ← Wave 1D: shadow + floor planes
    └── ui.js               ← Wave 1E: UI overlay + controls
```

## Dependency Graph

```
WAVE 0 (Sequential — 1 subagent, ~3 min)
═════════════════════════════════════════
  ┌──────────────────────────────────┐
  │ T0: config.js + directory        │
  │ (defines all shared constants    │
  │  and module API contract)        │
  └───────────────┬──────────────────┘
                  │
    ┌─────────────┼─────────────────────────┐
    │             │                          │
    ▼             ▼                          ▼
WAVE 1 (Parallel — 5 subagents, ~5 min each, concurrent)
════════════════════════════════════════════════════════
  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
  │ T1A:     │ │ T1B:     │ │ T1C:     │ │ T1D:     │ │ T1E:     │
  │ Environ- │ │ Lighting │ │ Chair    │ │ Ground   │ │ UI       │
  │ ment.js  │ │ .js      │ │ .js      │ │ .js      │ │ .js      │
  │          │ │          │ │          │ │          │ │          │
  │ deps:    │ │ deps:    │ │ deps:    │ │ deps:    │ │ deps:    │
  │ config   │ │ config   │ │ config   │ │ config   │ │ config   │
  └─────┬────┘ └─────┬────┘ └─────┬────┘ └─────┬────┘ └─────┬────┘
        │            │            │            │            │
        └────────────┴────────────┼────────────┴────────────┘
                                  │
                                  ▼
WAVE 2 (Sequential — 1 subagent, ~5 min)
═══════════════════════════════════════════
  ┌────────────────────────────────────────┐
  │ T2: index.html integrator              │
  │ imports all 6 modules, creates scene/  │
  │ camera/renderer, OrbitControls,        │
  │ animation loop, wires everything       │
  └───────────────────┬────────────────────┘
                      │
                      ▼
WAVE 3 (Sequential — 1 subagent, ~3 min)
═══════════════════════════════════════════
  ┌────────────────────────────────────────┐
  │ T3: Browser verification               │
  │ starts HTTP server, opens index.html,  │
  │ checks console, 14-point checklist     │
  └───────────────────┬────────────────────┘
                      │
                      ▼
WAVE 4 (Sequential — 1 subagent, ~3 min)
═══════════════════════════════════════════
  ┌────────────────────────────────────────┐
  │ T4: Netlify deploy                     │
  └────────────────────────────────────────┘
```

## Module API Contract

This is THE critical boundary. Every Wave 1 subagent must conform to this:

```
config.js       → exports: CHAIR_DIMS, SEAT_Y, BACK_TOP_Y, COLORS, RENDERER_OPTS, CAMERA_OPTS, LIGHT_OPTS, SCENE_OPTS
environment.js  → export function createEnvMap(THREE) → returns THREE.CanvasTexture
lighting.js     → export function createLighting(scene, THREE) → returns { keyLight, fillLight, rimLight, ambient, hemi }
chair.js        → export function createChair(envMap, THREE) → returns THREE.Group
ground.js       → export function createGround(scene, THREE) → returns { shadowPlane, floor }
ui.js           → export function setupUI(controls, camera, THREE) → returns { btnRotate, btnReset }
```

**Key pattern:** Every factory function receives `THREE` as a parameter — only the integrator imports Three.js from CDN. This avoids version drift and keeps modules self-documenting about their Three.js dependency.

## Dispatch Pattern — Wave 1 (Parallel)

All 5 tasks dispatched via a SINGLE `delegate_task` call with `tasks: [...]`:

```
delegate_task(tasks: [
  {
    goal: "Create js/environment.js at /path/to/project. Export createEnvMap(THREE)...",
    context: "Part of Three.js 3D chair viewer. Config exists at js/config.js..."
  },
  {
    goal: "Create js/lighting.js at /path/to/project. Export createLighting(scene, THREE)...",
    context: "Import COLORS and LIGHT_OPTS from './config.js'..."
  },
  {
    goal: "Create js/chair.js at /path/to/project. Export createChair(envMap, THREE)...",
    context: "Import CHAIR_DIMS, SEAT_Y, BACK_TOP_Y, COLORS from './config.js'..."
  },
  {
    goal: "Create js/ground.js at /path/to/project. Export createGround(scene, THREE)...",
    context: "Import COLORS and SCENE_OPTS from './config.js'..."
  },
  {
    goal: "Create js/ui.js at /path/to/project. Export setupUI(controls, camera, THREE)...",
    context: "Import CAMERA_OPTS and SCENE_OPTS from './config.js'..."
  }
])
```

### What goes in each subagent's `context` field:

1. **Project context:** "Part of a Three.js 3D chair viewer"
2. **Import instructions:** Exact module path and named exports to import
3. **Export contract:** Exact function name and signature to export
4. **Parameter semantics:** What `THREE` means, what `scene` is, what `envMap` is
5. **Physical/domain constraints:** "1 unit = 1 cm, ISO 9241 standards, all meshes must castShadow + receiveShadow"
6. **Style guidelines:** "Dark glassmorphic UI, backdrop-filter blur"

## Dispatch Pattern — Cascading (Wave 1 + Wave 2 Together)

When confident in the contract, dispatch Wave 1 and Wave 2 together:

```
delegate_task(tasks: [
  // ... 5 Wave 1 tasks ...
  {
    goal: "Create index.html integrator. WAIT for all js/*.js files to exist first...",
    context: "The 5 JS modules are being created by parallel subagents right now.
              Before writing index.html, verify all 6 files exist and read each to
              confirm export names match. Key API contract: [list all signatures]..."
  }
])
```

**Risk:** The integrator subagent may start before Wave 1 files exist. Mitigate by:
- Explicitly stating "WAIT" in the goal
- Telling it to verify file existence first
- Providing the full API contract so it can check export names

## Task Decomposition Table Template

| ID | Task | Priority | Wave | Deps | Parallelizable |
|----|------|----------|------|------|----------------|
| T0 | Config/contract | P0 (critical) | 0 | none | No |
| T1A | Module A | P1 | 1 | T0 | Yes |
| T1B | Module B | P1 | 1 | T0 | Yes |
| T1C | Module C | P1 | 1 | T0 | Yes |
| T1D | Module D | P1 | 1 | T0 | Yes |
| T1E | Module E | P1 | 1 | T0 | Yes |
| T2 | Integrator | P0 (critical) | 2 | T0 + all T1x | No |
| T3 | Verify | P0 (critical) | 3 | T2 | No |
| T4 | Deploy | P2 | 4 | T3 | No |

## Performance Comparison

| Metric | Sequential | Subagent-Parallel | Savings |
|--------|-----------|-------------------|---------|
| Wall-clock time | ~35 min | ~18 min | ~48% |
| Peak concurrency | 1 | 5 subagents | — |
| Files | 2 | 8 (better separation) | — |

## Timeline Visualization

```
TIME →  0min        3min              8min         13min    16min   18min
        │            │                 │            │        │       │
WAVE 0: ████ T0      │                 │            │        │       │
WAVE 1:              ████████████ T1A ─┤            │        │       │
                     ████████████ T1B ─┤ (parallel) │        │       │
                     ████████████ T1C ─┤            │        │       │
                     ████████████ T1D ─┤            │        │       │
                     ████████████ T1E ─┤            │        │       │
WAVE 2:                              ████████████ T2┤        │       │
WAVE 3:                                             ██████ T3┤       │
WAVE 4:                                                      ██████ T4
```

## Common Decomposition Patterns

### Pattern: Library/Framework Project (Multiple Independent Components)

```
config.js (Wave 0)
├── components/Button.js     (Wave 1A)
├── components/Card.js       (Wave 1B)
├── components/Modal.js      (Wave 1C)
├── styles/theme.js          (Wave 1D)
└── App.jsx (Wave 2 — imports all)
```

### Pattern: API Service (Multiple Endpoints)

```
config.js (Wave 0 — DB models, shared types)
├── routes/users.js    (Wave 1A)
├── routes/products.js (Wave 1B)
├── routes/orders.js   (Wave 1C)
├── middleware/auth.js (Wave 1D)
└── server.js (Wave 2 — imports all routes)
```

### Pattern: Documentation Site

```
config.js (Wave 0 — shared metadata)
├── pages/index.md     (Wave 1A)
├── pages/guide.md     (Wave 1B)
├── pages/api.md       (Wave 1C)
├── components/Nav.js  (Wave 1D)
└── _config.ts (Wave 2 — imports all)
```

## Anti-Patterns to Avoid

### Anti-pattern: Splitting a monolithic file artificially

**Bad:** Splitting a 200-line `index.html` into 6 files where each file is 30 lines and they're all tightly coupled.

**Good:** Only split when modules have genuinely independent concerns and can be developed without knowledge of each other's internals.

### Anti-pattern: Dispatching Wave 2 without waiting for Wave 1

**Bad:** `delegate_task` with integrator + 5 modules all at once, no "wait" instruction.

**Good:** Either (a) wait for Wave 1 to complete, or (b) explicitly instruct the integrator to verify file existence before proceeding.

### Anti-pattern: Vague subagent context

**Bad:** `context: "Create a Three.js module for lighting"`

**Good:** `context: "Import COLORS and LIGHT_OPTS from './config.js'. Create 5 lights: AmbientLight, HemisphereLight, DirectionalLight (key, shadow-casting), DirectionalLight (fill), SpotLight (rim). Each light's parameters come from config. Return { keyLight, fillLight, rimLight, ambient, hemi }. Add all lights to scene. Shadow camera bounds -80 to 80."`
