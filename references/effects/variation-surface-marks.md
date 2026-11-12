# Variation: surface marks

## 1. Overview
A slow tone drift across a whole surface, and the method that sets the extent and strength of every
mark layer from the image.

**Use when:** a surface reads too even, or a mark layer's strength is off.

## 2. Layers and node-editor diagram
```
 ┌─ VARIATION: SURFACE MARKS — LAYER DIAGRAM ───────────────────────────┐
 │ 4.1 Macro tone  → albedo ×, roughness +                              │
 └──────────────────────────────────────────────────────────────────────┘
 ┌─ EVERY LAYER AND MARK (4.3) — PROCEDURE DIAGRAM ─────────────────────┐
 │ Extent    marks only: a slow mask that can reach zero ─► mark amount │
 │   ▼                                                                  │
 │ Strength  each layer's AOV and the beauty ─► gain                    │
 └──────────────────────────────────────────────────────────────────────┘
 macro tone (4.1) ─► Base Color (×), Roughness (+)
```
- One multiplier and one switch per field (RULES MAT_07).

## 3. Code
- `scripts/blender/effects/variation_surface_marks.py`: `macro_tone`, `patchy_extent`, each
  with its `var_<layer>` AOV (§4.3 step 2).
- Control: `scripts/controls/effects/variation_lab.py --only marks`.

## 4. Instructions and parameters, per layer
### 4.1 Macro tone
- Cheapest, biggest payoff: a world-space noise × albedo, + roughness.
- Check: on the full frame the tone drifts across the surface, with no blobs.

| Parameter | Value |
|---|---|
| Scale | 2–8 m, world space |
| Albedo | ±5–10 % (multiplied) |
| Roughness | added |

### 4.2 Surface wear (moved)
Grunge, scratches, dried marks and exposed under-material: [surface-wear.md](surface-wear.md).

### 4.3 Every layer and mark
1. **Extent** (marks only, RULES MAT_05). Drive the extent of a mark with a slow noise that can reach zero
   (`patchy_extent`); give each mark a physical shape (a dried splash is a blob, darker at its rim).
   Check: some areas carry none; no constant-width band or contour ring.
2. **Strength from the image.** Needs an AOV of each layer's multiplier. Measure it on interior pixels of dry
   surfaces and on the beauty, never from the shader value. Choose it from previews composited from one
   render. Undo: the layer's amount 0.

### Generic layers
| Layer | Reference | Note for this material |
|---|---|---|
| Run-off, edge dust | [edge-wear.md](edge-wear.md) | weathering on walls is gravity-shaped |
| Previews, strength choice | [validation.md](../review/validation.md) | composite from one render |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Strength does not match the shader value | set on the shader parameter | measure the AOV (§4.3 step 2) |
| Constant-width band or contour ring | fixed extent | slow noise that reaches zero (§4.3 step 1) |

Generic problems: troubleshooting.md.
