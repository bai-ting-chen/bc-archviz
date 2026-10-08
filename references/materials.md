# Materials

Code: `study_materials.py` (concrete, gravel, coated wood, glass, glazed tiles), `interior.py`
(granite, stone tiles, steel, pool water, steam, emitters), `lookdev.py` (measured-albedo PBR,
vertical boards, long pavers, sheers, glass shells), `wear.py` / `wood_wear.py` (edge-wear.md).

The recipes below are *shapes* — which nodes, wired which way, and why. Their tuned values live
in whichever study last used them (RULES 0); read the recipe here, then set the numbers from the
shot in front of you.

## Physical ranges and conventions
These transfer to any scene and any renderer — they are measurements of the world, not settings.

- Non-metal albedo ~ 0.03-0.85 linear: charcoal 0.02, asphalt 0.04, brick 0.26, concrete 0.51,
  paper 0.79, marble 0.83. Keep <= 0.8 to limit bounce noise.
- Real IOR: stone/concrete 1.5, water 1.333, glass 1.52. `Specular IOR Level` 0.5 = neutral.
  Specular Tint white on dielectrics; on metals it is the F82 edge tint.
- Polished steel base ~ (0.67, 0.64, 0.60) with edge tint ~0.8 — a property of the metal, not of
  a scene. For other metals, measured n,k go into Metallic BSDF *Physical Conductor*.
- Colour maps sRGB, data maps Non-Color. ARM: R = AO (leave unused — it double-darkens),
  G rough, B metal.
- Image maps on real-metre UVs (`box_uv`, Poly Haven `dimensions_mm`). Tangent-space normal maps
  need a UV map; shader-box-projected maps get Bump from height instead (`archviz.pbr_material`).
- Bump: Distance = the real height of the relief in metres, Strength 1. Relief chain:
  Normal Map -> Bump -> (Bevel node). The Bevel node costs ~20 % and is invalid on MNEE
  casters/receivers → use the Bevel *modifier* there.

## Choosing and scaling a texture
- **Judge a map by its measured mean, not its thumbnail.** Average the diffuse map in linear
  space (sRGB -> linear, mean per channel) before committing: maps that look like a pale grey
  paver routinely measure warm brown, and a map whose mean sits far from the target will not
  scale cleanly. Hit the target albedo with a Vector Math MULTIPLY of target/mean per channel —
  a Mix colour socket clamps factors above 1, so it cannot brighten a dark map.
  → `lookdev.albedo_material(tex_id, name, target)` (measures and caches the mean in meta.json).
- Pick from a contact sheet: Poly Haven thumbnails
  (`cdn.polyhaven.com/asset_img/thumbs/<id>.png?width=300`) for 10-20 candidates in one image.
  `api.polyhaven.com/assets?t=textures` filtered by id/tags finds what `polyhaven_fetch.py
  search <category>` misses.
- Check the map's own features before choosing it: rows of tie holes, strong directional stains
  or a visible repeat disqualify a map for a large jointless surface however good its mean is.
- Variation: Object Info Random, Geometry › Random per Island (per plank/tile in one mesh).
- Node trees in labelled frames. Mix nodes keep hidden same-named sockets → `study_materials.sock()`.

## Concrete
`concrete_study()`. Structure: map x tone multiplier to hit the target albedo, roughness mixed
between map and a constant, IOR 1.5, light coat, Normal Map -> Bump -> Bevel. Leak stain rides on
`height_span_uv` (v clamped below 1, REPEAT) x (1 - |N.z|) so streaks only run down verticals.

### Monolithic concrete (basements, car parks, cast-in-place frames)
- **One material** for floor, walls, ceiling, beams and columns (user preference). Vary it by
  world-space masks inside the shader, not by separate materials: Geometry › Normal Z separates
  *up* (floor: lower roughness, sealed-slab sheen, softer stains), *down* (ceilings: less grunge)
  and *vertical* (walls: damp band at the foot).
- The leak-stain map (Megascans, `library/local/`) needs the user's own download; when it is
  missing, build `concrete_study(stain=False)` and say so — never silently drop a layer.
- Check the recipe's tone multiplier against the reference. The default is a cool match and will
  read blue-grey next to a warm reference.
- **Grunge comes in patches, not streaks** (user correction — check the reference before adding
  any streak). Shape, all world-space Noise: a low-frequency patch field (with some Distortion)
  *plus* a centred high-frequency field at low amplitude, summed *before* a narrow threshold —
  that sum is what gives ragged, speckled borders instead of soft blobs. Inside a patch,
  mid-frequency mottle x speckle; keep clean gaps between patches. Use separate decorrelated
  fields (Mapping › Location offset) for floor stains so they don't echo the wall.
- Damp band at the foot of walls and columns: world Z thresholded, plus the same ragged noise so
  the top edge isn't a straight line.
- Concave-corner grime: AO node (**outside**, not Inside) x fine noise, into the grunge
  darkening. See edge-wear.md › Concave corners.
- **Multiplying several 0..1 masks washes them out fast.** Remap the inner masks into a narrow
  high range before multiplying, or the patches disappear.
- Fresh breaks under direct floods want their tint only *barely* above the surface; a visibly
  lighter paste reads as white paint flecks when lit head-on.

### Tiled maps with joints
- Formwork and panel textures carry joint lines at their tile edges. Box UVs computed from world
  coordinates put a joint at world 0 — usually the camera axis, where it becomes one long line
  running to the vanishing point on floor and ceiling. Offset the UVs by a fraction of a tile.
