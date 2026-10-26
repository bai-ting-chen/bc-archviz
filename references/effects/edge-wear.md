# Edge wear (dirty edges, shading) and edge chips (geometry)

## 1. Overview
No built-in "edge wear" node in Blender 5.2; it is a recipe. It has two parts: a dirty arris (shading,
a mask from the distance to the edge) and edge chips (geometry, a chipped arris). Corner dust, runoff and
cracks are in this file too.

**Every size here is a dial, not a value** — a chipped arris is millimetres on a close-up and can be a
hundred across a courtyard. What matters is the pixels it occupies, so set reach, depth and band from the
shot and judge the first render (RULES MAT_03).

**Use when:** a convex arris needs chips or a dirty edge, a surface needs run-off or cracks, or a concave
joint needs dust (§4.8). Per-unit variation and grunge strength are in the variation reference (variation.md).

## 2. Layers and node-editor diagram
Specific layers are described in §4. Generic layers are written once, in their own reference.

```
                          EDGE WEAR AND CHIPS
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ SPECIFIC (§4)                              GENERIC (own reference)        │
 │ 1 Arris mask         → edge_dist           Per-unit variation, grunge     │
 │ 2 Chip geometry      → chips (mesh)                → variation.md          │
 │ 3 Fresh break, dirt  → colour, roughness   Faint arris on huge meshes     │
 │ 4 Chips as relief    → displacement                → concrete.md           │
 │ 5 Wood arrises       → bevel, dents        Cracks in glazed tiles         │
 │ 6 Concave dust       → shading at joints           → materials/tile        │
 │ 7 Run-off            → vertical faces                                     │
 │ 8 Cracks             → dark crack lines                                   │
 └───────────────────────────────────────────────────────────────────────────┘
   edge field and chips (1, 2)                       what it drives
   arris mask (1) ─► edge_dist, rest_pos ─► band subdivision + chips (2) ─► chip mesh along −normal
   chip mask (2) ─► fresh-break colour and dirt (3) ─► shading
   chips as displacement (4) replaces (2) where the mesh is already dense
   run-off (7), concave dust (6), cracks (8) ─► shading masks on the material; no added geometry
   wood (5) ─► its own real bevel and dents on its own arrises
```

- **Geometry, then shading:** the chips (2) are geometry; the other layers are shading that reads the edge
  field (RULES MAT_07 layers).
- **Run-off first:** the leak field (7) runs on the clean shell, before any chip (§4.9).
- **Per object:** each repeated object gets its own chips through its seed (§4.4).

## 3. Code
- `scripts/blender/effects/edge_wear.py`: the facade (`effects.edge_wear`) that re-exports the modules below.
- `scripts/blender/effects/edge_chips.py`: `dice`, `edge_wear_group`, `add_edge_wear`, `set_input` (§4.2, §4.4).
- `scripts/blender/effects/edge_shading.py`: `weathered_concrete` (§4.3).
- `scripts/blender/effects/leak_field.py`: `add_leak_field` (§4.9).
- `scripts/blender/effects/runoff.py`: `add_runoff` (§4.9).
- `scripts/blender/effects/cracks.py`: `add_cracks(mat, openings)` (§4.11).
- Wood: `scripts/blender/materials/wood/wood_wear.py` (§4.7); `round_arrises` in
  `scripts/blender/materials/wood/wood_arrises.py`; `directional_uv` in `scripts/blender/core/uv.py`.
- Run-off control: `scripts/controls/effects/weathering_lab.py` (flat test wall, §4.10).

## 4. Instructions and parameters, per layer
### 4.1 Arris mask (distance to the arris)
- Compared on one test: Pointiness tracks mesh density and comes out blurry; AO Inside is grainy and
  expensive; Bevel-vs-shading-normal is thin and expensive.
- **Use GN Edge Angle → Proximity → `edge_dist`** — exact metres, clean, cheap and EEVEE-safe.
- Exception: a *faint* dirty arris on huge meshes that would need dicing — the shader Bevel-normal mask
  ([concrete.md](../materials/concrete/concrete.md)).

| Method | Result on the test |
|---|---|
| Pointiness | blurry; tracks mesh density |
| AO Inside | grainy; expensive |
| Bevel vs shading normal | thin; expensive |
| GN Edge Angle → Proximity → `edge_dist` | exact metres, clean, cheap, EEVEE-safe (chosen) |
| Shader Bevel-normal mask | faint dirty arris on huge meshes that would need dicing |

