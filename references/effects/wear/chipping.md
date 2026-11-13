# Chipping

## 1. Overview
Removed material: edge chips and fresh breaks, and flaked coating that exposes an under-material.
**Use when:** material is missing; dark deposits belong to dirt.md or water-marks.md.

## 2. Layers and node-editor diagram
Geometry chips alter the silhouette; flaked coating selects coat or substrate shaders.
Locations are inputs from [wear-locations.md](wear-locations.md), including edges and feet.
Shared source composition, scan mapping and stack order live in `references/effects/wear/wear.md`.
A fresh break uses the clean underlying material, before accumulated dirt.

## 3. Code
- `scripts/blender/effects/wear/chipping.py`: `dice`, `edge_wear_group`, `add_edge_wear`, `set_input`,
  `chipping_field`, `flaked_paint_masks`. `concrete_shading.py`: `weathered_concrete`, fresh-break shader.
- Coating loss: `WearLayer` key `chipping`, `wear_factor`, `apply_surface_wear` in `wear.py`;
  supply the actual `under_shader`. Deprecated `worn-through` remains an accepted alias.
- Controls: `scripts/controls/effects/edge_wear_lab.py`, `surface_wear_lab.py`, both graph checks.

## 4. Instructions and parameters
### 4.1 Edge chips and fresh breaks
Dice coarse meshes first, then apply the chip modifier. Size chip reach from the shot, band to
contain that reach, subdivision so a chip spans several faces. Limit work to visible outside
edges; leave floors/slabs coarse. At room scale try half the close-up size and a lower chipped
share. Seed repeated objects individually. An already dense mesh can use the same chip field
as material displacement on rest position; adaptive displacement can exhaust small-GPU VRAM.
Fresh break: sample clean base before grime, lighten/roughen it and add a fine fracture bump;
sampling finished weathered colour makes a dark spot. Wood uses real bevels and grain-wise breaks
in its material-specific group (`references/materials/wood/wood.md`).

| Parameter | Existing starting point (RULES MAT_03) |
|---|---|
| `dice` size / chip band | 0.05 m / 0.08 m |
| Chip reach / depth | 0.045 m / 0.018 m |
| Chipped share | 0.55 close up; lower at room scale |
| Fresh-break albedo / roughness | clean base ×1.15 / 0.95 |
| Switches | `chips=False`; fresh-break `chips_amount=0` |

### 4.2 Flaked coating patches
Hybrid is selected. Hard procedural region AND thresholded bare-substrate interior selects
actual concrete/metal beneath the coat, with no grey half-mix, dirt shader or wet-looking tint.
Only antialiasing mixes pixels at edges. Amount changes coverage through the scan cutoff.
Displacement distributions overlap paint and substrate in these assets; registered BaseColor
instead verifies opposite Roughness polarities. Preserve those verified signals.
Several scan-shaped flakes should fit a region; override `MaskSource.size_m` when the shot needs
it and record the world sizes, leaving asset metadata untouched (RULES MAT_03). A paler test
coat helps inspection; its colour is scene code, not a skill default.
The procedural alternative thresholds noise smoothly. Raw/procedural/stamps preserve the
existing thin darker transition border; binary hybrid bypasses that border shader.

| Parameter | Existing starting point |
|---|---|
| Key / default | `chipping` / `hybrid` |
| Interior scans | `ub1meemn`: 1 m; `tmulfghdy`: 2 m; 4K `_Roughness`, checked against `_BaseColor` |
| `ub1meemn` levels | black/white 0.65/0.72 then invert: smoother green substrate below white paint |
| `tmulfghdy` levels | black/white 0.80/0.85, no inversion: rough pale substrate below green paint |
| Region threshold / pre-binary edge width | 0.30 / 0.02 normalized field units; final edge binary |
| Interior cutoff | `flake_threshold` 0.5; actual cut = threshold + 0.5 − amount |
| `scale_m` / `amount` | 0.25 m / 0.50; shot-sized starting points |
| Procedural shape | noise detail 3, smooth remap 0.54–0.57 |
| Raw mask | `uh4tbdhc`: 0.7 m, 4K `_Mask`; striped appearance in comparison |
| Under-material | actual shader output socket required |

Explicit `stamps` keeps the chip-decal alternative, never a hybrid/default dependency:
`ukgodfdcw` (2 m), `ujzjdgmo`, `ui2ncdjfw` (1 m), `_Opacity` atlas, full rotation.
Neighbour support is the shared stamp method in water-marks.md §4.3.

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Far beam looks chewed | close-up chip size | smaller reach/depth and share (§4.1) |
| Repeated chips / dark breaks | same seed / weathered base | seed per object; clean fresh-break source (§4.1) |
| Coat reads as wet stain | transparent or darkened bare selection | binary coat/substrate shader choice (§4.2) |
| No exposed substrate | only colour was changed | supply actual under-material (§4.2) |

Generic problems: troubleshooting.md.
