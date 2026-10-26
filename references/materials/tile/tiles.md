# Tiles

## 1. Overview
Glazed, layout-driven tile with real joints, a glaze surface, cracks and relief. Real tiles never
match a downloaded map, so layout, joint and face are separate real-unit knobs. Stone slabs, pavers
and large-format stone tiles are a different case (stone.md, plain-text neighbour).

**Use when:** glazed or layout-driven tile with real joints, cracks and relief. Stone slabs, pavers
or large stone tiles: stone.md (plain text).

## 2. Layers and node-editor diagram
Specific layers are described in §4. This file has no generic layers of its own: the layers below
are all specific to this material.

```
                                  TILES
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ SPECIFIC (§4)                                                             │
 │ 1 Mapping    → metre UVs on Rhino meshes (planar, cylinder, annulus)      │
 │ 2 Layout     → Tile ID, Tile UV, Edge (m), Joint, Cell, Tile Size         │
 │ 3 Surface    → glaze, grout, dust, tint, gloss, specks, metre height       │
 │ 4 Cracks     → damage masks (tile_damage, kind 1), piece lift and tilt    │
 │ 5 Relief     → displacement of damage only; profile and joints stay bump  │
 │ GENERIC      → none linked from this file                                 │
 └───────────────────────────────────────────────────────────────────────────┘
   order of evaluation                       node-editor output it drives
   mapping (1) ─► metre coordinate ─► layout (2)  ─► Tile ID, Tile UV, Edge
   layout (2) ─► surface (3) ─► material with glaze, grout and joint dust
   cracks (4) ─► damage mask inside the surface (3)
   damage (4) ─► relief (5) ─► displacement on the damaged pieces only
```

- **Knobs live in group nodes.** Every surface knob sits on the `TileLayout`, `TileFinish` and
  `TileDamage` group nodes, set with `set_param` or `toggle` (§3).
- **Which way joints run on returns and soffits** is a per-project decision (§4.1). Keep it a switch.

## 3. Code
Module names follow the code under `scripts/blender/materials/tile/`:
- Mapping: `tile_mapping.py` (`planar_uv` from `tile_uv_planar.py`; `cylinder_uv` and `annulus_uv`
  from `tile_uv_polar.py`).
- Layout: `tile_layout.py` (`add_layout`, from `layout_instance.py`).
- Surface: `tile_surface.py` is the one import point (`tile_material`, from `tile_build.py`; `use_bump`,
  `use_damage_displacement`, `use_displacement` from `tile_displacement.py`; `toggle` from
  `tile_finish.py`; `set_param` from `tile_settings.py`).
- Cracks: `tile_damage.py` (with `damage_build.py`, `damage_fields.py`, `damage_graph.py`,
  `damage_shading.py`).
- Controls, in `scripts/controls/tile/`: `tile_mapping_check.py`, `tile_layout_check.py`,
  `tile_surface_check.py`, `tile_damage_check.py`, and `tile_graph_check.py`. `tile_damage_rig.py` is
  the shared rig for the tile damage probes.

## 4. Instructions and parameters, per layer

### 4.1 Mapping (metre UVs)
- `materials.tile.tile_mapping.planar_uv`, `cylinder_uv` and `annulus_uv` write metre UVs on Rhino
  meshes. Cylinder UVs use arc length on curved walls. `annulus_uv(like=wall)` continues a wall's
  columns onto a ring.
- Which way joints run on returns and soffits is a per-project decision. Keep it a switch.

| Parameter | Value |
|---|---|
| Planar | `planar_uv` |
| Curved wall | `cylinder_uv` (arc length) |
| Ring | `annulus_uv(like=wall)` |
| Joint direction on returns and soffits | per-project switch |

### 4.2 Layout (Tile ID, Tile UV, joints)
- `materials.tile.tile_layout.add_layout` turns the metre coordinate into Tile ID, Tile UV, signed
  Edge (m), Joint, Cell and Tile Size.
- Set the bond, rotation, origin, corner radius and per-tile jitter on the layout.

| Parameter | Value |
|---|---|
| Bond | stack or running |
| Rotation, origin | set on the layout |
| Corner radius | set on the layout |
| Per-tile jitter | set on the layout |
| Outputs | Tile ID, Tile UV, Edge (m), Joint, Cell, Tile Size |