- Bisect odd lines by unlinking chains (normal/bump, grunge) in a border render: a line that
  survives every unlink is in the image itself.
- **Tile edges draw a grid** wherever the map repeats in both directions; on a curved wall that
  reads as panels the reference doesn't have.
- **Board marks run the other way round.** Most board-formed maps run horizontal. To stand them
  up, feed a FLAT projection with Combine(z, along-wall): x+y on planar walls, and on a cylinder
  the arc length (atan2(y-cy, x-cx)·R), which also avoids box-projection stretch on the curve.
  Then vary tone per formwork strip (white noise on floor(along / strip width)) x a low-frequency
  field — that reads as cast panels and hides the tile repeat. If the map's stains repeat
  visibly, mix the diffuse part-way toward its own mean.
  → `lookdev.vertical_boards(mat, cylinder=(cx, cy, r) | None)`.
- **Monolithic but not identical.** A drum or infill of the "same" concrete often measures darker
  than the walls under the same light. Match the measured ratio by giving it its own albedo
  rather than relighting it.

## Exposed aggregate, pavers, litter
- Exposed-aggregate precast (columns, slab edges): box-map an aggregate map at real size. Use the
  same map on fascia and soffit bands, and put soffits (Normal Z < -0.5) on a smoother, darker
  concrete via a second material slot.
- Long-strip pavers: a Brick Texture on (y, x) puts the long axis across the façade. Read the
  direction from which vanishing point the long joints run to. **Mortar has to stay legible at
  frame scale** — too thin or too close in tone and the joints vanish entirely; give it real
  width and a clearly darker grey, then set per-paver tone with Color1/Color2.
  → `lookdev.long_pavers(tex_id, name, target, long_axis="Y")`.
- Leaf litter and foliage: one GN group (Distribute Points on Faces, selection = Z below a limit
  AND a noise patch threshold -> Instance on Points with random rotation and scale), per-instance
  tone via Object Info › Random. → `scatter.scatter(...)` + `lookdev.random_tone_material`.
  **The patch threshold is knife-edge** — a hair too low blankets the surface, a hair too high
  clears it. Bisect it against a render rather than reasoning about it.

## True displacement
`displaced_ground()` + `enable_true_displacement()`. Displacement Scale = the relief height,
Midlevel = -shift/scale; method BOTH (Displacement Only once finely diced); Subdivision SIMPLE
adaptive 1 px, last in the stack; `cycles.dicing_camera` = the render camera.

## Wood
- **Coated** `coated_wood()`: the coat trap — satin varnish is a *low* coat weight with *tight*
  coat roughness, not a strong rough coat. Spread the base roughness toward matte; don't lower
  IOR to compensate. Coat › Normal can stay smooth over bumped wood (to try).
- Cladding: pick the plank map by its real size and run `grain_uv(obj, tex_size_m, axis)` so the
  grain follows the boards. A map whose grain runs along V needs `along="V"`.
- Battens and veneers want matte — a coat mirrors lenses as halos.

## Stone
- **Polished speckled granite** `interior.polished_granite()`: world-space Voronoi crystals sized
  to the real grain, cell value -> CONSTANT ramp of 3-4 stone tints, low roughness, IOR 1.55, no
  coat; edges by Bevel modifier. Polished dark granite measures far darker than intuition
  suggests — take the albedo off a reference, not from memory.
- **Large tiles** `interior.stone_tiles()`: Brick Texture offset 0 on BoxUV, per-tile tone, cloud
  noise + specks, recessed joints (`bump.invert = True`); floors glossier than walls, with a coat.
- Rough mineral surfaces (plaster, concrete, brick, fabric): Principled **Diffuse Roughness**
  (Oren-Nayar, 4.3+) — to try.

## Metal
`interior.polished_steel()`: Metallic BSDF F82, low roughness, shade smooth. Brushed:
Anisotropic + Tangent.

## Glass
- Principled transmission 1, IOR 1.52, roughness 0. Thin Film for coated glazing (to try).
- Re-lathe Rhino glassware at a high segment count for close-ups.
- Sheer curtains: Mix(Diffuse, Translucent, ~0.5) at high albedo, so a lit room behind glows
  through them (lighting-camera.md › Glass and what it shows). → `lookdev.sheer()`.
- **Liquid in glass**: Cycles has no nested-IOR priority, so model three surfaces — GLASS (1.52),
  INTERFACE below the waterline (1.52/1.333) and WATER_SURFACE (1.333) →
  `glassware.glass_of_water()`. Check normals per wall.

## Water (pool)
- `interior.pool_water()`: Principled transmission 1, IOR 1.333, a shallow ripple bump, and
  **Volume Absorption** for the tint — depth does the colour work, so a pool reads green in the
  deep end and clear at the step without any gradient map.
- Geometry: `interior.water_surface(obj, …)` = top face only, diced, smooth (MNEE-ready; the
  volume still works over an opaque basin). Keep the waterline just under the coping.
- Rippled sunlit pool: Ocean modifier on a diced plane — no choppiness on short waves, and
  `wave_scale_min` >= 5 x grid spacing or the waves alias. Short wavelengths give the tight
  caustic networks; long swell does not.
- To try (manual-confirmed): **Volume Coefficients** node (absorption per channel in 1/m, from
  measured water absorption) + Volume Scatter phase **Fournier-Forand** (IOR 1.0-1.2,
  backscatter) for haze and light shafts; noise -> roughness for wind patches; Gabor texture for
  directional ripples.
- Steam: `interior.steam()` — Principled Volume, noise x height fade, anisotropy ~0.5.
