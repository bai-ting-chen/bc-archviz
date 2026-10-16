# Materials

Code: `study_materials.py` (concrete, gravel, coated wood, glass, glazed tiles), `interior.py`
(granite, stone tiles, steel, pool water, steam, emitters), `lookdev.py` (measured-albedo PBR,
vertical boards, long pavers, sheers, glass shells, glass distortion), `wear.py` / `wood_wear.py`
(edge-wear.md), `terrain.py` + `scatter.py` (hill, ground, meadow), `vegetation.py` (grass, wet, dew),
`tile_mapping.py` / `tile_layout.py` / `tile_surface.py` / `tile_damage.py` (› Tiles).

Contents: Physical ranges · Choosing and scaling a texture · Concrete · Exposed aggregate, pavers,
litter · Terrain · Grass and meadow · Wet surfaces and dew · True displacement · Wood · Stone ·
Metal · Glass · Water · Randomness and anti-tiling.

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
  scale cleanly. Hit the target albedo with a per-channel gain of target/mean (Vector Math
  MULTIPLY, or a Mix MULTIPLY whose B colour is set above 1 by script — measured unclamped; only
  the Mix *Factor* clamps at 1). Measure the mean on linear values: Blender returns 8-bit maps
  sRGB-encoded (api-traps).
  → `lookdev.albedo_material(tex_id, name, target)` (measures and caches the mean in meta.json).
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
- Node trees in labelled frames (`study_materials.G`). Mix nodes keep hidden same-named sockets
  → `archviz.sock()`.
- **Which Poly Haven builder:** `archviz.pbr_material` — shader box projection, no UVs needed,
  bump from height (quick, any Rhino mesh); the `study_materials` / `lookdev` recipes — real-size
  `BoxUV`/`directional_uv` UVs, so normal maps and directional grain work; `lux_materials.lux_textured`
  — native LuxCore tree (Randomized Tiling). Clear glass and water: `archviz.dielectric`.

## Concrete
`concrete_study()`. Structure: map x tone multiplier to hit the target albedo, roughness mixed
between map and a constant, IOR 1.5, light coat, Normal Map -> Bump -> Bevel. Leak stain rides on
`height_span_uv` (v clamped below 1, REPEAT) x (1 - |N.z|) so streaks only run down verticals.

### Monolithic concrete (basements, car parks, cast-in-place frames)
- **One material** for floor, walls, ceiling, beams and columns. Vary it by
  world-space masks inside the shader, not by separate materials: Geometry › Normal Z separates
  *up* (floor: lower roughness, sealed-slab sheen, softer stains), *down* (ceilings: less grunge)
  and *vertical* (walls: damp band at the foot).
- The leak-stain map (Megascans, `library/local/`) needs the user's own download; when it is
  missing, build `concrete_study(stain=False)` and say so — never silently drop a layer.
- Check the recipe's tone multiplier against the reference. The default is a cool match and will
  read blue-grey next to a warm reference.
- **Grunge comes in patches, not streaks** (RULES 8c; check the reference before adding any
  streak). Shape, all world-space Noise: a low-frequency patch field (with some Distortion)
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

- Rough, weathered concrete from a dark scanned map: `study_materials.retone(mat, target, tex_id)` -
  desaturate, then scale the measured mean to the target albedo (the multiply keeps pits and
  pores). Runoff streaks and cracks: edge-wear.md > Runoff streaks, cracks.

### Burnished / polished white concrete (microcement, soffits)
- Reads glossy, not matte: low roughness varied in soft clouds; the plaster relief mostly
  polished off (sub-millimetre bump). Tone clouds at two scales; lighting gradients swallow small
  tone differences, so a variation that looks right in the node preview can render perfectly
  clean — judge it in a render. Trowel marks: a moderately stretched noise (a strong stretch draws
  parallel lines), rotated, high distortion, thresholded to its top few percent and clustered by
  a patch mask, lighter and smoother than the field.
- A neutral white next to a strongly coloured surface takes its bounce colour (a soffit over a
  turquoise pool renders cyan): correct the albedo toward the reference rather than relighting.
- Faint dirty arris on huge meshes (30 m slabs, canopies): shader **Bevel normal vs true
  normal** as the edge mask (no dicing needed) — GN `edge_dist` would need the mesh diced.
  "Very faint" sits just above visibility: set the darkening with a control (RULES 9), since a
  value that looks faint in the shader can vanish entirely in the render.

