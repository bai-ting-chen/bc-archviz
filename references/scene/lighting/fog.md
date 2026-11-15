# Fog and mist

## 1. Overview
Volumetric fog and mist with a density taken from the visibility distance; local steam over hot water.

## 2. Layers and node-editor diagram
```
 ┌─ FOG AND MIST — PROCEDURE DIAGRAM ──────────────────────────────────────┐
 │ Density       visibility V ─► sigma = 3.912 / V                        │
 │   ▼                                                                    │
 │ Shape         height fade × hollows × patch noise ─► Density           │
 │   ▼                                                                    │
 │ Clear boxes   zero density inside buildings                            │
 │   ▼                                                                    │
 │ Scatter       Volume Scatter, Mie phase ─► Material Volume             │
 │   ▼                                                                    │
 │ Render        volume bounces on                                        │
 └────────────────────────────────────────────────────────────────────────┘
```

## 3. Code
- `scripts/blender/scene/lighting/atmosphere.py` (module `scene.lighting.atmosphere`):
  - `fog_volume(centre, visibility_m, box, top, diameter_um=…, valley=…, patch=…, clear_boxes=…)`: the
    fog box; pass the options by keyword.
  - `sigma_from_visibility(visibility_m)`; `volume_render_settings(bounces, max_bounces)`.
- Steam: `scripts/blender/materials/shared/volumes.py` (`steam()`), a small Principled Volume over hot water.
- Control: `scripts/controls/lighting/fog_koschmieder.py` (transmission = exp(−sigma·d) to 1.000).

## 4. Instructions and parameters
1. **Density.** Extinction coefficient from the meteorological visibility (Koschmieder, 2 % contrast).
   Check: an object at distance d keeps exp(−sigma·d) of its contrast.
2. **Shape.** A box around the site with the camera inside: full below the fog top, a smooth fade
   to clear air above it, denser in hollows, patchy by noise (RULES MAT_03). Size the box and the
   levels from the site.
3. **Clear boxes.** Indoor air has no fog; a fog-filled dark room behind glass is also a noise source.
4. **Scatter.** Droplets scatter forward and do not absorb: Volume Scatter, phase Mie, white.
5. **Render.** `volume_render_settings()`: with volume bounces at 0 the fog only removes light.
   Light it with a sunless HDRI of the matching condition (`references/scene/lighting/hdri.md`).
   Check: a contrast-stretched sky crop is free of blotches.

| Parameter | Value |
|---|---|
| Visibility, dense fog | ~150 m |
| Visibility, mist | 1 000–2 000 m |
| Droplet diameter | 5–20 µm |
| Volume bounces | 8 |
| Render cost | ~2.5–3.5× a clear scene |

**Steam over hot water** (a hot tub, a heated pool) is a small local volume, not site fog: `steam()`,
density = noise × a fade with height above the water, forward-scattering (anisotropy ~0.5). Steps 1–3
do not apply; step 5 does.

| Parameter | Value |
|---|---|
| Steam anisotropy | ~0.5 |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Fog dark and murky | volume bounces 0 | `volume_render_settings()` (step 5) |
| Fog a uniform wall | no height fade or patch noise | shape it (step 2) |
| Noisy dark rooms behind glass | fog inside the building | clear boxes (step 3) |

Generic render problems are in troubleshooting.md.
