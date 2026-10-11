# Edge wear (dirty edges, shading) and edge chips (geometry)

No built-in "edge wear" node in 5.2; it is a recipe. Code `scripts/blender/wear.py`, `wood_wear.py`.

**Every size here is a dial, not a value** — a chipped arris is millimetres on a close-up and
can be a hundred across a courtyard. What matters is the pixels it occupies, so set reach, depth
and band from the shot and judge the first render (RULES 8).

## Mask: distance to the arris
Compared on one test: Pointiness tracks mesh density and comes out blurry; AO Inside is grainy
and expensive; Bevel-vs-shading-normal is thin and expensive. **Use GN Edge Angle → Proximity →
`edge_dist`** — exact metres, clean, cheap and EEVEE-safe.

## Concrete recipe
1. `dice(obj, …)` — Rhino meshes are too coarse to carry an edge band.
2. GN `edge_wear_group()`: Edge Angle (signed, convex positive) over a threshold → Mesh to Curve
   → Curve to Mesh → Proximity → store `edge_dist` and `rest_pos`; faces within the band →
   Subdivide so the band resolves the chip size; chip where `edge_dist` < reach, modulated by a
   bite/segment noise and a chipped-share fraction; depth x profile x fracture noise;
   Set Position along −normal; store `chip`; join; merge by distance.
3. `weathered_concrete()`: dirt = smoothstep over the dirt band x grime noise x (1 − chip) → a
   grimier, rougher BSDF; chips → a fresh-break BSDF, slightly lighter and rougher with its own
   bump. The dirt band is wider than the chip reach — grime spreads past where material is gone.
4. Per object: `add_edge_wear(obj, group, …)` → `set_input()`.

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

## Wood (`wood_wear.py`)
A real bevel on the arris (`round_arrises`) rather than a shaded one; `archviz.directional_uv`; GN dents on the
edges plus surface breaks on up-facing faces, the break noise stretched *along* the grain so it
reads as split timber rather than dents. Shader: worn edge = varnish off + grime; exposed wood =
the texture lifted and pulled toward a raw tint.

**The break share is a steep response** — a small fraction of the top surface is all you want,
and a little more reads as damage rather than wear. Bisect it against a render.

## Concave corners (RULES 8d)
Corner dust (wall/floor, wall/ceiling, plinths, beam/slab) is shading, not geometry. Target (as
VRayDirt does it): darkest in the joint, fading outward over ~15–25 cm, broken up, stronger where
air is still — floor joints and the tops of plinths — and fainter, greyer at the ceiling.
- **Cycles** (the numbers are one room's starting point — size them from the shot, RULES 8):
  AO node, **Inside off, Only Local off** (floor and wall are usually separate Rhino
  objects; Only Local would miss their joint), Distance ≈ 0.2 m → Map Range AO 0.55..0.97 →
  1..0, ^1.2, × a 5/m noise remapped 0.45–1 (patchy extent) × a 90/m noise 0.7–1 (speckle) ×
  a height falloff (1.0 at 0.6 m → 0.45 at 2.6 m); albedo × mix(1, (0.62, 0.58, 0.52), mask). AO is
  expensive: bake it for repeated renders.
- **LuxCore** (no AO texture): the same shader **baked** per object into its own UV layout,
  then multiplied in a native tree — `lux_materials.bake_dust(objs, cache_dir)` +
  `lux_textured(..., dust_png=...)`. 4096 px per object keeps a 20 cm band smooth at room scale.
- A reach of 0.12 m reads as a pencil line from a few metres; judge the width on the full frame,
  not a close-up.

## Proving it
Each layer gets its own control (RULES 9). A layer that moves the frame a few times the noise
floor is doing visible work; one that moves it *by* the noise floor is not installed, however
good the node tree looks. Record the ratios in the study.

## Open
Per-object seeds (offset `rest_pos`). Adaptive displacement for chips is a memory risk on a
small-VRAM GPU — the band-subdivision approach exists because of that.
