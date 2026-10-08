# Materials

Code: `study_materials.py` (concrete, gravel, coated wood, glass, glazed tiles), `interior.py`
(granite, stone tiles, steel, pool water, steam, emitters), `wear.py` / `wood_wear.py` (edge-wear.md).

## Physical ranges and conventions
- Non-metal albedo ≈ 0.03–0.85 linear (charcoal 0.02, asphalt 0.04, brick 0.26, concrete 0.51,
  paper 0.79, marble 0.83); keep ≤ 0.8 to limit bounce noise. Hit a measured albedo with
  levels: gamma then per-channel gain solved from the map mean (`solve_levels`).
- Real IOR (stone/concrete 1.5, water 1.333, glass 1.52); `Specular IOR Level` 0.5 = neutral.
  Specular Tint white on dielectrics; on metals it is the F82 edge tint.
- Colour maps sRGB, data maps Non-Color. ARM: R = AO (unused — double-darkens), G rough, B metal.
- Image maps on real-metre UVs (`box_uv`, Poly Haven `dimensions_mm`). Tangent-space normal maps
  need a UV map; shader-box-projected maps get Bump from height instead (`archviz.pbr_material`).
- Bump: Distance = real height in m, Strength 1. Relief chain: Normal Map → Bump → (Bevel node).
  Bevel node costs ~20 % and is invalid on MNEE casters/receivers → Bevel *modifier* there.
