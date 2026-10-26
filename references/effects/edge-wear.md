# Edge wear (dirty edges, shading) and edge chips (geometry)

No built-in "edge wear" node in 5.2; it is a recipe. Code `scripts/blender/effects/edge_wear.py`, `scripts/blender/materials/wood/wood_wear.py`.

**Every size here is a dial, not a value** — a chipped arris is millimetres on a close-up and
can be a hundred across a courtyard. What matters is the pixels it occupies, so set reach, depth
and band from the shot and judge the first render (RULES MAT_03).

## Mask: distance to the arris
Compared on one test: Pointiness tracks mesh density and comes out blurry; AO Inside is grainy
and expensive; Bevel-vs-shading-normal is thin and expensive. **Use GN Edge Angle → Proximity →
`edge_dist`** — exact metres, clean, cheap and EEVEE-safe. Exception: a *faint* dirty arris on
huge meshes that would need dicing - the shader Bevel-normal mask ([concrete.md](../materials/concrete/concrete.md)).

## Concrete recipe
1. `dice(obj, …)` — Rhino meshes are too coarse to carry an edge band.
2. GN `edge_wear_group()`: Edge Angle (signed, convex positive) over a threshold → Mesh to Curve
   → Curve to Mesh → Proximity → store `edge_dist` and `rest_pos`; faces within the band →
   Subdivide so the band resolves the chip size; chip where `edge_dist` < reach, modulated by a
   bite/segment noise and a chipped-share fraction; depth x profile x fracture noise;
   Set Position along −normal; store `chip`; join; merge by distance.
- **Fresh-break colour comes from the clean base**, before grime, ink or other darkening layers,
  then lighter (~+20 %) and rougher, blended by a soft mask on the chip depth (0 → ~0.5 mm). Taken
  from the finished colour, a chip inherits the grime and reads as a dark spot.
3. `weathered_concrete()`: dirt = smoothstep over the dirt band x grime noise x (1 − chip) → a
   grimier, rougher BSDF; chips → a fresh-break BSDF, slightly lighter and rougher with its own
   bump. The dirt band is wider than the chip reach — grime spreads past where material is gone.
4. Per object: `add_edge_wear(obj, group, …)` → `set_input()`. Repeated objects (a row of
   identical beams or boards) get their own chips with `Seed=(x, y, z)` — it offsets the noise
   lookups; Seed 0 is the group's default pattern.

**Size in this order**, each following from the one before rather than guessing all four: chip
reach from the shot → band wide enough to contain it → subdivision fine enough that a chip spans
several faces → dirt band wider than reach.

## Whole rooms (one material, chips only where they show)
- Apply the GN modifier only to objects with convex arrises *in view* — beams, columns, piers,
  wall ends. Big flat floors, slabs and enclosures stay coarse; they have no arris the camera can
  see and they dominate the face count.
- Dice large walls coarser than close-up objects: the band subdivision still resolves chips
  because it subdivides only inside the band.
- **Gate the edge field in the shader.** On an object *without* the modifier the Attribute node
  returns 0 for `edge_dist`, which reads as "on an arris", so the whole surface gets edge grime.
  Add a large offset where `rest_pos` is unset (`length(rest_pos) < epsilon`) before the band
  remap. This is the single most common way a floor goes uniformly dirty.
- Halve chip size and lower the chipped share for room-scale shots relative to a close-up: sizes
  that read well on a hero object look chewed on a beam several metres away.

