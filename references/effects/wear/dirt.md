# Dirt

## 1. Overview
Dust and build-up, and bordered grunge marks.
**Use when:** deposits are dry dirt; water-borne streaks and drying deposits belong to water-marks.md.

## 2. Layers and node-editor diagram
Dust is a location field applied directly to the surface: no procedural region border and no scan.
Grunge uses a bordered pattern. Shared source composition and stacking are in
`references/effects/wear/wear.md`; locations are in [wear-locations.md](wear-locations.md).
Keep dust beneath the darker edge line. Clean chips exclude accumulated dirt.

## 3. Code
- `scripts/blender/effects/wear/dirt.py`: `edge_dirt_masks`, `corner_dirt_masks`, `dust_surface`,
  `add_corner_dirt`, `grunge_field`; `grunge` preserves the legacy calibrated multiplier API.
- `edge_profile.py` shares edge-distance falloff/noise with `edge_line.py` without rebuilding it.
- Face grunge: `WearLayer`, key `grunge`, through `wear_factor` / `apply_surface_wear` in `wear.py`.
- Controls: `scripts/controls/effects/edge_dirt_lab.py`, `surface_wear_lab.py`.

## 4. Instructions and parameters
### 4.1 Dust and build-up
Use the location input for edge dust, settled dust on top faces and build-up at feet. Existing
edge/corner helpers preserve their orientation weighting; choose top/foot fields explicitly for
those locations. Dust is lighter than edge line, several times wider and smoothly fading onto
faces. Tonal order: surface > dust > line. Darken/desaturate the original albedo, retaining its
texture; a fixed tint can become a pale highlight or black stroke. Inside corners are stronger
low down and fainter at ceilings (RULES MAT_06). Judge width in the full frame.

| Parameter | Starting point (RULES MAT_03) |
|---|---|
| Edge dust width / amount | 0.150 m / 0.40 |
| Relative dust albedo / saturation | ×0.825 / 0.90 retained saturation |
| Pattern source | location only, no border or scan |

### 4.2 Grunge
Hybrid is selected; the procedural alternative reads as cloudy smoke. Use the shared hybrid
method in `references/effects/wear/wear.md`. White in both Mask scans is grime, black is clean;
their Roughness maps place brighter values on those same marks. No inversion or compensating
per-scan clip. Random interior rotations remove scan direction; for run-down grime, stretch the
procedural region along gravity. The procedural option combines fine remapped noise with slow
zero-reaching noise; legacy `grunge` retains its separate calibrated multiplier contract.
Dust has no border; grunge marks have a soft but readable one (edge width 0.20). Keep that
contrast: do not feather grunge into a field, and do not give dust an outline.

| Parameter | Starting point |
|---|---|
| Key / default | `grunge` / `hybrid` |
| Interior scans | `uh4tfagc`, `uh4uabdc`: 0.7 m each, 4K `_Mask` |
| Scan levels | black/white 0/1, gamma 1, no inversion |
| Region threshold / edge width | 0.24 / 0.20 normalized field units |
| `scale_m` / `amount` | 0.25 m / 0.45; shot-sized starting points (RULES MAT_03) |
| Procedural field | detail 3; fine range 0.35–0.65 × noise at 4× size, range 0.43–0.57 |
| Colour / roughness at factor 1 | ×0.52 / ×1.35 |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Dust becomes a pencil line | judged only close up | judge width in full frame (§4.1) |
| Dust loses base texture | fixed-colour replacement | relative albedo composition (§4.1) |
| Dirt reads as smoke | isotropic region on directional deposits | orient region, or use water-marks.md (§4.2) |

Generic problems: troubleshooting.md.