### 4.2 Chip geometry
- `dice(obj, …)` first — Rhino meshes are too coarse to carry an edge band.
- GN `edge_wear_group()`: Edge Angle (signed, convex positive) over a threshold → Mesh to Curve → Curve to
  Mesh → Proximity → store `edge_dist` and `rest_pos`; faces within the band → Subdivide so the band resolves
  the chip size; chip where `edge_dist` < reach, modulated by a bite/segment noise and a chipped-share
  fraction; depth × profile × fracture noise; Set Position along −normal; store `chip`; join; merge by distance.
- **Size in this order**, each following from the one before rather than guessing all four.

| Order | Size from |
|---|---|
| 1 Chip reach | the shot |
| 2 Band | wide enough to contain the reach |
| 3 Subdivision | fine enough that a chip spans several faces |
| 4 Dirt band (§4.3) | wider than the reach |

### 4.3 Fresh-break colour and weathered dirt
- **Fresh-break colour comes from the clean base**, before grime, ink or other darkening layers, then lighter
  and rougher, blended by a soft mask on the chip depth. Taken from the finished colour, a chip inherits the
  grime and reads as a dark spot.
- `weathered_concrete()`: dirt = smoothstep over the dirt band × grime noise × (1 − chip) → a grimier,
  rougher BSDF; chips → a fresh-break BSDF, slightly lighter and rougher with its own bump. The dirt band is
  wider than the chip reach — grime spreads past where material is gone.

| Parameter | Value |
|---|---|
| Fresh-break lightness | ~+20 % over the clean base |
| Fresh-break mask depth | 0 → ~0.5 mm |
| Dirt band | wider than the chip reach |

### 4.4 Per-object chips on repeated objects
- Per object: `add_edge_wear(obj, group, …)` → `set_input()`.
- Repeated objects (a row of identical beams or boards) get their own chips with `Seed=(x, y, z)` — it offsets
  the noise lookups; Seed 0 is the group's default pattern.

| Parameter | Value |
|---|---|
| Seed | `(x, y, z)` per repeated object; 0 = group default |

### 4.5 Whole rooms (one material, chips only where they show)
- Apply the GN modifier only to objects with convex arrises *in view* — beams, columns, piers, wall ends. Big
  flat floors, slabs and enclosures stay coarse; they have no arris the camera can see and they dominate the
  face count.
- Dice large walls coarser than close-up objects: the band subdivision still resolves chips because it
  subdivides only inside the band.
- **Gate the edge field in the shader.** On an object *without* the modifier the Attribute node returns 0
  for `edge_dist`, which reads as "on an arris", so the whole surface gets edge grime. Add a large offset
  where `rest_pos` is unset (`length(rest_pos) < epsilon`) before the band remap. This is the single most
  common way a floor goes uniformly dirty.
- Halve chip size and lower the chipped share for room-scale shots relative to a close-up: sizes that read
  well on a hero object look chewed on a beam several metres away.

| Setting | Value |
|---|---|
| Modifier scope | objects with convex arrises in view |
| Wall dice | coarser than close-up objects |
| Floor gate | `length(rest_pos) < epsilon` → large offset before the band remap |
| Chip size and chipped share | lower than close-up (about half the size) |

### 4.6 Chips as displacement (meshes already subdivided wall-wide)
- When another modifier has already subdivided the whole wall (a proximity or wet field at a high level), band
  subdivision on top multiplies an already dense mesh. Long thin faces (planks, boards) cannot resolve chips
  along their length cheaply either.
- Then build the same chip field (`_chip_field`: segments with a chipped share, bite noise on the reach,
  profile, fracture noise on the depth) in the material's displacement, through the existing adaptive dicing,
  along −normal. It adds no mesh; resolution follows the camera.
