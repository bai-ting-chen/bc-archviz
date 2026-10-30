# Texture Selection
Use when: choosing a texture source or method for a surface, then scaling it and laying its UVs.

## Choosing and scaling a texture
| Case | Method | Criteria and checks |
|---|---|---|
| A scan fits (Poly Haven or local map) | scanned map, hit the target albedo with a per-channel gain (steps 3-4) | measured mean near the target (a map whose mean sits far from it will not scale cleanly); no rows of tie holes, strong directional stains or visible repeat on a large jointless surface, however good its mean |
| Clean white finish (concrete, plaster, mortar) | steps 1–4 for the scan, then flat target plus a fraction of a scan's tonal variation: Mix(flat albedo, scaled scan, fac), fac set from the shot; desaturate, soften the normal map; leave out panel joints and tie holes unless the design has them | a good scan still reads dirty at its own contrast; white paint and plaster sit near 0.8 albedo, cement mortar lower |
| Aggregate, chip or grain pattern | size is a design choice: take it from the brief or the reference; bake to a seamless image (numpy, tileable via FFT noise + wrapped stamps) when the renderer has no procedural textures (LuxCore) | judge the size at the shot's scale |
| Formwork or panel texture with joints at its tile edges | tiled map with UVs offset by a fraction of a tile (see Tiled maps with joints below) | no joint line on the camera axis; no grid the reference doesn't have |
| Clear glass, water | `materials.shared.pbr.dielectric` | |

- **Fallback, missing map:** choose the substitute by texture as well as mean — compare high-pass
  sigma, not only colour; a "clean" crop of a marble scan reads blank at floor distance.
- **Report** which case and method were chosen, and why.
- **Which Poly Haven builder:** `materials.shared.pbr.pbr_material` — shader box projection, no UVs
  needed, bump from height (quick, any Rhino mesh); the family recipes in `materials` — real-size
  `BoxUV`/`directional_uv` UVs, so normal maps and directional grain work;
  `renderer.luxcore.luxcore.lux_textured` — native LuxCore tree (Randomized Tiling).

### Scaling and UV steps
1. **Shortlist from a contact sheet:** Poly Haven thumbnails
   (`cdn.polyhaven.com/asset_img/thumbs/<id>.png?width=300`) for 10-20 candidates in one image.
   `api.polyhaven.com/assets?t=textures` filtered by id/tags finds what `polyhaven_fetch.py
   search <category>` misses.
2. **Open the colour map itself**, not the sphere thumbnail or the tags — a "white, clean" tag can
   sit on painted boards or a weathered, stained surface. Check its features against the table.
3. **Judge the map by its measured mean, not its thumbnail.** Average the diffuse map in linear
   space (sRGB -> linear, mean per channel) before committing: maps that look like a pale grey
   paver routinely measure warm brown. Blender returns 8-bit maps sRGB-encoded (api-traps).
   → `materials.shared.pbr.albedo_material(tex_id, name, target)` (measures and caches the mean in meta.json).
4. **Scale with a gain of target/mean per channel** (Vector Math MULTIPLY, or a Mix MULTIPLY whose
   B colour is set above 1 by script — measured unclamped; only the Mix *Factor* clamps at 1).
   Tint a scan with a gain, never with a flat-colour Mix: Mix(MIX) of a flat colour over the map at
   a high factor replaces the texture, and the surface renders as plain colour.
5. **Directional or not decides the UVs.** `box_uv` projects each face along its own dominant
   axis, so the image turns 90° from one face to the next — invisible on non-directional maps
   (plain concrete, plaster, terrazzo, mortar, gravel, most granites), wrong on anything with a
   direction: wood grain and veneer, bamboo, board-formed concrete, brushed/linear metal,
   vein-cut or banded stone (travertine), ribbed or corrugated sheet, woven fabric, long-format
   tiles and pavers. Those take `archviz.directional_uv(obj, size_m, axis)`: U follows the
   element's long axis (or the given world axis) on every face; `along="V"` when the texture's
   direction runs up the image.
6. **Variation:** Object Info Random, Geometry › Random per Island (per plank/tile in one mesh).
7. **Node trees** in labelled frames (`materials.shared.nodes.G`). Mix nodes keep hidden
   same-named sockets → `materials.shared.nodes.sock()`.
8. **Prove the texture survives:** high-pass sigma (`imgstats`) of a native render crop against
   the reference crop at a matching screen scale.

### Tiled maps with joints
- Formwork and panel textures carry joint lines at their tile edges. Box UVs computed from world
  coordinates put a joint at world 0 — usually the camera axis, where it becomes one long line
  running to the vanishing point on floor and ceiling. Offset the UVs by a fraction of a tile.
- **Tile edges draw a grid** wherever the map repeats in both directions; on a curved wall that
  reads as panels the reference doesn't have.
- Bisect odd lines by unlinking chains (normal/bump, grunge) in a border render: a line that
  survives every unlink is in the image itself.
