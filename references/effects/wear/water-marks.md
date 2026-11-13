# Water marks

## 1. Overview
Water-borne deposits: run-off streaks and dried marks or stains.
**Use when:** water has left deposits; active films belong to wet-surfaces.md, dry grime to dirt.md.

## 2. Layers and node-editor diagram
Run-off hangs from a drip origin; dried marks have a body and darker drying rim. They can coexist.
Shared sources and strength inspection: `references/effects/wear/wear.md`.
Location/orientation and raycast setup: [wear-locations.md](wear-locations.md).

## 3. Code
- `scripts/blender/effects/wear/water_marks.py`: `LEAK`, `add_runoff`, `deposit_distance`,
  `deposit_profile`, `irregular_deposits`, `dried_marks_field`.
- `leak_field.py`: `add_leak_field`; dried marks use `WearLayer` key `dried-marks` in `wear.py`.
- `stamps.py`: non-default `deposit_stamps`; `atlas.py`: `StampAtlas`, `build_stamp_atlas`.
- Controls: `scripts/controls/effects/weathering_lab.py`, `surface_wear_lab.py`.

## 4. Instructions and parameters
### 4.1 Run-off streaks
Gravity-shaped streaks stretch down, vary their lengths and cluster patchily along the wall.
Isotropic noise reads as smoke. Start on the flat-wall control, then install the same graph;
check joints introduce no step. Sunlit walls can need full strength. Origin fields are owned by
wear-locations.md §4.3; do not derive them from chipped geometry.

| Parameter | Starting point (RULES MAT_03) |
|---|---|
| Default source | procedural; the 0.25 m leakage mask visibly tiled |
| Stretch across / down | approximately ×14 / ×0.6 |
| Length | approximately 1–3 m, varied per streak |
| Switch | `add_runoff(..., amount=0)` disables |

### 4.2 Dried marks and stains
Hybrid is selected. Both scans have bright deposits: the Roughness image has a ~0.34 background
to remove, while the Mask needs no compensation. Neither has BaseColor; compare their data maps
and raw-mask control instead of inferring polarity from absent albedo. Both scans form one
hybrid interior pool. Raw masks retain separate vertical/up-facing scans. Orientation lives in
wear-locations.md §4.2 and remains active with the extent switch off.

The hybrid region uses continuous warped blob distance **before** body/rim profiling. Thresholding
a flattened body against a smooth height fade creates gradient bands. A darker rim follows the
irregular region edge. Procedural fallback has domain-warped, varied-size, sometimes merged blobs
and uneven rims, with no identical circle primitive. Roughness changes represent dry deposits.

| Parameter | Starting point |
|---|---|
| Key / default | `dried-marks` / `hybrid` |
| Interior pool | `uh4tdhic`: 0.7 m, 4K `_Mask`; `tjwtbgvc`: 1 m, 4K `_Roughness` |
| Scan levels | Mask 0/1, Roughness 0.34/1; gamma 1, no inversion |
| Raw-mask assignment | Roughness vertical, Mask up-facing |
| Region threshold / edge width | 0.07 / 0.08 normalized field units |
| Drying rim | `4 × region × (1-region)`; up to 25% extra colour darkening weighted by wear |
| `scale_m` / `amount` | 0.25 m / 0.85; readable starting points, inspect shot (RULES MAT_03) |
| Colour / roughness at factor 1 | ×0.35 / ×1.45 |

### 4.3 Explicit stamp alternative
`stamps` is separate from hybrid. Use top-anchored leaks and small wall-foot stains, plus floor
oil/mud. Density is occupied-cell probability; do not multiply by another patch sample. The
common point extent supplies patchiness. `profile='deposit'` adds darker rim and source-tone body.
Full-tile `wbhtbcov`, `wbhtahpv`, `wbhtbcev` need `cutout_indices` for irregular pieces; preserve
`sdfplbi`/`sdjliyi` oil/mud silhouettes. Drip alternatives: `tk3jefoc`, `tk3jfbec`, `tdiledyc`,
`skphbg3c`, `tcumebvc`, `skivejqc`, sized from metadata, with small vertical tilt.
Scatter samples 3×3 neighbouring cells. Maximum scaled half-diagonal + centre jitter + top-anchor
shift must fit one cell width, allowing marks to cross their own cell border without clipping.

| Parameter | Starting point |
|---|---|
| `StampAtlas.cell_m` / `density` | 3.2 m / 0.8; fit actual stamp support |
| Scale / tilt / centre jitter | 0.7–1.1 / ±7 degrees vertical / 0.2 cells |
| Physical stamp size | width × height from metadata; keep aspect ratio |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Run-off reads as smoke | isotropic noise | gravity stretch and varied lengths (§4.1) |
| Gradient bands in region/rim | profiled blob plateau | continuous pre-profile distance (§4.2) |
| Deposits invisible | weak contrast or sparse/rejected stamp placement | inspect components; explicit density/top anchoring (§4.2–4.3) |
| Stamp squares / clipping | full-tile opacity / insufficient neighbour support | cutouts and support bound (§4.3) |

Generic problems: troubleshooting.md.
