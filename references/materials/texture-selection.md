# Texture Selection

## Choosing and scaling a texture
- **Judge a map by its measured mean, not its thumbnail.** Average the diffuse map in linear
  space (sRGB -> linear, mean per channel) before committing: maps that look like a pale grey
  paver routinely measure warm brown, and a map whose mean sits far from the target will not
  scale cleanly. Hit the target albedo with a per-channel gain of target/mean (Vector Math
  MULTIPLY, or a Mix MULTIPLY whose B colour is set above 1 by script — measured unclamped; only
  the Mix *Factor* clamps at 1). Measure the mean on linear values: Blender returns 8-bit maps
  sRGB-encoded (api-traps).
  → `materials.pbr.albedo_material(tex_id, name, target)` (measures and caches the mean in meta.json).
- **Tint a scan with a gain, never with a flat-colour Mix.** Mix(MIX) of a flat colour over the
  map at a high factor replaces the texture, and the surface renders as plain colour. Prove the
  texture survives: high-pass sigma (`imgstats`) of a native render crop against the reference
  crop at a matching screen scale.
- **A substitute for a missing map is chosen by texture as well as mean.** A "clean" crop of a
  marble scan reads blank at floor distance; compare high-pass sigma, not only colour.
- Pick from a contact sheet: Poly Haven thumbnails
  (`cdn.polyhaven.com/asset_img/thumbs/<id>.png?width=300`) for 10-20 candidates in one image.
  `api.polyhaven.com/assets?t=textures` filtered by id/tags finds what `polyhaven_fetch.py
  search <category>` misses.
- Check the map's own features before choosing it: rows of tie holes, strong directional stains
  or a visible repeat disqualify a map for a large jointless surface however good its mean is.
  Open the colour map itself, not the sphere thumbnail or the tags — a "white, clean" tag can sit
  on painted boards or a weathered, stained surface.
- **Clean white finishes** (concrete, plaster, mortar): a good scan still reads dirty at its own
  contrast. Keep only a fraction of its tonal variation around a flat target — Mix(flat albedo,
  scaled scan, fac) with fac set from the shot — desaturate, soften the normal map, and leave out
  panel joints and tie holes unless the design has them. White paint and plaster sit near 0.8
  albedo, cement mortar lower.
- **Aggregate, chip and grain size is a design choice** — take it from the brief or the
  reference, and judge it at the shot's scale. Bake such patterns to a seamless image (numpy,
  tileable via FFT noise + wrapped stamps) when the renderer has no procedural textures (LuxCore).
- **Directional or not decides the UVs.** `box_uv` projects each face along its own dominant
  axis, so the image turns 90° from one face to the next — invisible on non-directional maps
  (plain concrete, plaster, terrazzo, mortar, gravel, most granites), wrong on anything with a
  direction: wood grain and veneer, bamboo, board-formed concrete, brushed/linear metal,
  vein-cut or banded stone (travertine), ribbed or corrugated sheet, woven fabric, long-format
  tiles and pavers. Those take `archviz.directional_uv(obj, size_m, axis)`: U follows the
  element's long axis (or the given world axis) on every face; `along="V"` when the texture's
  direction runs up the image.
- Variation: Object Info Random, Geometry › Random per Island (per plank/tile in one mesh).
- Node trees in labelled frames (`materials.nodes.G`). Mix nodes keep hidden same-named sockets
  → `materials.nodes.sock()`.
- **Which Poly Haven builder:** `materials.pbr.pbr_material` — shader box projection, no UVs needed,
  bump from height (quick, any Rhino mesh); the family recipes in `materials` — real-size
  `BoxUV`/`directional_uv` UVs, so normal maps and directional grain work; `materials.luxcore.lux_textured`
  — native LuxCore tree (Randomized Tiling). Clear glass and water: `materials.pbr.dielectric`.


### Tiled maps with joints
- Formwork and panel textures carry joint lines at their tile edges. Box UVs computed from world
  coordinates put a joint at world 0 — usually the camera axis, where it becomes one long line
  running to the vanishing point on floor and ceiling. Offset the UVs by a fraction of a tile.
- Bisect odd lines by unlinking chains (normal/bump, grunge) in a border render: a line that
  survives every unlink is in the image itself.
- **Tile edges draw a grid** wherever the map repeats in both directions; on a curved wall that
  reads as panels the reference doesn't have.
