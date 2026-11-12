# Surface wear

## 1. Overview
Wear on surface faces: grunge, scratches, dried deposits and coating worn through to an
under-material.

**Use when:** wear occupies a face. Edge-shaped damage belongs to edge-wear.md; active water films
belong to wet-surfaces.md.

## 2. Layers and node-editor diagram
Hybrid has one definition for the active layers: **wear = procedural region × bitmap interior**.
The region thresholds the layer's procedural field multiplied by its location extent, using a
layer-specific edge width. The interior retains the scan's black-to-white pattern through the
shared stochastic tiler, with an interior remap calibrated after region masking. Worn-through
thresholds the flake interior and region into a binary cutout; continuous layers retain the product.
Dried marks receive additional mild colour darkening at the drying edge; their wear factor still
follows the same product. Scratches keep their legacy hybrid (scan modulation of procedural strokes), not yet judged.

| Layer | Current source choice | Status |
|---|---|---|
| Grunge | Hybrid | selected; compare the revised region/interior composition |
| Dried marks | Hybrid | selected; scanned deposits inside an irregular procedural outline |
| Worn-through | Hybrid | selected; binary scan-shaped paint loss inside a procedural region |
| Scratches | Hybrid (legacy modulation) | not yet judged; judge in a close scene |
| Run-off, owned by edge-wear.md | Procedural | the 0.25 m leakage mask tiled visibly |

```
 +-- SURFACE WEAR — LAYER DIAGRAM -----------------------------------------+
 | §4.1 Grunge       -> colour x, roughness x; soft region edge             |
 | §4.2 Scratches    -> roughness x, slight groove normal; held             |
 | §4.3 Dried marks  -> colour x, roughness x; darker drying edge            |
 | §4.4 Worn-through -> under-material mix; hard region edge                 |
 | GENERIC: macro tone; extent/strength -> variation-surface-marks.md       |
 +------------------------------------------------------------------------+
 location extent × procedural field -> threshold/feather -> region ----+
 scans -> 3 rotated/offset/scale-jittered lookups -> interior ------------×
                                                                      |
                       product -> amount/switch -> AOV -> shader inputs
 region × (1-region) -> drying rim -> mild extra colour darkening
 coating + under-material -> worn-through shader mix -> Material Surface
 clean mesh -> geometry fields -> geometry modifiers -> shading
```
- Supply layers in evaluation order, with worn-through last (RULES MAT_07).
- Location owns coverage (RULES MAT_05): wall/column feet, supplied soffit-edge grime,
  vertical/up-facing deposits and zero-reaching slow patches. Dried marks always exclude undersides.
- `stamps` retains the separate decal approach as a non-default source for deposits and coating
  loss. Hybrid never calls it and needs no atlas. Select it explicitly when testing decals.
- Worn-through changes shading. Deep chips need geometry and edge-wear.md (RULES MAT_08).

## 3. Code
- `scripts/blender/effects/surface_wear.py`: `WearLayer`, `wear_factor`, `apply_surface_wear`.
  Pass a mapping of layer names to settings and an existing Principled shader. `under_shader`
  is required for worn-through. The builder returns the Surface socket; `g` is
  `materials.shared.nodes.G`. Existing input links remain in the composition.
- `source=None` uses the layer default; explicit sources are `procedural`, raw `mask`, `hybrid`,
  or non-default `stamps` for dried marks/worn-through. `enabled=False` and `amount=0` give zero.
  Continuous sources scale their factor with amount. Binary worn-through hybrid uses amount for
  chip coverage, never transparency. Factor AOV: `var_surface-<layer>`.
- `scripts/blender/effects/surface_wear_hybrid.py`: `HybridSource`, `hybrid_field`.
  Every active hybrid uses this one composition function. Optional `masks` overrides the interior
  pool; `region_threshold` and `edge_width` override the layer's normalized-field settings.
  `interior_black`, `interior_white`, `interior_gamma` and `interior_gain` remap the stochastic
  scan before multiplication; the remapped interior is capped at 1. `flake_threshold` controls
  the binary worn-through cut. Match the measured effect at a fixed layer amount.
  `wear_factor(..., components=output_dict)` exposes region, interior, rim and full-strength factor.
  Component AOVs are `var_surface-<layer>-region`, `-interior`, `-rim`, `-scan` and `-driver`.
  These are unlit fields; scan and driver permit calibration without baking new bitmap files.
- `scripts/blender/effects/surface_wear_tiling.py`: `stochastic_mask`. The sampler reuses
  `randomized_vectors` in `scripts/blender/effects/variation_tiling.py` and the canonical image
  loader. `seed`, `blend_scale_m` and `scale_jitter` live in `HybridSource`. The former import of
  `stochastic_mask` from the hybrid module remains an alias to this owner.
