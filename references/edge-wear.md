# Edge wear (dirty edges, shading) and edge chips (geometry)

No built-in "edge wear" node in 5.2; it is a recipe. Code `tools/blender/wear.py`, `wood_wear.py`.

## Mask: distance to the arris
Tested (35 mm band): Pointiness = mesh density, blurry; AO Inside = grainy, expensive; Bevel vs
shading normal = thin, expensive. **Use GN Edge Angle → Proximity → `edge_dist`** (exact metres,
clean, cheap, EEVEE-safe).

## Concrete recipe
1. `dice(obj, 0.05)` — Rhino meshes are coarse.
2. GN `edge_wear_group()`: Edge Angle (signed, convex positive) > 30° → Mesh to Curve → Curve to
   Mesh → Proximity → store `edge_dist`, `rest_pos`; faces within Band 8 cm → Subdivide ×3 (~6 mm);
   chip where `edge_dist` < reach (50 mm × bite/segment noise; Chipped Share 0.30), depth 18 mm ×
   profile × fracture noise; Set Position −normal; store `chip`; join; merge 1e-5.
   ≈ 2 M faces on the canopy, ~21 s at 1500×1000.
3. `weathered_concrete()`: dirt = smoothstep(edge_dist, 0–80 mm) × grime noise × (1 − chip) →
   grime BSDF (albedo ≈ 0.10, rough 0.93); chips → fresh-break BSDF (×1.16, rough 0.95, bump 3 mm).
4. Per object: `add_edge_wear(obj, group, Chip_Depth=…)` → `set_input()`.
Proof: dirt OFF 4.41 % changed vs 0.04 % floor; chips OFF 0.85 %.

## Whole rooms (one material, chips only where they show)
- Apply the GN modifier only to objects with convex arrises in view (beams, columns, piers,
  wall ends); big flat floors/slabs/enclosures stay coarse. Dice large walls coarser (~0.1 m) —
  the band subdivision still gives ~12 mm chip resolution. A beam-and-slab room came to ≈ 3 M
  evaluated faces, fine on 8 GB.
- **Gate the edge field in the shader.** On an object without the modifier the Attribute node
  returns 0 for `edge_dist` = "on an arris" → the whole surface gets edge grime. Add
  `edge_dist += 10 m × (length(rest_pos) < 1e-4)` before the band remap.
- Size chips for the viewing distance: reach/depth that read well on a close-up canopy look
  chewed on a beam 3–4 m from the camera; roughly halve them for room-scale shots and lower
  the Chipped Share.

## Wood (`wood_wear.py`, study 261006_wood_wear)
Real 2.5 mm bevel (`round_arrises`); `grain_uv`; GN dents (6 mm reach, 2.5 mm deep) + surface
breaks on up-facing faces (noise stretched along grain, 1.5 mm deep, Break Share 0.42 ≈ 1 % of
the top — steep response). Shader: worn edge = varnish off + grime; exposed wood = texture ×1.7,
30 % toward raw tint. Proof: breaks 13×, dents 19×, worn edges 27× the noise floor.

## Concave corners
Corner grime (beam/slab, wall/floor) is shading: AO node (outside, not Inside, ~0.3 m,
8 samples) remapped 0.85→0.35 into 0..1, × fine noise, into the grunge darkening
(materials.md › Monolithic concrete). No control render yet.

## Open
Per-object seeds (offset `rest_pos`). Adaptive displacement for chips ran out of memory on 8 GB.
