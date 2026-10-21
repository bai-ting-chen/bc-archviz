# Tiles

### Tiles: layout, mapping, surface, cracks
Real tiles never match a downloaded map, so layout, joint and face are separate real-unit knobs:
- `materials.tile_mapping.planar_uv / cylinder_uv / annulus_uv` write metre UVs on Rhino meshes (arc length on
  curved walls; `annulus_uv(like=wall)` continues a wall's columns onto a ring). Which way joints
  run on returns and soffits is a per-project decision — keep it a switch.
- `materials.tile_layout.add_layout` turns the metre coordinate into Tile ID, Tile UV, signed Edge (m), Joint,
  Cell, Tile Size (stack/running bond, rotation, origin, corner radius, per-tile jitter).
- `materials.tile_surface.tile_material(...)` is the material: glaze coat over any PBR face (albedo
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
- **Relief:** in the main frame displace only the damage (`materials.tile_surface.use_damage_displacement`;
  piece steps and cuts become geometry, profile and joints stay bump, so mesh edges move only
  where damage reaches them). Displacing the full tile height pulls the wall's boundary edges
  inward along the joint recess and opens bright slits to the sky at floor and ceiling junctions.
  A macro view can displace everything, but only on the objects in frame with a high offscreen
  dicing scale (dicing every wall from a macro camera can exhaust VRAM, RULES SAF_02). The mode and its
  objects are stored in the material, so a structural `set_param` re-applies them; `use_bump`
  undoes the shader side but leaves the subdivision modifiers. `piece_tilt` is in radians.
- **Tune on a flat pattern sheet first:** render the damage masks (emission, 1 sample) on a flat
  wall of the real tile size with the joints drawn, several parameter sets side by side — seconds
  per sheet. Then confirm in the final view (RULES MAT_03). Use the scene's own depth/width values on the
  sheet: defaults differ, and a sheet without joints makes edge damage look like islands.