## Chips as displacement (meshes already subdivided wall-wide)
When another modifier has already subdivided the whole wall (a proximity or wet field at a high
level), band subdivision on top multiplies an already dense mesh. Long thin faces (planks,
boards) cannot resolve chips along their length cheaply either. Then build the same chip field
(`_chip_field`: segments with a chipped share, bite noise on the reach, profile, fracture noise on
the depth) in the material's displacement, through the existing adaptive dicing, along −normal.
It adds no mesh; resolution follows the camera.
- Noise coordinates: a stored rest position, not the displaced position.
- Edge distance: an attribute adapter (distance to the unit's edges), gated where it is missing.
- Only outside arrises: exclude wall feet, inside corners and the low side of steps.

## Wood (`scripts/blender/materials/wood/wood_wear.py`)
A real bevel on the arris (`round_arrises`) rather than a shaded one; `archviz.directional_uv`; GN dents on the
edges plus surface breaks on up-facing faces, the break noise stretched *along* the grain so it
reads as split timber rather than dents. Shader: worn edge = varnish off + grime; exposed wood =
the texture lifted and pulled toward a raw tint.

**The break share is a steep response** — a small fraction of the top surface is all you want,
and a little more reads as damage rather than effects.edge_wear. Bisect it against a render.

## Concave corners (RULES MAT_06)
Corner dust (wall/floor, wall/ceiling, plinths, beam/slab) is shading, not geometry. Target: darkest in the joint, fading outward over ~15–25 cm, broken up, stronger where
air is still — floor joints and the tops of plinths — and fainter, greyer at the ceiling.
- **Cycles** (the numbers are one room's starting point — size them from the shot, RULES MAT_03):
  AO node, **Inside off, Only Local off** (floor and wall are usually separate Rhino
  objects; Only Local would miss their joint), Distance ≈ 0.2 m → Map Range AO 0.55..0.97 →
  1..0, ^1.2, × a 5/m noise remapped 0.45–1 (patchy extent) × a 90/m noise 0.7–1 (speckle) ×
  a height falloff (1.0 at 0.6 m → 0.45 at 2.6 m); albedo × mix(1, (0.62, 0.58, 0.52), mask). AO is
  expensive: bake it for repeated renders.
- **LuxCore** (no AO texture): the same shader **baked** per object into its own UV layout,
  then multiplied in a native tree — `renderer.luxcore.luxcore.bake_dust(objs, cache_dir)` +
  `lux_textured(..., dust_png=...)`. 4096 px per object keeps a 20 cm band smooth at room scale.
- A reach of 0.12 m reads as a pencil line from a few metres; judge the width on the full frame,
  not a close-up.

## Runoff streaks, cracks
- **Runoff** starts where water leaves a surface: eaves, gable rakes, sill corners. The drip
  edge above every wall point is found by a GN raycast straight up from just inside the wall
  (`effects.edge_wear.add_leak_field`) -> `leak_d` (m below the edge). Streaks: noise stretched across x14 /
  down x0.6, each streak its own length (0.8-3 m), a drip band under the edge, patchy along it
  (RULES MAT_05), vertical faces only (`effects.edge_wear.add_runoff`). On a sunlit wall streaks need full
  strength to read at all.
- **Procedural run-off (no drip-edge raycast):** for walls whose top is the drip edge, build the
  layer from the wall's own top and foot (stored per-vertex) and the along-wall coordinate (x + y
  on axis-aligned walls, plus a per-wall offset). Weathering is gravity-shaped: isotropic cloud
  noise alone reads as smoke or blur. Factors, multiplied (RULES MAT_07):
  - streaks from the top in two widths (noise ~7/m and ~3/m across, ~0.45/m down), clustered by a
    low-frequency noise along the wall (~0.45/m, ~70 % coverage), edges meandering ~5 cm, each
    streak its own length (~1.2–4 m) fading downward;
  - a dirt band ~0.35 m under the top;
  - a damp base with an uneven upper edge, from the *visible* foot (ground or waterline);
  - large soft patches (~2–3 m) and medium blotches (~0.4 m) at low weight;
  - **leaks under horizontal joints:** narrow drips (~18/m across), present on ~55 % of each
    joint, with a per-joint seed so no two joints match; each drip fades over 0.1–0.65 m and ends
    at the next joint below.
  Design it on a flat test wall first (`scripts/controls/effects/weathering_lab.py`), then install the
  exact graph. Check that it adds no step at joints (change across a joint ≈ change within a unit).
- **Modifier order:** the leak field goes FIRST, on the clean shell. Run after the chips, rays
  from under an arris slip through the chip-band seam or hit the chipped underside; the wrong
  value of one vertex then spreads over a whole coarse dice triangle -> light triangles hanging
  from the arris. Any raycast/proximity field: before modifiers that crack or move the mesh.
- **Cracks** (`effects.edge_wear.add_cracks(mat, openings)`): shrinkage cracks start at re-entrant corners -
  45 deg (+-15) out of opening corners, 0.4-1 m, tapering, two-scale wobble; plus patchy
  map-cracking from noise-distorted Voronoi cell edges, only some edges, only in patches. A
  hairline is invisible at room-to-street scale; what reads is a dirt-darkened crack: core
  ~5 mm, halo ~20 mm at ~5 mm/px, a shallow groove. One crack at every corner looks
  deliberate - keep a few, not a symmetric set (an opposite pair reads as one line).
- **Cracks in glazed tiles:** a per-tile Voronoi network, not hand-placed lines — [materials/tiles.md](../materials/tile/tiles.md)

## Proving it
Each layer gets its own control (RULES VAL_02): one that moves the frame only *by* the noise floor
is not installed, however good the node tree looks. Record the ratios in the study.

## Open
Adaptive displacement for chips is a memory risk on a
small-VRAM GPU — the band-subdivision approach exists because of that.