- `scripts/blender/effects/surface_wear_masks.py`: `MaskSource`, `asset_mask`, `asset_maps`,
  `scan_size_m`, `image_mask`, `mask_field` and metre-space dominant-face projection.
  All grayscale sources share this resolver and loader. Imports of `MaskSource` and `image_mask`
  through `effects.surface_wear` remain valid.
- `scripts/blender/effects/surface_wear_defaults.py` owns source choices and raw default masks.
  A missing default scan falls back to procedural and logs one line per missing id per process,
  with its Fab search. Acquire it through pipeline.md Assets; the effect does not download.
- `scripts/blender/effects/surface_wear_fields.py` owns procedural shapes;
  `surface_wear_deposits.py` owns irregular bodies/rims. Legacy `grunge` remains importable
  through `effects.surface_wear` and `effects.variation_surface_marks` with its original behaviour.
- `scripts/blender/effects/surface_wear_extent.py`: `WearExtent`, `location_extent`.
  Supply floor datum, foot fade, slow patch settings and the clean-mesh `edge_distance` socket.
  Without that socket no soffit-edge contribution is created. Disabled extent still excludes
  down-facing dried marks.
- `scripts/blender/effects/surface_wear_chips.py`: `flaked_paint_masks`, the per-scan bare-substrate
  interior pool verified against registered BaseColor. There is no scan-biased outer outline.
- `scripts/blender/effects/surface_wear_stamps.py`: `StampSource`, `stamps_field`, `scatter_stamps`,
  `deposit_stamps`. Only the explicit stamps source owns the old decal outline/placement approach.
  Supply `WearLayer.stamps`, with vertical/floor and optional wall/worn atlases.
  `surface_wear_atlas.py` builds these from 4K BaseColor/Opacity without changing originals.
- Controls: `scripts/controls/effects/surface_wear_graph_check.py` checks defaults, shared product
  topology, scan-independent regions, fallback, compatibility and the unchanged scratch graphs.
  `surface_wear_hybrid_check.py` checks period and undersides without any atlas dependency;
  pass `--project <project> --out <output>` after Blender's `--`.
  `surface_wear_lab.py` retains the shared edge rig and variation AOV reader.

## 4. Instructions and parameters, per layer
### 4.1 Grunge
Use hybrid by default. The soft procedural region chooses the stain outline; the two scans
supply texture within it. Three lookups and slow noise blending reduce recognizable repeats.
White in both Mask scans denotes grime; black denotes clean background. Their corresponding
Roughness maps place brighter roughness on the same marks. Preserve that polarity: load the full
0–1 data range without inversion, then fit a monotone post-tiling remap above the background.
Keep marks a minority inside the region; do not raise the background with a low gamma or clip
it to full grime to obtain a stronger image. Adjust procedural region coverage and foreground
contrast together at a fixed amount. Inspect the raw scan beside the remapped interior.
Each lookup is randomly rotated, so the interior carries no direction: vertical streaks in a
raw scan average out. For directional grime (run-down on walls), stretch the procedural region
along the direction instead.

| Parameter | Starting point |
|---|---|
| Layer / current default | `grunge` / hybrid |
| Interior scans | `uh4tfagc`, `uh4uabdc`; both 0.7 m, 4K `_Mask` |
| Interior levels | black 0, white 1, gamma 1, no inversion; no per-scan compensating clip |
| Post-tiling remap | black/white 0/1, gamma/gain 1/1 defaults; remove only background, then fit foreground contrast and region coverage |
| Mapping size | each scan's metadata size, 0.7 m |
| Region threshold / edge width | 0.24 / 0.20, normalized procedural-field units |
| `scale_m` | 0.25 m starting point; size from final-view pixels (RULES MAT_03) |
| `amount` | 0.45 used-interior starting point; inspect the shot |
| Colour / roughness multiplier at factor 1 | 0.52 / 1.35 |

### 4.2 Scratches
Default `hybrid` (the user: all layers hybrid), but still the legacy scan modulation of the
procedural strokes, not the region × interior hybrid of the other layers; not yet judged.
Judge it in a close scene before relying on it.

| Parameter | Existing setting |
|---|---|
| Layer / current default | `scratches` / hybrid (legacy modulation) |
| Mask | `vdekdjrc`, 0.5 m, 4K `_Mask` |
| Procedural directions | 13, 61, 112 and 157 degrees, independently phased |
| `scratch_width_m` | default 0.003 m; inspect actual stroke width in final-view pixels |
| Mask crossing | second copy +90 degrees and offset (0.37, 0.19) UV tiles |
| Roughness / normal | smoother grooves; inverted bump 0.15 mm, strength 0.4 |

