# Procedural Character & Vehicle Geometry from Three.js Primitives

Building recognizable multi-part objects (animals, vehicles, furniture) from Three.js primitives (Sphere, Box, Cylinder, Cone, Torus) without loading external GLTF/GLB models. All examples use 1 unit = 1 cm real-world scale.

## Core Pattern: makeMesh Helper + Factory Function

Every geometry module follows this structure:

```javascript
import { DIMS, COLORS } from './config.js';

export function createModel(envMap, THREE) {
  const group = new THREE.Group();

  // Reusable materials (create once, reference many times)
  const bodyMat = new THREE.MeshStandardMaterial({
    color: COLORS.BODY, roughness: 0.7, metalness: 0.0,
    envMap, envMapIntensity: 0.3,
  });

  // Helper: every mesh gets shadows automatically
  function makeMesh(geo, mat, x = 0, y = 0, z = 0) {
    const m = new THREE.Mesh(geo, mat);
    m.position.set(x, y, z);
    m.castShadow = true;
    m.receiveShadow = true;
    return m;
  }

  // ... build parts using makeMesh ...
  return group;
}
```

## Organic Shapes (Animals / Characters)

### Body — Scaled Sphere (Ellipsoid)

The single most useful primitive for organic shapes. A sphere scaled to different dimensions becomes a body, head, or pouch:

```javascript
const bodyGeo = new THREE.SphereGeometry(1, 32, 24); // unit sphere
bodyGeo.scale(D.BODY_LEN / 2, D.BODY_HGT / 2, D.BODY_WID / 2); // stretch to ellipsoid
const body = makeMesh(bodyGeo, bodyMat, 0, BODY_CENTER_Y, 0);
```

**Pitfall:** Scale the *geometry*, not the mesh. `mesh.scale.set()` works but doesn't affect child meshes in a Group. `geometry.scale()` bakes the deformation into the vertex data.

### Neck — Segmented Cylinders (S-Curve)

Necks, tails, and spines use a series of slightly-rotated cylinders:

```javascript
const segCount = 3;
let yPos = bodyTopY, zPos = bodyFrontZ;
for (let i = 0; i < segCount; i++) {
  const segLen = NECK_LEN / segCount;
  const seg = makeMesh(
    new THREE.CylinderGeometry(R * (1 - i * 0.1), R * (1 - (i+1) * 0.1), segLen, 12),
    bodyMat, 0, yPos + segLen / 2, zPos
  );
  seg.rotation.x = -0.3 + i * 0.1; // increasing forward tilt
  group.add(seg);
  yPos += segLen * 0.9;
  zPos += segLen * 0.2;
}
```

### Beak — Cone Rotated to Point Forward

`ConeGeometry` defaults to pointing +Y (up). Rotate to point +Z (forward):

```javascript
const beakGeo = new THREE.ConeGeometry(BEAK_WID, BEAK_LEN, 8);
beakGeo.rotateX(Math.PI / 2); // +Y → +Z (point forward)
const beak = makeMesh(beakGeo, beakMat, 0, headY, headFrontZ + BEAK_LEN / 2);
```

### Pouch — Scaled Sphere Underneath

```javascript
const pouchGeo = new THREE.SphereGeometry(1, 16, 12);
pouchGeo.scale(POUCH_LEN / 2, POUCH_DEPTH / 2, BEAK_WID);
const pouch = makeMesh(pouchGeo, pouchMat, 0, headY - POUCH_DEPTH / 2, pouchFrontZ);
```

### Wings — Folded Boxes at Body Sides

```javascript
const wingGeo = new THREE.BoxGeometry(WING_LEN, WING_HGT, WING_WID);
const leftWing = makeMesh(wingGeo, bodyMat, 0, bodyY, -(BODY_WID / 2 + WING_WID / 2));
leftWing.rotation.z = -0.15; // slight outward angle
```

### Feet — Flat Boxes Pointing Forward