- Noise coordinates: a stored rest position, not the displaced position.
- Edge distance: an attribute adapter (distance to the unit's edges), gated where it is missing.
- Only outside arrises: exclude wall feet, inside corners and the low side of steps.
- **Open:** adaptive displacement for chips is a memory risk on a small-VRAM GPU — the band-subdivision
  approach (§4.2) exists because of that.

| Item | Setting |
|---|---|
| Field | segments, chipped share, bite noise, profile, fracture noise |
| Noise coordinates | stored rest position |
| Edge distance | attribute adapter, gated where missing |
| Excluded | wall feet, inside corners, low side of steps |

### 4.7 Wood (`wood_wear.py`)
- A real bevel on the arris (`round_arrises`) rather than a shaded one; `archviz.directional_uv`; GN dents on the
  edges plus surface breaks on up-facing faces, the break noise stretched *along* the grain so it reads as split
  timber rather than dents. Shader: worn edge = varnish off + grime; exposed wood = the texture lifted and
  pulled toward a raw tint.
- **The break share is a steep response** — a small fraction of the top surface is all you want, and a little
  more reads as damage rather than effects.edge_wear. Bisect it against a render.

| Item | Setting |
|---|---|
| Arris | real bevel (`round_arrises`) |
| Break share | small fraction of up-facing top surface; bisect against a render |
| Break noise | stretched along the grain |

### 4.8 Concave corners (RULES MAT_06)
Corner dust (wall/floor, wall/ceiling, plinths, beam/slab) is shading, not geometry. Target: darkest in the
joint, fading outward over ~15–25 cm, broken up, stronger where air is still — floor joints and the tops of
plinths — and fainter, greyer at the ceiling.
- **Cycles** (the numbers are one room's starting point — size them from the shot, RULES MAT_03): AO node,
  **Inside off, Only Local off** (floor and wall are usually separate Rhino objects; Only Local would miss their
  joint), Distance ≈ 0.2 m → Map Range AO 0.55..0.97 → 1..0, ^1.2, × a 5/m noise remapped 0.45–1 (patchy
  extent) × a 90/m noise 0.7–1 (speckle) × a height falloff (1.0 at 0.6 m → 0.45 at 2.6 m); albedo ×
  mix(1, (0.62, 0.58, 0.52), mask). AO is expensive: bake it for repeated renders.
- **LuxCore** (no AO texture): the same shader **baked** per object into its own UV layout, then multiplied in a
  native tree — `renderer.luxcore.luxcore.bake_dust(objs, cache_dir)` + `lux_textured(..., dust_png=...)`.
  4096 px per object keeps a 20 cm band smooth at room scale.
- A reach of 0.12 m reads as a pencil line from a few metres; judge the width on the full frame, not a close-up.

| Parameter | Value (Cycles) |
|---|---|
| AO node | Inside off, Only Local off |
| AO distance | ≈ 0.2 m |
| Map Range AO | 0.55..0.97 → 1..0, ^1.2 |
| Patchy noise | 5/m, remapped 0.45–1 |
| Speckle noise | 90/m, 0.7–1 |
| Height falloff | 1.0 at 0.6 m → 0.45 at 2.6 m |
| Albedo | × mix(1, (0.62, 0.58, 0.52), mask) |
| LuxCore bake texture | 4096 px per object |

### 4.9 Runoff streaks (drip-edge raycast)
- Runoff starts where water leaves a surface: eaves, gable rakes, sill corners. The drip edge above every wall
  point is found by a GN raycast straight up from just inside the wall (`effects.edge_wear.add_leak_field`) →
  `leak_d` (m below the edge).
- Streaks: noise stretched across ×14 / down ×0.6, each streak its own length (0.8–3 m), a drip band under the
  edge, patchy along it (RULES MAT_05), vertical faces only (`effects.edge_wear.add_runoff`). On a sunlit wall
  streaks need full strength to read at all.
- **Modifier order:** the leak field goes FIRST, on the clean shell. Run after the chips, rays from under an arris
  slip through the chip-band seam or hit the chipped underside; the wrong value of one vertex then spreads over a
  whole coarse dice triangle → light triangles hanging from the arris. Any raycast/proximity field: before
  modifiers that crack or move the mesh.

| Parameter | Value |
|---|---|
| Streak stretch | ×14 across, ×0.6 down |
| Streak length | 0.8–3 m each |
| Drip band | under the edge, patchy along it |
| Faces | vertical only |

### 4.10 Procedural run-off (no drip-edge raycast)
- For walls whose top is the drip edge, build the layer from the wall's own top and foot (stored per-vertex) and
  the along-wall coordinate (x + y on axis-aligned walls, plus a per-wall offset). Weathering is gravity-shaped:
  isotropic cloud noise alone reads as smoke or blur. Factors, multiplied (RULES MAT_07):
- Design it on a flat test wall first (`scripts/controls/effects/weathering_lab.py`), then install the exact graph.
  Check that it adds no step at joints (change across a joint ≈ change within a unit).

| Factor | Value |
|---|---|
| Streaks from the top | two widths: noise ~7/m and ~3/m across, ~0.45/m down |
| Clustering | low-frequency noise along the wall (~0.45/m, ~70 % coverage) |
| Streak edges | meandering ~5 cm |
| Streak length | ~1.2–4 m each, fading downward |
| Dirt band | ~0.35 m under the top |
| Damp base | uneven upper edge, from the *visible* foot (ground or waterline) |
| Large patches | ~2–3 m, low weight |
| Medium blotches | ~0.4 m, low weight |
| Joint leaks | narrow drips (~18/m across) on ~55 % of each joint; per-joint seed so no two joints match; each drip fades over 0.1–0.65 m and ends at the next joint below |

### 4.11 Cracks (`add_cracks(mat, openings)`)
- Shrinkage cracks start at re-entrant corners — 45° (±15) out of opening corners, 0.4–1 m, tapering, two-scale
  wobble; plus patchy map-cracking from noise-distorted Voronoi cell edges, only some edges, only in patches.
- A hairline is invisible at room-to-street scale; what reads is a dirt-darkened crack: core ~5 mm, halo ~20 mm
  at ~5 mm/px, a shallow groove. One crack at every corner looks deliberate — keep a few, not a symmetric set
  (an opposite pair reads as one line).

| Parameter | Value |
|---|---|
| Angle from opening corners | 45° ±15 |
| Length | 0.4–1 m, tapering |
| Core | ~5 mm |
| Halo | ~20 mm at ~5 mm/px |
| Groove | shallow |
| Count | a few, not symmetric |

### 4.12 Proving it
Each layer gets its own control (RULES VAL_02): one that moves the frame only *by* the noise floor is not
installed, however good the node tree looks. Record the ratios in the study.

| Check | Rule |
|---|---|
| Control per layer | one control per layer; a layer under the noise floor is not installed (RULES VAL_02) |
| Ratios | recorded in the study |

### Generic layers
| Layer | Reference | Note for this material |
|---|---|---|
| Per-unit variation and grunge strength | variation.md | weathering shape is gravity-driven; dust and cracks are here |
| Faint dirty arris on huge meshes | [concrete.md](../materials/concrete/concrete.md) | shader Bevel-normal mask instead of dicing (§4.1) |
| Cracks in glazed tiles | [tiles.md](../materials/tile/tiles.md) | a per-tile Voronoi network, not hand-placed lines |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Chips chewed on a far beam, too big | close-up chip sizes used at room scale | halve chip size, lower the chipped share (§4.5) |
| Whole floor uniformly dirty | the edge field reads 0 on objects without the modifier | gate on `rest_pos` before the band remap (§4.5) |
| Light triangles hanging from an arris | leak field run after the chips; one vertex's value spreads over a coarse triangle | leak field first, on the clean shell (§4.9) |
| Dark spot where a chip is | fresh-break colour taken from the grimed finished colour | fresh break from the clean base (§4.3) |
| Slow render on an already dense wall | band subdivision on a wall another modifier already subdivided | chips as displacement (§4.6) |
| Identical chips on repeated beams | same noise lookups | seed per object (§4.4) |
| Wood reads as damaged | break share too high | bisect the break share against a render (§4.7) |
| Corner dust reads as a pencil line from a few metres | reach of 0.12 m judged up close | judge the width on the full frame (§4.8) |
| Sunlit wall shows no streaks | streaks at less than full strength | full strength on a sunlit wall (§4.9) |
| Weathering reads as smoke or blur | isotropic cloud noise | gravity-shaped run-off (§4.10) |
| Two cracks read as one line | an opposite pair of cracks | keep a few, not a symmetric set (§4.11) |
| VRAM runs out on a small GPU | adaptive displacement for chips | band subdivision instead (§4.2, §4.6) |

Generic problems that often show up with this material, in troubleshooting.md.
