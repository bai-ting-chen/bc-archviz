# Concrete

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
- **Grunge comes in patches, not streaks** (RULES MAT_05; check the reference before adding any
  streak). Shape, all world-space Noise: a low-frequency patch field (with some Distortion)
  *plus* a centred high-frequency field at low amplitude, summed *before* a narrow threshold —
  that sum is what gives ragged, speckled borders instead of soft blobs. Inside a patch,
  mid-frequency mottle x speckle; keep clean gaps between patches. Use separate decorrelated
  fields (Mapping › Location offset) for floor stains so they don't echo the wall.
- Damp band at the foot of walls and columns: world Z thresholded, plus the same ragged noise so
  the top edge isn't a straight line.
- Concave-corner grime: AO node (**outside**, not Inside) x fine noise, into the grunge
  darkening. See [edge-wear.md](edge-wear.md) › Concave corners.
- **Multiplying several 0..1 masks washes them out fast.** Remap the inner masks into a narrow
  high range before multiplying, or the patches disappear.
- Fresh breaks under direct floods want their tint only *barely* above the surface; a visibly
  lighter paste reads as white paint flecks when lit head-on.

- Rough, weathered concrete from a dark scanned map: `materials.concrete.retone(mat, target, tex_id)` -
  desaturate, then scale the measured mean to the target albedo (the multiply keeps pits and
  pores). Runoff streaks and cracks: [edge-wear.md](edge-wear.md) > Runoff streaks, cracks.

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
  "Very faint" sits just above visibility: set the darkening with a control (RULES VAL_02), since a
  value that looks faint in the shader can vanish entirely in the render.


- **Monolithic but not identical.** A drum or infill of the "same" concrete often measures darker
  than the walls under the same light. Match the measured ratio by giving it its own albedo
  rather than relighting it.
