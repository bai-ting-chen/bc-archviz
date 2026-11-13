# Metal

## 1. Overview
Metal, polished or brushed. Both are one material; only roughness and anisotropy change (§4.2).

## 2. Layers and node-editor diagram
```
 +-- METAL — LAYER DIAGRAM ------------------------------------------------+
 | SPECIFIC                                                               |
 | 4.1 Base clean metal       → metallic response, colour, roughness       |
 | 4.2 Brush streaks          → anisotropy, roughness                       |
 | GENERIC                                                                |
 | edge-wear.md               → rounded normal/geometry, edge line, dust  |
 | surface-wear.md            → grunge, scratches, marks: colour, roughness |
 | variation-macro-tone.md → macro tone: colour                         |
 +------------------------------------------------------------------------+
```
Clean mesh → edge fields → rounding geometry/normal → BSDF Normal.
Base (§4.1) → surface marks and edge masks → BSDF Base Color / Roughness.
Directional UV and streak noise (§4.2) → BSDF Tangent / Anisotropy / Roughness → Surface.

- Compose the terms at those inputs (RULES MAT_07); geometry-field order follows RULES MAT_08.

## 3. Code
- `scripts/blender/materials/metal/metal.py`: `materials.metal.metal.polished_steel(name="metal")`
  builds the base; smooth shading is set on the object separately.
- Brush and generic layers are applied separately through their linked effect references; the base
  builder exposes no switches for them. No complete metal control scene is named here.

## 4. Instructions and parameters, per layer

### 4.1 Base clean metal
- Use the builder in §3; polished-steel colour numbers live in
  [physical-ranges.md](../physical-ranges.md).

| Parameter | Value |
|---|---|
| BSDF | Metallic, F82 |
| Roughness | low for polished; increase for a brushed finish |
| Shading | smooth |
| Edge tint | brighter, warmer than the base |

### 4.2 Brush streaks
- Method: [anisotropy.md](../../effects/anisotropy.md).

| Parameter | Metal starting value |
|---|---|
| Anisotropy | ~0.75 for brushed; 0 for polished |
| Tangent | directional UV along the part's length |
| Rotation | 0.25 turn, so highlights stretch across the brushing |
| Streak noise stretch | ~400:1, driving roughness |

### Generic layers, metal settings
| Layer | Reference | Note for this material |
|---|---|---|
| Surface wear | [surface-wear.md](../../effects/surface-wear.md) | grunge, scratches, dried marks and worn-through coatings |
| Rounded edge/bevel, edge line, dust in joints | [edge-wear.md](../../effects/edge-wear.md) | keep the clean metal base beneath the wear |
| Macro tone | [variation-macro-tone.md](../../effects/variation-macro-tone.md) | vary base colour and roughness |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Metal looks faceted | flat object shading | shade smooth (§4.1) |
| Brush lines run across the part | tangent not along its length | align the directional UV (§4.2) |
| Brushed finish has no directional blur | roughness or anisotropy is zero | check both settings (§4.1, §4.2) |

Wear problems are in the effect references above; generic render problems in troubleshooting.md.
