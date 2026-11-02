# Variation: surface marks

## 1. Overview
Noise fields that break an even surface: two layers (a macro tone across the whole surface, and grunge),
then two steps for every layer and for the marks of other files (wet, stain, wear, dirt): a patchy extent,
and a strength set from what reaches the image, since Blender Noise rarely reaches its given range.

**Use when:** a surface reads too even, or a grunge layer's strength is off.

## 2. Layers and node-editor diagram
```
 ┌─ VARIATION: SURFACE MARKS — LAYER DIAGRAM ───────────────────────────┐
 │ 4.1 Macro tone  → albedo ×, roughness +                              │
 │ 4.2 Grunge      → albedo, roughness: normalised signed field         │
 └──────────────────────────────────────────────────────────────────────┘
 ┌─ EVERY LAYER AND MARK (4.3) — PROCEDURE DIAGRAM ─────────────────────┐
 │ Extent    marks only: a slow mask that can reach zero ─► mark amount │
 │   ▼                                                                  │
 │ Strength  each layer's AOV and the beauty ─► gain                    │
 └──────────────────────────────────────────────────────────────────────┘
 macro tone (4.1), grunge (4.2) ─► Base Color (×), Roughness (+)
```
- One multiplier and one switch per field (RULES MAT_07).

## 3. Code
- `scripts/blender/effects/variation_surface_marks.py`: `macro_tone`, `grunge`, `patchy_extent`, each
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

### 4.2 Grunge
- A range set on the remap extremes lands far smaller (±15 % → ~±3 %); averaging two fields shrinks it again,
  masks dilute it.
- Normalise: sample the field on the surface, remap around its measured mean and SD to a signed field, then
  set the gain from the SD you want.
- A scan as grunge source must be non-directional: board-formed, panel and brushed scans bring their own lines.
  Preview it first. Isotropic cloud noise alone reads as smoke.
- Check: the AOV SD matches the target (§4.3 step 2).

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
| Grunge too weak in the render | range set on the remap extremes; averaged or masked fields | normalise by the measured SD (§4.2) |
| Strength does not match the shader value | set on the shader parameter | measure the AOV (§4.3 step 2) |
| Directional lines | board-formed, panel or brushed scan as grunge | non-directional scan (§4.2) |
| Reads as smoke or blur | isotropic cloud noise | gravity-shaped run-off (edge-wear.md) |
| Constant-width band or contour ring | fixed extent | slow noise that reaches zero (§4.3 step 1) |

Generic problems: troubleshooting.md.
