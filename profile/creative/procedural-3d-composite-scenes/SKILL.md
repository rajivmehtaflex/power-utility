---
name: procedural-3d-composite-scenes
description: Design, debug, verify, and parallelize Three.js scenes that combine organic characters with mechanical vehicles or props.
license: MIT
metadata:
  author: Hermes Agent
  hermes_related_skills: interactive-3d-web, subagent-orchestration
  hermes_tags: threejs, geometry, procedural-modeling, composite-scenes, coordinate-systems, visual-qa, subagents
  platforms: macos, linux, windows
  version: 1.0.0
---

# Procedural 3D Composite Scenes

Use this skill for scenes such as animals riding bicycles, mascots operating machines, people seated in vehicles, or any procedural model where an organic character must physically connect to a mechanical object.

## 1. Perform coordinate gap analysis before editing

Do not begin by changing mesh positions based on visual intuition alone. Establish one world-space coordinate contract:

- ground plane height
- wheel hubs and wheel-contact points
- seat top
- pedal endpoints
- handlebar grips
- character hips/feet
- character shoulders/hands

Then trace the character transform in order:

```text
local limb coordinate → scale → rotation → translation → world coordinate
```

Compare the resulting world anchor with the vehicle target. A common defect is moving the character to seat height while leaving its local feet near the character origin; the feet then float near the seat instead of reaching the pedals.

Use an explicit table:

| Connection | Character world anchor | Mechanical target | Delta |
|---|---|---|---|
| foot → pedal | `(x, y, z)` | `(x, y, z)` | `Δx, Δy, Δz` |
| hand → grip | `(x, y, z)` | `(x, y, z)` | `Δx, Δy, Δz` |

Do this analysis for every visible physical connection before implementation.

## 2. Keep modules independent and connect at the composite boundary

Use separate factories with stable APIs:

```javascript
createCharacter(envMap, THREE) → THREE.Group
createVehicle(envMap, THREE) → THREE.Group
createComposite(envMap, THREE) → THREE.Group
```

The character and vehicle factories should not import each other. Add bridging legs, arms, rods, hands, joints, and other connector geometry in `createComposite`, because it has both object graphs and the shared world coordinate system.

Do not duplicate numeric target coordinates in separate modules. Put shared values such as `CRANK_SIDE`, wheelbase, handlebar height, and pedal radius in `config.js`.

## 3. Use quaternion alignment for arbitrary beams

`CylinderGeometry` defaults along local Y. Avoid guessing Euler rotations for limbs, frame tubes, crank arms, or rods. Use a midpoint plus quaternion alignment:

```javascript
function addBeam(THREE, parent, material, from, to, radius) {
  const direction = new THREE.Vector3().subVectors(to, from);
  const beam = new THREE.Mesh(
    new THREE.CylinderGeometry(radius, radius, direction.length(), 10),
    material
  );
  beam.position.copy(from).add(to).multiplyScalar(0.5);
  beam.quaternion.setFromUnitVectors(
    new THREE.Vector3(0, 1, 0),
    direction.normalize()
  );
  beam.castShadow = true;
  beam.receiveShadow = true;
  parent.add(beam);
  return beam;
}
```

For readable joints, add a small endpoint sphere at hands, hubs, or limb joints.

## 4. Mechanical orientation checklist

- `CylinderGeometry` default axis: Y.
- Horizontal axle along X: rotate Z by `Math.PI / 2`.
- Horizontal member along Z: rotate X by `Math.PI / 2`.
- Arbitrary member: use `setFromUnitVectors`.
- A front wheel with X axle has its rotation plane in Y–Z.
- A pedal mechanism should visibly originate at the hub, use a shared lateral offset, and place two pedal endpoints at explicit opposite crank positions.
- Add a hub cap or axle connector when the crank-to-wheel relationship is visually ambiguous.
- Every visible mesh should set `castShadow = true` and `receiveShadow = true`.

## 5. Subagent wave design

For complex composite scenes, use this dependency graph:

```text
Wave 0: shared config / anchor contract
                 │
      ┌──────────┼──────────┐
      ▼          ▼          ▼
Wave 1: vehicle  character  static harness
         module   composite  module
      └──────────┼──────────┘
                 ▼
Wave 2: integration/API gate
                 ▼
Wave 3: browser visual QA
                 ▼
Wave 4: deployment + live smoke test
```

Wave 1 tasks must have disjoint file ownership. The parent must not start the next wave until every delegated result is complete and the actual files have been checked. A delayed delegation result is not proof that the current filesystem state is correct; inspect the files and rerun the gate.

Do not parallelize two tasks that edit the same file. Do not pre-dispatch an integrator unless its context explicitly tells it to wait for all required files and verify exports.

## 6. Verification gates

`node --check` validates syntax only. Add a small static harness that checks:

- shared anchor constants exist;
- public factory exports remain unchanged;
- beam alignment uses `setFromUnitVectors`;
- hub, crank, pedal, shoulder, and grip anchors are present;
- stale imports for replaced objects are absent.

Then perform mandatory browser verification for any scene with more than five meshes:

1. Start `python3 -m http.server 8080`.
2. Open `http://localhost:8080`.
3. Check browser console for import/runtime errors.
4. Use a screenshot/vision inspection with specific spatial questions:
   - Are all wheels attached and touching the ground?
   - Does the crank visibly connect to the hub?
   - Are feet connected to pedals?
   - Are hands connected to grips?
   - Is the character seated rather than floating or clipping?
   - Are any parts detached or floating?
5. Test orbit, zoom, auto-rotate, reset, and resize.
6. Fix the smallest offending module and repeat the visual gate.

Never report a procedural geometry change as complete based on syntax checks alone.

## 7. Common failure modes

- **Floating limbs:** character translation was applied without transforming local foot/hand coordinates.
- **Disconnected crank:** crank was modeled along the axle instead of radially in the wheel rotation plane.
- **Wrong cylinder axis:** Euler rotation chosen without checking the default Y axis.
- **False confidence from lint:** all modules parse, but geometry is spatially wrong.
- **Subagent drift:** a worker changes a file outside its ownership or changes a public export. Reject the result and restore the contract before integration.
- **Stale asynchronous result:** a worker reports success after the parent already applied a fallback. Verify the current filesystem and do not blindly reapply delayed output.