### 4.3 Dried water marks and stains
The hybrid uses the same two-scan interior pool on vertical and up-facing faces. Bright values
denote deposits in both scans. Remove the Roughness image's approximately 0.34 background before
blending; retain its bright rims and bodies without inversion. The Mask needs no background or
gamma compensation. These assets have no BaseColor maps; compare their Mask/Roughness patterns
and raw-mask control rather than inferring polarity from an unavailable albedo.

Its procedural region uses the continuous warped blob distance before body/rim profiling,
multiplied by the shared extent. Thresholding an already flattened deposit body against a smooth
height fade can turn that fade into broad gradient bands. The continuous field avoids those
plateaus; the darker drying rim follows its irregular region boundary. These are dry deposits
with roughness change, not active water films. Every source excludes undersides.

The procedural fallback uses domain-warped, varied-size, sometimes merged blobs and uneven rims,
with no radial circle or identical tide-ring primitive. The raw mask option retains the original
Normal-Z split: `tjwtbgvc` on vertical faces and `uh4tdhic` on up-facing faces.

| Parameter | Starting point |
|---|---|
| Layer / current default | `dried-marks` / hybrid |
| Hybrid interior scans | `uh4tdhic`, 0.7 m, 4K `_Mask`; `tjwtbgvc`, 1 m, 4K `_Roughness` |
| Interior levels, `uh4tdhic` | black 0, white 1, gamma 1; no inversion |
| Interior levels, `tjwtbgvc` | black 0.34, white 1, gamma 1; removes background; no inversion |
| Post-tiling remap | fit black/white, gamma/gain after the common region; inspect both wall and drip zones |
| Mapping size | each scan's listed 0.7 m or 1 m size |
| Region threshold / edge width | 0.07 / 0.08, normalized procedural-field units |
| Drying rim | `4 × region × (1-region)`; up to 25% additional colour darkening weighted by wear |
| `scale_m` | 0.25 m starting blob spacing; size from the shot (RULES MAT_03) |
| `amount` | 0.85 starting point for readable deposits; inspect both close and final-view crops (RULES MAT_03) |
| Colour / roughness multiplier at factor 1 | 0.35 / 1.45 |
| Underside gate | world Normal Z below -0.001 excluded |
| Raw-mask zone blend | world Normal Z from 0.25 to 0.75 |

For explicit `stamps`, build separate top-anchored leaks and small wall-foot stains. Atlas
`density` is occupied-cell probability; do not multiply it by a second patch sample. The common
point extent supplies patchiness. Use `profile='deposit'` for a darker rim and source-tone body.
The `wbhtbcov`, `wbhtahpv`, `wbhtbcev` maps fill their tiles: mark their `cutout_indices` to extract
irregular pieces. Keep the oil/mud silhouettes (`sdfplbi`, `sdjliyi`) intact. Every point samples
3×3 neighbouring cells; maximum scaled half-diagonal + centre jitter + top-anchor shift must
fit one cell width. Stamps may then cross their own cell border without clipping.

### 4.4 Worn-through patches
Use hybrid by default. Supply the actual under-material shader. The hybrid uses a hard procedural
region and a thresholded bare-substrate scan inside it. Displacement does not reliably segment
paint from substrate in these assets: their height distributions overlap. Registered BaseColor
instead verifies opposite Roughness polarities: `ub1meemn` has smooth green substrate under white
paint; `tmulfghdy` has rough pale substrate under green paint. Normalize those signals to white
bare/black paint before stochastic blending. Each shading point is coat or the actual
under-material: there is no grey half-mix, dark overlay or wet-looking
tint added to the bare material. Only antialiasing mixes the image pixels along chip edges.

Size the scan in the final view so several scan-shaped flakes fit inside a region (RULES MAT_03).
Override `MaskSource.size_m` when necessary and record the chosen world sizes in study notes;
keep the source metadata unchanged. A paler test coat helps distinguish chips from stains;
that coat colour is scene code, not a skill default.

| Parameter | Starting point |
|---|---|
| Layer / current default | `worn-through` / hybrid |
| Hybrid interior scans | `ub1meemn`, 1 m; `tmulfghdy`, 2 m; both 4K `_Roughness`, polarity checked against `_BaseColor` |
| Substrate extraction, `ub1meemn` | black/white 0.65/0.72, then invert: low Roughness is bare green substrate |
| Substrate extraction, `tmulfghdy` | black/white 0.80/0.85, no inversion: high Roughness is bare pale substrate |
| Mapping size | start at the listed 1 m / 2 m sizes; size resolved flakes from the shot |
| Region threshold / final edge | 0.30 normalized field units / binary hard edge |
| Flake cutoff | `flake_threshold` default 0.5; actual cut = threshold + 0.5 - amount |
| Amount | varies chip coverage through that cut; 0 disables the layer |
| `scale_m` | 0.25 m starting patch size; size from the shot (RULES MAT_03) |
| `amount` | 0.50 used-interior starting point |
| `under_shader` | required shader output socket; binary hybrid directly selects it without a dirt overlay |
| Raw mask option | `uh4tbdhc`, 0.7 m, 4K `_Mask` |