### 4.3 Surface (glaze, grout, finish)
- `materials.tile.tile_surface.tile_material(...)` is the material. It is either a glaze coat over any
  PBR face (albedo normalised, each tile its own patch of the map) or a procedural glaze.
- Rounded shoulder and recess are metre height. Grout and patchy joint dust sit at the joints.
- Per-tile tint, gloss and tilt, waviness and specks are all on the finish.

| Parameter | Value |
|---|---|
| Glaze source | PBR face (albedo normalised) or procedural |
| Edge profile | rounded shoulder and recess, metre height |
| Joints | grout and patchy joint dust |
| Per tile | tint, gloss, tilt, waviness, specks |

### 4.4 Cracks (`tile_damage`, kind 1)
- A noise-warped Voronoi *Distance to Edge* network in each tile's own frame, with a per-tile offset
  and cell size. It is drawn only around cells picked by their hash, and under a patch mask.
- Each tile gets 0–3 runs at any position and angle, with Y-junctions and varying width.
- **Do not hand-place chords.** One line across mid-tile reads as stamped.
- **Cell length sets the crack.** Cells longer than the tile's short side give long, gentle curves;
  cells about the tile width give crazing-like closed cells.
- **Picked cells are rigid pieces** (own lift and tilt), so the reflection breaks across the crack.
- **A hairline is sub-pixel at room distance.** What reads is the patchy dirt band: dirt and limescale
  wick into the crack and the porous body (`Crack Dirt`, `Dirt Width`).
- **Tune on a flat pattern sheet first:** render the damage masks (emission, 1 sample) on a flat wall
  of the real tile size with the joints drawn, several parameter sets side by side. Each sheet takes
  seconds. Then confirm in the final view (RULES MAT_03). Use the scene's own depth and width values
  on the sheet: defaults differ, and a sheet without joints makes edge damage look like islands.
- **Chips and edge flakes** are in development and are not yet a method.

| Parameter | Value |
|---|---|
| Runs per tile | 0–3 |
| Cell length | longer than the tile's short side for long curves; about the tile width for crazing |
| Dirt band | `Crack Dirt`, `Dirt Width` |
| Tuning sheet | flat wall, real tile size, joints drawn, emission, 1 sample |

### 4.5 Relief (displacement of damage only)
- In the main frame, displace only the damage (`materials.tile.tile_surface.use_damage_displacement`).
  Piece steps and cuts become geometry; profile and joints stay bump. Mesh edges move only where
  damage reaches them.
- **Do not displace the full tile height.** It pulls the wall's boundary edges inward along the joint
  recess and opens bright slits to the sky at floor and ceiling junctions.
- A macro view can displace everything, but only on the objects in frame, with a high offscreen dicing
  scale. Dicing every wall from a macro camera can exhaust VRAM (RULES SAF_02).
- The mode and its objects are stored in the material, so a structural `set_param` re-applies them.
  `use_bump` undoes the shader side but leaves the subdivision modifiers.
- `piece_tilt` is in radians.

| Parameter | Value |
|---|---|
| Displacement scope | damage only (main frame); everything only for a macro view on objects in frame |
| Dicing scale (macro) | high, offscreen |
| `piece_tilt` | radians |

No generic layers are linked from this file, so there is no generic table here.

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Bright slits to the sky at floor and ceiling junctions | full tile height displaced; boundary edges pulled inward | displace only the damage (§4.5) |
| Cracks read as stamped | hand-placed chord across mid-tile | per-tile Voronoi network with picked cells (§4.4) |
| Edge damage reads as islands | flat sheet drawn without joints | draw the joints on the tuning sheet (§4.4) |
| Cracks invisible at room distance | hairline is sub-pixel | the dirt band: `Crack Dirt`, `Dirt Width` (§4.4) |
| Reflection runs unbroken across a crack | cells not rigid | picked cells as rigid pieces with own lift and tilt (§4.4) |
| VRAM exhausted from a macro camera | every wall diced at a high scale | displace only the objects in frame (§4.5) |

Generic problems that show up in any material are in troubleshooting.md.
