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

## Wood (`wood_wear.py`, study 261006_wood_wear)
Real 2.5 mm bevel (`round_arrises`); `grain_uv`; GN dents (6 mm reach, 2.5 mm deep) + surface
breaks on up-facing faces (noise stretched along grain, 1.5 mm deep, Break Share 0.42 ≈ 1 % of
the top — steep response). Shader: worn edge = varnish off + grime; exposed wood = texture ×1.7,
30 % toward raw tint. Proof: breaks 13×, dents 19×, worn edges 27× the noise floor.

## Open
Concave-corner dirt (AO not Inside); per-object seeds (offset `rest_pos`). Adaptive displacement
for chips ran out of memory on 8 GB.