For explicit `stamps`, `ukgodfdcw` (2 m), `ujzjdgmo` and `ui2ncdjfw` (1 m) use `_Opacity`
with an opacity atlas and full chip rotation. That separate source retains scan-shaped outlines;
it is never selected by a hybrid builder or a default.

### Shared settings and mask loading
- Edge width is the span of the region's smoothstep in normalized field units. It is not a
  constant distance in metres; its visible width also depends on `scale_m` and the field gradient.
  Size it from the final shot (RULES MAT_03). No scan changes the procedural region's outline.
- `WearExtent` starts at floor datum 0 m, fades feet over 0.02–0.7 m, and uses a 2.3 m patch
  field remapped over 0.46–0.66. For dense low scuffs, try full strength below 0.3 m and a higher
  fade limit. Optional `drip_top_m`/`drip_length_m` describe actual vertical deposit origins.
- `HybridSource` uses 3 lookups, seed 17, blend scale 1.7 m and scale jitter 0.88–1.12.
  These and the amounts are shot-dependent starting points, not rules.
- Keep assets under the project library/local directory. `asset_mask` reads scan size from
  `meta.json`; 4K maps are Non-Color grayscale RGB. Levels, gamma and optional inversion precede
  the stochastic blend. Raw `MaskSource` also supports rotation, offset, world or named-UV mapping.
- Project world metres onto the dominant face plane. For `mapping='uv'`, author the named UVs
  with `box_uv` or `directional_uv` at the scan size; do not scale twice.
- Keep one amount per layer across comparisons; report the final AOV mean/SD and coverage.
  Fit the hybrid interior against the procedural control at that amount. Compare the same native
  pixels using the beauty PNG change/off-off-noise metric; aim within 15%, and retain interior
  variation in the flat masks. Factor AOVs report coverage separately from that image metric.
  Use variation-surface-marks.md §4.3 for extent/strength calibration. Inspect beauty PNGs beside
  unlit component masks and native crops, with repeated-render noise (RULES VAL_02).
- Check polarity against registered albedo where present and the raw-mask control otherwise.
  Show unmodified source scans and a same-crop pre-remap scan/interior board. Keep interior mean
  and strong-mark area below one half; filtered nonzero pixels are not a coverage measure because
  antialiasing spreads fine marks. For binary chips, interior mean is exposed-substrate coverage.

### Generic layers
| Layer | Reference | Note for this effect |
|---|---|---|
| Macro tone; extent and strength | variation-surface-marks.md §4.3 | measure after masking |
| Edge-shaped wear and run-off | edge-wear.md | run-off stays procedural; the 0.25 m leakage mask tiled visibly |
| Wet film | wet-surfaces.md | active water, distinct from dried deposits |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Hybrid outline follows a scan | bitmap was fed into the region driver | keep scans exclusively in the interior input (§2) |
| Hybrid interior looks flat | near-one modulation or a threshold erased its contrast | retain the full normalized scan through the product (§4 shared settings) |
| Hybrid seems reversed | background was boosted into wear, or a map's polarity was assumed | verify registered source values; keep clean/paint background black and foreground sparse (§4) |
| Dried region/rim has broad gradient bands | profiled body plateau was thresholded against a height fade | build its region from continuous blob distance before profiling (§4.3) |
| Raw mask tiles visibly | listed scan too small for the area | retain physical scan size and compare stochastic hybrid (§4 shared settings) |
| Wear resembles camouflage | coverage/amount too high | reduce location extent and amount from the final view (§4 shared settings) |
| Dried marks appear on soffits | orientation gate bypassed | retain the common underside exclusion (§4.3) |
| Dried deposit is unreadable | weak body/edge contrast or sparse/rejected stamp placement | inspect region and interior separately; stamps use explicit occupancy and top anchoring (§4.3) |
| Stamps clip or make squares | neighbour support insufficient, or full-tile opacity used as a decal | satisfy support bound and extract continuous-texture cutouts (§4.3) |
| Default scan missing | named 4K map unavailable | procedural fallback and one missing-id/Fab-search line (§3) |
| Worn-through looks painted | colour changed without an under-material | supply the actual under-material shader (§4.4) |
| Scratches cannot be judged | camera/light cannot resolve their glints | leave undecided and judge in a close scene (§4.2) |

Generic problems: troubleshooting.md.
