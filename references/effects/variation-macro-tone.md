# Variation: macro tone

## 1. Overview
Broad tone variation across a surface.

**Use when:** the base reads too even; localized dirt and damage belong to wear/wear.md.

## 2. Layers and node-editor diagram
```
 +-- VARIATION: MACRO TONE — LAYER DIAGRAM --------------------------+
 | §4.1 Macro tone -> Base Color x, Roughness +                     |
 | GENERIC: wear/wear.md -> localized dirt and damage            |
 +----------------------------------------------------------------+
 world position -> slow noise -> albedo multiplier / roughness addition
                -> independent amount switches -> AOVs -> shader inputs
```
- Compose the colour multiplier and roughness addition around the existing base (RULES MAT_07).

## 3. Code
- `scripts/blender/effects/variation_macro_tone.py`: `macro_tone` returns an albedo multiplier
  and a roughness addition, each with an amount control and `var_macro_tone` / `var_macro_roughness` AOV.
- Control: `scripts/controls/effects/variation_lab.py --only marks`.
  Add `--check-only` for graph checks without rendering.

## 4. Instructions and parameters, per layer
### 4.1 Macro tone
- Use a slow world-space noise to multiply albedo and add roughness.
- Check the full frame: tone drifts across the surface without becoming small blobs.
- Size the drift from the final view (RULES MAT_03).

| Parameter | Starting point |
|---|---|
| `scale_m` | 2–8 m; default 4 m, world space |
| `albedo` | ±5–10%; default ±0.075 around multiplier 1 |
| `roughness` | default ±0.05, added to the base |
| `amount` | 1; 0 restores colour multiplier 1 and roughness addition 0 |

### Generic layers
| Layer | Reference | Note for this effect |
|---|---|---|
| Localized dirt and damage | wear/wear.md | extent: wear/wear-locations.md; image-based strength: wear/wear.md |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Tone forms small blobs | field too small in the shot | increase `scale_m` and inspect the full frame (§4.1) |
| Surface remains uniform | amount is zero or drift is larger than the view | inspect both amount controls and the visible scale (§4.1) |

Generic problems: troubleshooting.md.