```javascript
const footGeo = new THREE.BoxGeometry(FOOT_LEN, FOOT_HGT, FOOT_WID);
group.add(makeMesh(footGeo, footMat, BODY_WID / 4, FOOT_HGT / 2, BODY_FRONT_Z));
```

## Mechanical Shapes (Vehicles / Wheels)

### Wheel — Torus + Hub + Spokes

The most error-prone assembly. Each part has a specific orientation:

```javascript
function makeWheel(x, z) {
  const g = new THREE.Group();

  // Tire: torus rotated to face axle direction
  const tire = new THREE.Mesh(
    new THREE.TorusGeometry(WHEEL_R, TUBE_R, 16, 32), wheelMat
  );
  tire.rotation.y = Math.PI / 2; // CRITICAL: default faces +Z, rotate to face +X (axle)
  g.add(tire);

  // Hub: cylinder along axle (X direction)
  const hub = new THREE.Mesh(
    new THREE.CylinderGeometry(HUB_R, HUB_R, HUB_LEN, 16), hubMat
  );
  hub.rotation.z = Math.PI / 2; // cylinder default Y → X
  g.add(hub);

  // Spokes: thin cylinders rotating in the wheel plane (YZ after tire rotation)
  const spokeGeo = new THREE.CylinderGeometry(0.2, 0.2, WHEEL_R * 2 - 2, 6);
  for (let i = 0; i < 4; i++) {
    const spoke = new THREE.Mesh(spokeGeo, hubMat);
    spoke.rotation.x = (i * Math.PI) / 4; // fan within YZ plane, NOT XY
    g.add(spoke);
  }

  g.position.set(x, WHEEL_R, z); // bottom touches y=0
  return g;
}
```

**Critical pitfall:** TorusGeometry lies in the XY plane by default (hole faces +Z). For a wheel whose axle is along X and rolls on Z, you need `rotation.y = Math.PI / 2`. Forgetting this makes wheels face sideways (visible as thin lines from the camera).

### Frame Tube — Cylinder Between Two Points

For diagonal/angled frame members, use quaternion alignment instead of guessing Euler angles:

```javascript
const start = new THREE.Vector3(0, FRAME_H, 0);
const end = new THREE.Vector3(0, HANDLEBAR_H, WHEELBASE);
const vec = new THREE.Vector3().subVectors(end, start);
const len = vec.length();
const mid = new THREE.Vector3().addVectors(start, end).multiplyScalar(0.5);

const tube = makeMesh(
  new THREE.CylinderGeometry(TUBE_R, TUBE_R, len, 12),
  frameMat, mid.x, mid.y, mid.z
);
tube.quaternion.setFromUnitVectors(
  new THREE.Vector3(0, 1, 0), vec.clone().normalize()
);
group.add(tube);
```

### Handlebars — Horizontal Cylinder

```javascript
const hbGeo = new THREE.CylinderGeometry(HB_R, HB_R, HB_WIDTH, 12);
const handlebar = makeMesh(hbGeo, handleMat, 0, HB_HEIGHT, FRONT_Z);
handlebar.rotation.z = Math.PI / 2; // Y-axis → X-axis (horizontal)
```

## Composite Objects (Character Riding Vehicle)

When combining two independent modules into one scene:

```javascript
import { createCharacter } from './character.js';
import { createVehicle } from './vehicle.js';

export function createComposite(envMap, THREE) {
  const sceneObj = new THREE.Group();

  const vehicle = createVehicle(envMap, THREE);
  sceneObj.add(vehicle);

  const character = createCharacter(envMap, THREE);
  character.scale.setScalar(0.55); // shrink to fit
  character.position.set(0, SEAT_HEIGHT - 1, WHEELBASE * 0.15); // sit on seat
  character.rotation.x = -0.15; // slight forward lean
  sceneObj.add(character);

  return sceneObj;
}
```

**Key adjustments when compositing:**
- Scale the character to fit the vehicle (start with 0.5× and adjust)
- Position Y so the character's bottom aligns with the seat top
- Add a slight forward lean (`rotation.x = -0.1 to -0.2`) for riding posture
- Center of mass should sit over the widest part of the vehicle base
