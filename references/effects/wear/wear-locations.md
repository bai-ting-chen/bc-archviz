# Wear locations

## 1. Overview
Location fields for wear: edge distances, rounding, feet, drip origins, face orientation and patch extent.

## 2. Layers and node-editor diagram
These fields feed the location input of wear mechanisms; they are not a separate wear stack.
Measure on the clean carrier, store attributes, then modify geometry and shade (RULES MAT_08).
The family assembly and source method live in `references/effects/wear/wear.md`.

## 3. Code
- `scripts/blender/effects/wear/wear_locations.py`: `edge_field`, `WearExtent`, `location_extent`,
  `patch_extent`, `face_z`, `set_round_radius`, `round_shader`, `round_geometry`, `switch_rounding`.
- `leak_field.py`: `leak_field_group`, `add_leak_field`; first modifier on the clean carrier.
- `edge_profile.py`: edge-gradient projection, junction join and cross-face orientation context;
  `dirt.corner_dirt_masks` supplies the AO input; `mask_views.mask_material` shows diagnostic fields.
- LuxCore contact field: `scripts/blender/renderer/luxcore/dust_shader.py`, `bake_dust`.
- Controls: `scripts/controls/effects/edge_wear_graph_check.py`, `surface_wear_hybrid_check.py`.

## 4. Instructions and parameters
### 4.1 Edge distance and rounding
- Outside: convex GN Edge Angle over threshold -> curve proximity -> `edge_dist` metres,
  plus `rest_pos`, junction distance and validity. Exact clean distance outperformed Pointiness,
  AO Inside and Bevel-normal detection in the control.
- Without the modifier, `edge_dist` reads zero. Add a large offset where `length(rest_pos)` is
  below epsilon before band remapping, so an untagged object is not uniformly dirty.
- Inside contacts: AO with Inside off and Only Local off sees separate floor/wall objects.
  Cap triple-face contacts so they are no darker than two-face joints. LuxCore has no AO texture:
  bake per object at 4096 px; reuse the bake for repeated renders.
- Slight rounding catches light. Set one scene radius; shader Bevel is the normal route. Use real
  bevel geometry for close silhouettes, chips and MNEE caustic casters/receivers (shader Bevel invalid).
- A faint edge on a huge mesh can use a Bevel-normal mask instead of dicing; see
  `references/materials/concrete/concrete.md` for that cheaper material-specific alternative.

| Parameter | Starting point |
|---|---|
| Scene rounding radius | 0.0025 m; typically 2–3 mm, size from shot (RULES MAT_03) |
| Geometry bevel | two segments, 30 degree threshold |
| Corner AO reach / mask cap | 0.30 m / 0.50 |

### 4.2 Feet, orientation and zero-reaching patches
- Feet use height above `floor_z_m`, faded across the chosen foot range on vertical faces.
  For scuffs densest in the lowest 0.3 m, raise the full-strength height then thin upward.
- Optional clean `edge_distance` adds grime under soffit edges; absent socket creates no edge term.
- Dried marks accept only world Normal Z > -0.001, even with extent disabled. Vertical weighting
  fades with absolute Normal Z 0.1–0.55; up-facing weighting rises over Z 0.35–0.85. Raw dried
  scans blend vertical/up zones over Z 0.25–0.75. Use world normals, not projected coordinates.
- A supplied `drip_top_m` defines an actual vertical origin; below it, `drip_length_m` fades downward.
  Multiply location by slow patch noise with real zero regions. Some areas must be unmarked;
  avoid a uniform band or contour ring (RULES MAT_05).

| `WearExtent` parameter | Starting point (RULES MAT_03) |
|---|---|
| `enabled`, `floor_z_m` | True, 0 m |
| `foot_full_m`, `foot_height_m` | 0.02 m, 0.7 m |
| `soffit_edge_m` | 0.18 m |
| `patch_scale_m`, `patch_black`, `patch_white` | 2.3 m, 0.46, 0.66 |
| `drip_top_m`, `drip_length_m` | None, 1 m; set from real origin |

### 4.3 Under-edge raycast origin
Raycast world-up from just inside the wall to its own first face; store `leak_d` and `leak_ok`.
A separate sill/eave is invisible to this self-mesh field. Closed walls hit their own top face.
Open/single-plane walls use `Top Fallback`: highest point, one top per object. Split stepped
sheets by height or give thickness when a sill must be found. Unapplied rotation/uniform scale
is supported; distances are world metres. Run this before chips, whose seams spoil ray hits.

| Parameter | Starting point |
|---|---|
| Ray inset / reach | 0.02 m / 6 m |
| `Top Fallback` | on |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Entire floor dirty | absent GN attribute reads zero | `rest_pos` validity gate (§4.1) |
| No contact dirt / triple-corner blob | local-only AO / uncapped contact | cross-object AO and cap (§4.1) |
| Constant band / ring | location never reaches zero | slow patch field (§4.2) |
| Dried marks on soffits | bypassed orientation | retain underside gate (§4.2) |
| Light triangles under arris | raycast after chips | leak field first (§4.3) |
| No sill streak origin | single-plane wall or separate sill | thickness / same mesh; fallback for simple top (§4.3) |

Generic problems: troubleshooting.md.
