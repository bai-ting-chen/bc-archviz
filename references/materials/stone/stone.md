# Stone

- Long-strip pavers: a Brick Texture on (y, x) puts the long axis across the façade. Read the
  direction from which vanishing point the long joints run to. **Mortar has to stay legible at
  frame scale** — too thin or too close in tone and the joints vanish entirely; give it real
  width and a clearly darker grey, then set per-paver tone with Color1/Color2.
  → `materials.stone.stone.long_pavers(tex_id, name, target, long_axis="Y")`.

- **Polished speckled granite** `materials.stone.stone.polished_granite()`: world-space Voronoi crystals sized
  to the real grain, cell value -> CONSTANT ramp of 3-4 stone tints, low roughness, IOR 1.55, no
  coat; edges by Bevel modifier. Polished dark granite measures far darker than intuition
  suggests — take the albedo off a reference, not from memory.
- **Large tiles** `materials.stone.stone.stone_tiles()`: Brick Texture offset 0 on BoxUV, per-tile tone, cloud
  noise + specks, recessed joints (`bump.invert = True`); floors glossier than walls, with a coat.
- **Slab floors modelled as separate pieces** (one object per slab or band): per-object random
  per-unit variation by object (RULES MAT_06; ranges in [variation](../../effects/variation.md)), so neighbours
  differ as laid stone does. Joints as a material hairline (≤ 1 mm, slightly darker), not a gap.
- **Honed stone** (lobby limestone/marble) shows soft, blurred reflections of walls and people:
  Cycles roughness ~0.3–0.5 modulated by the map. A roughness exported from another renderer
  (e.g. 0.9) is not a Cycles value; set it against the reference.
