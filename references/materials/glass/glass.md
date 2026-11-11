# Glass

## 1. Overview
A flat glazed pane in two layers: the clear glass base, and the surface distortion real glazing has
(roller waves and pillowing). Neighbours: patterned, cast or pressed relief is in
[glass-relief.md](glass-relief.md); hollow glass block units and walls are in
[glass-block.md](glass-block.md); water on or behind glass is in
[water-attached-film.md](../water/water-attached-film.md).

## 2. Layers and node-editor diagram
Specific layers are described in §4. Generic layers are written once, in their own reference, and
used here with glass settings.

```
                            GLASS — LAYER DIAGRAM
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ SPECIFIC (§4)                                                             │
 │   §4.1 Clear glass base          → transmission, IOR, tint, roughness     │
 │   §4.2 Roller waves, pillowing   → bump                                   │
 │ GENERIC (own reference)                                                   │
 │   Directional blur               → anisotropy.md                          │
 │   Relief (patterned, cast)       → glass-relief.md                        │
 │   Water on the glass             → water-attached-film.md                 │
 └───────────────────────────────────────────────────────────────────────────┘
   base (§4.1) ─► Principled: Base Color, IOR, Transmission, Roughness
   roller wave + dome (§4.2) ─► Bump ─► Principled Normal
```

- The distortion is added to a finished base material; it changes the normal only, plus a trace of
  roughness.
- Off switch (RULES MAT_07): the base alone is the pane without §4.2; on a built material, mute the
  Bump node labelled "roller wave + pillowing".

## 3. Code
- `scripts/blender/materials/glass/` (module `materials.glass.glass`):
  - `clear_glass(name, tint, roughness, ior)`: the one clear-glass builder (§4.1).
  - `glass_distortion(mat, obj, wave_period, wave_amp_mm, pillow_mm, roughness)`: adds §4.2 to `mat`,
    with the dome centred on `obj`.
  - `glass_shell(objs, thickness)`: turns solid lamp globes into thin shells; its use is in
    `references/scene/lighting-camera.md`.
- Controls: `scripts/controls/material/glass_graph_check.py` (node-graph baseline of the base, the
  shell and the distortion); `scripts/controls/environment/outdoor_smoke.py` renders a distorted pane.

## 4. Instructions and parameters, per layer
Table values are starting points; size them from the shot (RULES MAT_03) and record the final values
in the study notes (RULES GOV_01).

### 4.1 Clear glass base
- One builder for every clear glass. Coloured glass is the same builder with a tint.
- The tint multiplies the light at every crossing, so two panes in a row square it. Stay within a
  few percent of white; thick or low-grade glass leans green.
- A material that already exists under that name is edited in place, so nodes added by hand stay.

| Parameter | Value |
|---|---|
| `ior` | 1.52 (soda-lime) |
| `tint` | white (1, 1, 1); slight green for thick panes |
| `roughness` | 0 |
| Transmission | 1 (set by the builder) |

### 4.2 Roller waves and pillowing (bump)
- Glazing is not optically flat, and a perfectly flat pane reads as CG. Two things bend its
  reflections: **roller waves** from the float line (a fine, regular ripple) and **pillowing** of an
  insulated unit (each pane bowed, strongest towards the frame).
- The dome carries the effect. The roller wave only breaks up straight reflected lines; too much of it
  draws stripes across the pane.
- The dome is centred on `obj`'s bounding box and skips its thinnest axis, the glass thickness. Panes
  that share the material must have the same thin axis.
- Judge it on a reflection with straight lines in it (a mullion, a horizon, a neighbouring façade).

| Parameter | Value |
|---|---|
| `wave_period` | 0.30 m |
| `wave_amp_mm` | 0.05 mm (real float glass ~0.1 mm peak to valley, ~1 mrad slope) |
| `pillow_mm` | 2 mm (real units bow a few mm) |
| `roughness` | 0.01 |

### Generic layers, glass settings
| Layer | Reference | Note for this material |
|---|---|---|
| Directional see-through blur | [anisotropy.md](../../effects/anisotropy.md) | reeded or brushed glass too fine to model; needs roughness above 0 |
| Relief | [glass-relief.md](glass-relief.md) | patterned, cast and pressed glass: geometry, not bump |
| Water on the glass | [water-attached-film.md](../water/water-attached-film.md) | the wetted face takes the IOR ratio 1.14 |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Pane reads as blinds or stripes | roller wave too strong (0.25 mm does it) | lower `wave_amp_mm`; let the dome carry the effect (§4.2) |
| Reflections are ruler-straight, pane reads as CG | no distortion | add §4.2 |
| Glass turns green or dark through several panes | tint multiplied at every crossing | tint closer to white (§4.1) |
| Dome runs through the glass thickness | panes sharing the material have different thin axes | one material per orientation (§4.2) |

- Glass that looks too reflective, or shows nothing: `references/scene/lighting-camera.md` › Glass and
  what it shows. Other generic problems are in troubleshooting.md.