### Tiles: layout, mapping, surface, cracks
Real tiles never match a downloaded map, so layout, joint and face are separate real-unit knobs:
- `tile_mapping.planar_uv / cylinder_uv / annulus_uv` write metre UVs on Rhino meshes (arc length on
  curved walls; `annulus_uv(like=wall)` continues a wall's columns onto a ring). Which way joints
  run on returns and soffits is a per-project decision — keep it a switch.
- `tile_layout.add_layout` turns the metre coordinate into Tile ID, Tile UV, signed Edge (m), Joint,
  Cell, Tile Size (stack/running bond, rotation, origin, corner radius, per-tile jitter).
- `tile_surface.tile_material(...)` is the material: glaze coat over any PBR face (albedo
  normalised, each tile its own patch of the map) or a procedural glaze, rounded shoulder + recess
  as metre height, grout, patchy joint dust, per-tile tint/gloss/tilt, waviness, specks; every
  knob on the `TileLayout` / `TileFinish` / `TileDamage` group nodes (`set_param`, `toggle`).
- **Cracks** (`tile_damage`, kind 1): a noise-warped Voronoi *Distance to Edge* network in each
  tile's own frame (per-tile offset and cell size), drawn only around cells picked by their hash
  and under a patch mask — 0-3 runs per tile, any position and angle, Y-junctions, varying width.
  Hand-placed chords (one line across, mid-tile) read as stamped. Crack cells **longer than the
  tile's short side** give long gentle curves; cells about the tile width give crazing-like
  closed cells. Picked cells are rigid pieces (own lift and tilt), so the reflection breaks across
  the crack. A hairline is sub-pixel at room distance: what reads is the patchy dirt band (dirt
  and limescale wick into the crack and the porous body) — `Crack Dirt`, `Dirt Width`.
- **Chips / edge flakes:** in development — not yet a method.
- **Relief:** in the main frame displace only the damage (`tile_surface.use_damage_displacement`;
  piece steps and cuts become geometry, profile and joints stay bump). Displacing the full tile
  height pulls the wall's boundary edges inward along the joint recess and opens bright slits to
  the sky at floor and ceiling junctions. A macro view can displace everything, but only on the
  objects in frame with a high offscreen dicing scale (every wall diced from a macro camera runs
  an 8 GB GPU out of memory).
- **Tune on a flat pattern sheet first:** render the damage masks (emission, 1 sample) on a flat
  wall of the real tile size with the joints drawn, several parameter sets side by side — seconds
  per sheet. Then confirm in the final view (RULES 8). Use the scene's own depth/width values on the
  sheet: defaults differ, and a sheet without joints makes edge damage look like islands.

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

## Terrain (landform grading)
`terrain.landform_group(centre=…, pad_half=…, fall=…, run=…)` + `terrain.add_terrain(group, ground)`.
- A building on a hill: flat pad just under the slab, an apron, then the fall as a smoothstep in
  the distance from the pad - a rounded crest **and** a rounded toe (landform grading, natural
  slopes), never a cone or a linear batter. Warp the distance with a slow noise so contours
  wander; add a broad roll beyond and pasture hummocks (+-5-10 cm at ~1.5 m).
- Steepest slope of a smoothstep fall = 1.5 x fall / run. Gentle / mowable: <= 4:1 (25 %);
  3:1 is the usual limit for maintained grass.
- To read as a hill, the camera stands down the slope with the crest against the sky; the
  edge of the generated grid must stay out of frame (the frustum mask hides the rest).
- `terrain.height(x, y, ...)` is the no-noise twin for placing a camera at eye height.

## Grass and meadow
- Vendor grass clumps are often real blade geometry (no opacity cards) - check the units of
  each volume against a known plant height before anything else (one grass volume was in mm
  where its tree volume was cm; read in cm, clover came out 1 m tall).
- Scatter: `scatter.meadow_layer_group(scatter.load_scatter_on_surface())` - Blender's own
  *Scatter on Surface* (native, Poisson/random, collection + Pick Instance) wrapped with mask
  fields: species patch noise, a **shared** bare-soil noise (the ground shader opens to soil with
  the same 4D noise, `terrain.BARE_W`, so bare spots show earth), clearance from the pad, and
  the **camera frustum + distance** (only what the camera can see; the crest hides the rest).
  One object per species; Align Rotation off (grass grows up, gravitropism), small random lean.
- Density is set by clump size: a few-blade lawn clump needs ~200 /m2 to close the sward
  (30 /m2 left mostly soil). ~0.5-1 M instances render fine on 8 GB; unique meshes cost memory,
  instances barely.
- Blade material `vegetation.blade_material`: Principled + Translucent added (green leaf
  R ~0.10-0.15, T ~0.05-0.10 at the 550 nm green peak, lower across the rest of the visible), roughness ~0.45 (waxy cuticle), per-instance value
  0.8-1.15 and a patchy straw/dry mix on the instance location (RULES 8c, 8d). A grass canopy's
  visible albedo is only ~0.05-0.1: under a high-contrast AgX look it sinks - choose a softer
  look rather than brightening the albedo.
- Mixed species read as pasture: a dense low carpet + tuft drifts + broad-leaf (clover) patches
  + sparse seed heads/flowers.

## Wet surfaces and dew
- Wet = darker and more saturated (internal reflection in the film, Lekner-Dorf): albedo ->
  dry^gamma (1.4 for soil/stone; grass reads better at ~1.7) + a water coat (IOR 1.33).
- A wet lawn seen from a low camera is mostly grazing angles: the film's Fresnel sheen of a
  grey sky greys it out (saturation drops). A darker base keeps the "wet" reading; the sheen is
  physically right (dewy lawns look silvery under fog).
- Dew beads are sub-pixel beyond a few metres (1 mm at 4 m < 1 px at 2400 px): their sum is the
  sheen. Near the camera they read only where large - broad waxy leaves (clover) hold 2-5 mm
  beads. Under an even sky a bead is bright through refraction + total reflection inside it,
  not its ~4 % surface reflection: a coat-only bead bump was invisible even at 0.4 m. Model
  them as effective-reflectance glossy beads (declared approximation), faded with camera
  distance (`vegetation.DEW_GRASS`, `DEW_BROAD`). The denoiser smooths isolated sub-pixel
  glints, so size and density must carry them.

## True displacement
`displaced_ground()` + `enable_true_displacement()`. Displacement Scale = the relief height,
Midlevel = -shift/scale; method BOTH (Displacement Only once finely diced); Subdivision SIMPLE
adaptive 1 px, last in the stack; `cycles.dicing_camera` = the render camera.

## Wood
- **Coated** `coated_wood()`: the coat trap — satin varnish is a *low* coat weight with *tight*
  coat roughness, not a strong rough coat. Spread the base roughness toward matte; don't lower
  IOR to compensate. Coat › Normal can stay smooth over bumped wood (to try).
- Cladding: pick the plank map by its real size and run `archviz.directional_uv(obj, tex_size_m, axis)` so the
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
- **Glass block** (pressed hollow unit): two pressed halves fused hot and sealed hollow (partial
  vacuum); the pattern is on the **inner** faces, outer faces smooth with slight pressing
  waviness; coated sides key to the mortar. Common units 190×190×80 mm (2.3 kg) and 240×240×80
  (4.1 kg) — from the weight, ~8 mm face glass, ~7 mm sides. Stack bond, 10 mm joints, perimeter
  bands ≥ 15 mm, panels ≤ ~15 m². Curved walls: the concave-side joint stays constant and the
  convex one opens, E = (L + g)(1 + s/r) − L; with g 10 / E 25 mm the inner radius is ≥ ~1.05 m
  (190 units), ≥ ~1.33 m (240). Model the relief as geometry (caustics.md › Designing a
  refractive relief), and leave a fraction of a millimetre of air between mortar and glass so the
  surfaces never coincide.
- **Liquid in glass**: Cycles has no nested-IOR priority, so model three surfaces — GLASS (1.52),
  INTERFACE below the waterline (1.52/1.333) and WATER_SURFACE (1.333) →
  `glassware.glass_of_water()`. Check normals per wall.

- **Glazing is not optically flat.** Float glass has roller waves (~0.1 mm peak-to-valley over
  ~0.3 m, ~1 mrad slope); the visible wobble of real windows is insulated-unit **pillowing**
  (panes bowed a few mm), strongest towards the frame. `lookdev.glass_distortion(mat, obj)`:
  bump of a sine roller wave + a dome over the pane. 0.25 mm of wave read as blinds; the dome
  carries the effect. A glass that "looks too reflective" is usually a dark room behind it -
  Fresnel is physical; distortion and something to reflect make it read.

## Water (pool)
- `interior.pool_water()`: Principled transmission 1, IOR 1.333, a shallow ripple bump, and
  **Volume Absorption** for the tint — depth does the colour work, so a pool reads green in the
  deep end and clear at the step without any gradient map.
- Geometry: `interior.water_surface(obj, …)` = top face only, diced, smooth (MNEE-ready; the
  volume still works over an opaque basin). Keep the waterline just under the coping.
- Rippled sunlit pool: Ocean modifier on a diced plane — no choppiness on short waves, and
  `wave_scale_min` >= 5 x grid spacing or the waves alias. Short wavelengths give the tight
  caustic networks; long swell does not.
- **Wind ripples are geometry, not a bump.** A noise bump faking short ripples reads artificial,
  and stretching it "because ripples look flat" doubles what perspective already does — never
  stretch. Dice the surface finer, sized from the ripples visible in the shot, and let the Ocean
  carry them (wave_scale_min >= 5 x cell, a little choppiness for crisp crests; check for
  downward faces = folds). Keep only a millimetre-scale micro bump in the shader. Size the swell
  by RMS slope, not just amplitude.
- **Wet surround (pool coping, splash zone)**: wet porous albedo falls non-linearly and
  saturates (Lekner & Dorf 1988; Jensen et al. 1999) -> wet colour = dry ** ~1.4 (Gamma node;
  1.8 turns a warm white beige-brown and reads as dirt), roughness ~0.1, plus a water film as
  Principled coat (IOR 1.33, rough ~0.03). When the edge is an arc, mask by the analytic
  distance d = R - |P.xy - C| (no mesh density); ragged splash band by noise-pushed d, Voronoi
  drops thinning with d, faint darker tide rings beyond, scum band at the waterline on vertical
  faces. Gate by height so canopies and far floors stay dry. Patchy, never a band (RULES 8c):
  drive the band width with a slow noise along the edge (down to negative = dry), and make dried
  marks blobs darker at their rim (coffee-ring) rather than contour lines.
- **Opaque pool look** (a stylisation, only when asked): opaque diffuse body under an exact IOR 1.333
  surface. Declare it; near-field sky reflection is Fresnel-limited (~6-12 % at 55-65 deg), so a
  reference that is near-white there is showing a pale floor through clear water.
- To try (manual-confirmed): **Volume Coefficients** node (absorption per channel in 1/m, from
  measured water absorption) + Volume Scatter phase **Fournier-Forand** (IOR 1.0-1.2,
  backscatter) for haze and light shafts; noise -> roughness for wind patches; Gabor texture for
  directional ripples.
- Steam: `interior.steam()` — Principled Volume, noise x height fade, anisotropy ~0.5.

## Randomness and anti-tiling (RULES 8d)
Repeated units and tiled maps need three kinds of variation. Cycles has no built-in stochastic
tiling (5.2 manual: no such texture node); build it from nodes.
- **Per-unit key.** *Object Info › Random*: one value per object instance (a hash of the name;
  collection instances each get their own). A Rhino block made of several objects (frame + glass)
  gets a *different* value per part — for one value per unit store it on the instance (custom
  property or *Store Named Attribute*, Instance domain) and read it with *Attribute › Instancer*.
  *Geometry › Random per Island* (Cycles only) varies the pieces of one joined mesh (bricks,
  planks); it repeats across instances of that mesh, so combine it with the instance key.
- **Per-unit variation** from that key: tint ±2–5 % value, roughness ±0.05, bump strength,
  a random UV *offset* (offsets keep normal maps valid; rotations do not).
- **Macro variation** — cheapest, biggest payoff: a 2–8 m world-space noise multiplied into
  albedo (±5–10 %) and added to roughness; hides a repeat without removing it.
- **Anti-tiling** where a repeat would still show: 2–3 lookups of the same map with different
  offsets mixed by a noise (cost ×2–3, robust), or hex tiling (3 lookups over a random hex grid
  with weight-sharpened blending, Mikkelsen 2022 — the method behind V-Ray's Stochastic
  Tiling); Voronoi-cell offsets are cheap but seam at cell edges unless blended there. Any UV
  rotation breaks a tangent-space normal map — drive relief from the height map through a Bump
  node instead. Free add-on to compare against: Patchwork (MIT).
- **Box projection** (Image Texture › Box, Blend 0.1–0.2) for Rhino geometry without UVs; again
  Bump from height, not the normal map.
- **LuxCore:** native Image › Randomized Tiling and 2D Mapping › Randomized UV; Object Info ›
  Random converts per instance (luxcore.md › Native LuxCore materials).
- Generated maps with no recognisable feature (cloudy tone + grain) cannot show a repeat; a
  scanned map with stains or cracks repeats visibly along every joint it is box-mapped onto.
