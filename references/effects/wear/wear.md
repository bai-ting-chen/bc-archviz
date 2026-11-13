# Wear family

## 1. Overview
Wear by mechanism: dirt, water-borne deposits, chipping, scratches, cracks and edge lines.

## 2. Layers and node-editor diagram
Every wear layer = **where × pattern × effect**: a location field chooses where; a procedural,
raw-scan or hybrid pattern chooses the marks; colour, roughness, normal or an under-material
implements their effect. Location is an input, never a file boundary.

| Topic | Reference |
|---|---|
| Edge distance, rounding, feet, drip origins, orientation, patch extent | [wear-locations.md](wear-locations.md) |
| Dust/build-up and grunge | [dirt.md](dirt.md) |
| Run-off and dried marks | [water-marks.md](water-marks.md) |
| Geometry chips, fresh breaks and flaked coating | [chipping.md](chipping.md) |
| Crossing strokes | [scratches.md](scratches.md) |
| Edge and opening cracks | [cracks.md](cracks.md) |
| Narrow connected edge line | [edge-line.md](edge-line.md) |

Hybrid has one definition: **wear = procedural region × bitmap interior**. The region thresholds
procedural pattern × location, feathered by the layer's edge width. Only the interior sees scans.
Keep their full contrast; do not replace it with near-one modulation. Chipping thresholds region
and interior to binary coat/bare selection. Scratches retain their held legacy modulation.

```
 +-- WEAR ASSEMBLY — LAYER DIAGRAM ----------------------------------------+
 | clean carrier -> location fields -> geometry chips/rounding              |
 | base colour/normal -> dust -> edge line -> grunge -> dried deposits       |
 | run-off and crack masks -> colour / shallow groove                       |
 | flaked coat + under-material -> shader selection -> Material Surface     |
 +-------------------------------------------------------------------------+
```
Capture fields before modifiers move the mesh (RULES MAT_08). Leak origin runs before chips;
base variation precedes shading wear. Supply `apply_surface_wear` layers in order, chipping last.
Keep geometry switches and shading amounts independent (RULES MAT_07).

| Layer | Default source | Reason / status |
|---|---|---|
| Grunge | `hybrid` | selected over cloudy procedural grunge |
| Dried marks | `hybrid` | selected; scanned deposits inside irregular regions |
| Chipping (formerly `worn-through`) | `hybrid` | selected; scan-shaped binary paint loss |
| Scratches | `hybrid`, legacy | undecided; judge in a close scene; unchanged placeholder |
| Run-off | procedural | the 0.25 m leakage scan tiled visibly |
| Dust, edge line, geometry chips, cracks | procedural | existing location/geometry builders; no scan source switch |

## 3. Code
- `scripts/blender/effects/wear/wear.py`: `WearLayer`, `wear_factor`, `apply_surface_wear`.
  Pass `materials.shared.node_graph.NodeGraph`, a Principled shader and layer/settings mapping; chipping needs
  `under_shader`. `effects.wear` also exports the geometry and shading assembly helpers.
- `source=None` uses the table; explicit sources: `procedural`, raw `mask`, `hybrid`, or `stamps`
  (non-default deposits/chipping). `enabled=False` needs no assets; `amount=0` disables the effect.
  Continuous sources scale strength; binary hybrid chipping uses amount for coverage, not opacity.
  `worn-through` remains an accepted layer alias; new code and AOVs use `chipping`.
- `hybrid_sources.py`: `HybridSource`, `hybrid_field`; shared composer for active hybrids. `scan_sampling.py`:
  `stochastic_mask`, reusing `effects.variation_tiling.randomized_vectors`. `image_masks.py` owns
  `MaskSource`, `asset_mask`, `asset_maps`, `scan_size_m`, `image_mask`, `mask_field`.
- `default_sources.py`: defaults and one missing-id/Fab-search line per process; a missing default scan
  falls back to procedural. Acquire via pipeline.md Assets; builders never download.
- `decal_stamps.py` / `decal_atlas.py`: explicit neighbour-aware scatter and atlas preparation, separate from hybrid.
- Controls in `scripts/controls/effects/`: `edge_wear_graph_check.py`, `surface_wear_graph_check.py`,
  `surface_wear_lab.py`, `surface_wear_hybrid_check.py`; reuse the shared rigs and AOV reader.
  `wear_graph_check.py` snapshots every field/shader source and switch for graph equivalence.

## 4. Instructions and parameters
### 4.1 Scan loading and stochastic interior
Keep assets in `<project>/library/local/<id>/`; read `meta.json` scan width/height and units
(m/cm/mm) into metres. Use 4K Non-Color grayscale RGB. Mapping size starts at the listed scan
size on each axis. Levels, gamma and optional inversion precede stochastic blending. Raw masks
allow rotation, offset, world projection or named UVs. For UV mapping, author `box_uv` or
`directional_uv` at that size; do not scale twice. World projection uses the dominant face plane.
The sampler blends three randomly offset/rotated, slightly scale-jittered lookups with slow noise;
optionally select between scans. Check polarity against registered BaseColor when present, or
raw-mask controls otherwise. Keep clean/paint background black and marks a minority: interior
mean and strong-mark area below one half. Filtered nonzero pixels do not measure coverage.

| Parameter | Starting point (RULES MAT_03) |
|---|---|
| `HybridSource.seed` / `blend_scale_m` / `scale_jitter` | 17 / 1.7 m / 0.12 (0.88–1.12 scale) |
| Interior post-tiling remap | black/white 0/1, gamma/gain 1/1; cap at 1 |
| `region_threshold`, `edge_width` | per-layer normalized field units; visible width depends on field gradient and scale |

### 4.2 Strength matching and inspection
At one shared amount per layer/source, measure dry interior pixels: layer-factor AOV mean, SD
and coverage, plus beauty change relative to repeated off/off noise. Never infer image strength
from a shader parameter. Fit foreground contrast and region coverage together without clipping
background into wear; aim beauty change/noise within 15% of procedural. Preserve interior detail.
Show native crops, raw scan beside same-crop scan/interior, and unlit region/interior/rim masks.
`wear_factor(..., components=dict)` exposes these; AOVs are `var_surface-<layer>` and suffixes
`-region`, `-interior`, `-rim`, `-scan`, `-driver`. Composite previews from one render (validation.md).

### Generic layers
| Layer | Reference | Note |
|---|---|---|
| Base variation | variation-per-unit-shading.md, variation-macro-tone.md | vary base before wear |
| Active wet film | wet-surfaces.md | separate from dry deposits |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Hybrid outline follows scan | bitmap in region driver | isolate procedural region (§2) |
| Flat hybrid interior | near-one modulation or erased contrast | preserve full range (§4.1) |
| Apparent reversed polarity | foreground/background confused | verify source and preserve sparse marks (§4.1) |
| Raw scan visibly tiles | mapping or scan too small for area | retain physical size; compare stochastic hybrid (§4.1) |
| Camouflage / unequal strength | excess coverage or guessed parameter | measure AOV and beauty (§4.2) |
| Default scan missing | absent 4K map | procedural fallback and named acquisition log (§3) |

Generic problems: troubleshooting.md.