- **Choose and scale a texture by its measured mean, not its thumbnail.** Average the diff map
  in linear space (sRGB → linear, then mean per channel) before picking it: `concrete_floor_03`
  turned out brown (0.28, 0.20, 0.15) for a pale grey paver, while `concrete_floor_worn_001`
  (0.09, 0.09, 0.09) is neutral and scales cleanly. Hit the target albedo with a Vector Math
  MULTIPLY of target/mean per channel. A Mix colour socket clamps factors above 1, so it cannot
  brighten a dark map. → `lookdev.albedo_material(tex_id, name, target)` (measures and caches
  the mean in the texture's meta.json).
- Pick from a contact sheet: Poly Haven thumbnails
  (`cdn.polyhaven.com/asset_img/thumbs/<id>.png?width=300`) for 10–20 candidates in one image.
  `api.polyhaven.com/assets?t=textures` filtered by id/tags finds what `polyhaven_fetch.py
  search <category>` misses.
- Variation: Object Info Random, Geometry › Random per Island (per plank/tile in one mesh).
- Node trees in labelled frames. Mix nodes keep hidden same-named sockets → `study_materials.sock()`.

## Concrete — `concrete_study()`
concrete_wall_009 × (0.76, 0.82, 0.99) → albedo 0.265; roughness Mix(0.72, map, 0.45); IOR 1.5,
coat 0.03; Normal Map 0.6 → Bump 4 mm → Bevel 2.5 mm. Leak stain: Megascans leakage on `SpanUV`
(`height_span_uv`, v 0..0.9, REPEAT) × (1 − |N.z|).

### Monolithic concrete (basements, car parks, cast-in-place frames)
- **One material** for floor, walls, ceiling, beams and columns (user preference). Vary it by
  world-space masks inside the shader, not by separate materials: Geometry › Normal Z gives
  *up* (floor: lower roughness, sealed-slab sheen, softer stains), *down* (ceilings: less
  grunge) and *vertical* (walls: damp band at the foot).
- The leak-stain map (Megascans, `library/local/`) needs the user's own download; when it is
  missing, build `concrete_study(stain=False)` and say so — never silently drop a layer.
- Check the recipe's tone multiplier against the reference: the default is a cool match
  and reads blue-grey next to a warm reference.
- **Grunge comes in patches, not streaks** (user correction; check the reference before adding
  streaks). Recipe, all world-space Noise: patch field = low-frequency noise (scale ~0.45/m,
  some Distortion) **plus** centred high-frequency noise (~18/m) × ~0.2 *before* a narrow
  threshold → ragged, speckled borders; interior = mid-frequency mottle × speckle; clean gaps
  between patches. Separate decorrelated fields (Mapping › Location offset) for floor stains.
  Damp band at the foot of walls/columns: world Z plus the ragged noise, thresholded ~0.4–0.7 m.
  Concave-corner grime: AO (outside, ~0.3 m) × fine noise. Multiplying several 0..1 masks
  quickly washes them out — remap inner/speckle into ~0.55..1 to keep patches strong.
- Fresh breaks under direct floods: keep their tint barely above the surface (≈ ×1.03); the
  recipe's lighter paste reads as white paint flecks when lit head-on.

### Tiled maps with joints
Formwork/panel textures carry joint lines at their tile edges. Box UVs computed from world
coordinates put a joint at world 0 — usually the camera axis, where it becomes one long line
to the vanishing point on floor and ceiling. Offset the UVs by a fraction of a tile. Bisect
odd lines by unlinking chains (normal/bump, grunge) in a border render: a line that survives
both is in the image itself.

**Tile edges draw a grid** wherever the map repeats in both directions, and on a curved wall it
reads as panels the reference doesn't have. Check the map's own features too (rows of tie holes
in `concrete_wall_006`) before choosing it for a jointless pour.

**Board marks the other way round.** Most board-formed maps run horizontal. To turn them
vertical, feed a FLAT projection with Combine(z, along-wall): use x+y on planar walls, and on a
cylinder use arc length (atan2(y−cy, x−cx)·R), which also avoids box-projection stretch on the
curve. Then add tone per formwork strip (white noise on floor(along/0.9 m), ±8 %) × a
low-frequency noise (±12 %). That reads as cast panels and hides the tile repeat. If the map's
stains repeat visibly, mix the diffuse 30–40 % toward its mean.
→ `lookdev.vertical_boards(mat, cylinder=(cx, cy, r) | None)`.

**Monolithic but not identical.** A drum or infill of the "same" concrete read darker than the
walls in the reference under the same light (ratio 0.69). Match the measured ratio with its own
albedo rather than relighting.

## Exposed aggregate, pavers, litter
- Exposed-aggregate precast (columns, slab edges): `gravel_embedded_concrete`, box-mapped at
  real size, albedo ~0.30 warm grey. Use the same map on fascia and soffit bands, and keep
  soffits (Normal Z < −0.5) on a smoother, darker concrete via a second material slot.
- Long-strip pavers: a Brick Texture on (y, x) puts the long axis across the façade. Read the
  direction from which vanishing point the long joints run to. Mortar ≥ 8 mm and ~0.2 grey, or
  the joints vanish at frame scale; set per-paver tone with Color1/Color2 0.95/0.72.
  → `lookdev.long_pavers(tex_id, name, target, long_axis="Y")`.
- Leaf litter and foliage: one GN group (Distribute Points on Faces, with selection = Z below a
  limit AND a noise patch threshold → Instance on Points with random rotation and scale), and
  per-instance tone via Object Info › Random. A patch threshold of ~0.5 on a 0.6/m noise is very
  sensitive: 0.42 blanketed a wall, 0.53 removed everything. → `scatter.scatter(objs,
  scatter.leaf_proto(...), density, z_max=, patch=)` + `lookdev.random_tone_material`.

## Gravel, true displacement — `displaced_ground()` + `enable_true_displacement()`
Displacement Scale = amount (0.12 m), Midlevel = −shift/amount; method BOTH (Displacement Only once
finely diced); Subdivision SIMPLE adaptive 1 px, last; `cycles.dicing_camera` = render camera.

## Wood
- **Coated** `coated_wood()`: coat trap — satin varnish = LOW coat (0.2) + TIGHT coat roughness
  (0.04); spread base roughness toward matte; don't lower IOR. Coat › Normal can stay smooth over
  bumped wood (to try).
- **Oak cladding**: `oak_wood_planks` (1.2 m, grain along U) with `grain_uv(o, 3.0, axis="Z")` →
  ~230 mm vertical boards with knots. `oak_veneer_01` (grain along V → `along="V"`) reads as fine
  veneer. Battens: walnut_veneer, matte (a coat mirrors lenses as halos).

## Stone
- **Polished speckled granite** `interior.polished_granite()`: world-space Voronoi crystals (~6 mm),
  cell value → CONSTANT ramp (matrix / brown / grey / cream), roughness 0.04 ±0.02, IOR 1.55, no
  coat; edges by Bevel modifier 3 mm. Mean albedo ≈ 0.05 (a MIR reference read darker).
- **Large tiles** `interior.stone_tiles()`: Brick Texture offset 0 on BoxUV, per-tile tone, cloud
  noise + specks, recessed joints (`bump.invert = True`); floor rough 0.3 + coat 0.35/0.1, wall 0.55.
- Rough mineral surfaces (plaster, concrete, brick, fabric): Principled **Diffuse Roughness**
  (Oren-Nayar, 4.3+) — to try.

## Metal
`interior.polished_steel()`: Metallic BSDF F82, base (0.67, 0.64, 0.60), edge 0.8, rough 0.05,
shade smooth. Brushed: Anisotropic + Tangent. Measured n,k: Metallic BSDF *Physical Conductor*.

## Glass
Principled transmission 1, IOR 1.52, roughness 0. Thin Film for coated glazing (to try).
Re-lathe Rhino glassware at 256 segments for close-ups.
Sheer curtains: Mix(Diffuse, Translucent, 0.5) at albedo ~0.8, so a lit room behind glows
through them (lighting-camera › Glass and what it shows). → `lookdev.sheer()`.
**Liquid in glass**: no nested-IOR priority in Cycles — three surfaces: GLASS (1.52), INTERFACE
below the waterline (1.52/1.333), WATER_SURFACE (1.333) → `glassware.glass_of_water()`; check
normals per wall.

## Water (pool)
- `interior.pool_water()`: Principled transmission 1, IOR 1.333, ripple bump 1.5 mm + **Volume
  Absorption** tint (0.45, 0.85, 0.72) density 1/m → brown → green with depth.
- Geometry: `interior.water_surface(obj, 0.1)` = top face only, diced, smooth (MNEE-ready; the
  volume still works over an opaque basin). Waterline a few cm under the coping.
- Rippled sunlit pool: Ocean modifier on a diced plane — no choppiness on short waves,
  `wave_scale_min` ≥ 5 × grid spacing, λ 10–30 cm for caustic networks.
- To try (manual-confirmed): **Volume Coefficients** node (absorption per channel in 1/m — use
  measured water absorption) + Volume Scatter phase **Fournier-Forand** (IOR 1.0–1.2, backscatter)
  for haze/light shafts; noise → roughness for wind patches; Gabor texture for directional ripples.
- Steam: `interior.steam()` — Principled Volume, noise × height fade, anisotropy 0.5.
