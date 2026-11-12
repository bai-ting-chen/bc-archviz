# Concrete

## 1. Overview
Concrete without board marks: monolithic cast-in-place (§4.2–§4.7), burnished or polished (§4.8–§4.11)
and exposed-aggregate precast (§4.12).

**Use when:** board marks are not visible. Board marks that resolve in frame: board-formed-concrete.md.

## 2. Layers and node-editor diagram
Specific layers are described in §4. Generic layers are written once, in their own reference, and
used here with concrete settings.

```
              CONCRETE (monolithic and burnished) — LAYER DIAGRAM
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ SPECIFIC (§4)                          GENERIC (own reference)            │
 │ 1  Base recipe and tone  → colour, rough   Concave corners → edge-wear.md │
 │ 2  Zone masks (Normal Z) → masks           Runoff, cracks  → edge-wear.md │
 │ 3  Grunge patches        → colour, rough                                  │
 │ 4  Damp band at the foot → colour, rough                                  │
 │ 5  Leak stain            → see Runoff                                     │
 │ 6  Concave-corner grime  → colour (AO)                                    │
 │ 7  Monolithic tone match → own albedo                                     │
 │ 8  Burnished gloss       → roughness, bump                                │
 │ 9  Trowel marks          → tone, roughness                                │
 │ 10 Arris dirt            → colour (edge mask)                             │
 │ 11 Bounce correction     → albedo                                         │
 │ 12 Aggregate precast     → mapped surface, soffit slot                     │
 └───────────────────────────────────────────────────────────────────────────┘
   order of evaluation                       node-editor output it drives
   zone masks (2) ─► grunge (3), damp (4), stain (5), concave (6) ─► colour multipliers
   base map × tone (1) ─────────────────────────────────────► Base Color ─► Principled
   base roughness mixed with a constant (1) ─► Roughness, plus gloss (8), trowel marks (9)
   Normal Map ─► Bump ─► Bevel (1, 8) ───────────────────────► Principled Normal
   arris edge mask (10) ─► darkening ───────────────────────► Base Color
```

- Monolithic layers (§4.2–§4.7) and burnished layers (§4.8–§4.11) are separate looks; use the set
  that matches the wall.
- Each mask is remapped into a narrow high range before it multiplies into the colour (§4.3).

## 3. Code
- `scripts/blender/materials/concrete/`: `concrete_build.py` (`concrete_study`), `concrete_tone.py`
  (`retone`, called as `materials.concrete.concrete.retone`), `concrete_masks.py` (edge masks), and
  `concrete.py` (the module the calls go through).
- Control: none named in this file.

## 4. Instructions and parameters, per layer

### 4.1 Base recipe and tone
- `concrete_study()` builds the base: map × tone multiplier to hit the target albedo; roughness
  mixed between the map and a constant; IOR 1.5; light coat; Normal Map → Bump → Bevel.
- **Tone:** check the recipe's tone multiplier against the reference. The default is a cool match and
  reads blue-grey next to a warm reference.
- **Scanned base:** for a rough, weathered concrete from a dark scanned map, use
  `materials.concrete.concrete.retone(mat, target, tex_id)`: desaturate, then scale the measured mean
  to the target albedo (the multiply keeps pits and pores).
- **Fresh breaks:** under direct floods, their tint sits only *barely* above the surface. A visibly
  lighter paste reads as white paint flecks when lit head-on.

| Parameter | Value |
|---|---|
| IOR | 1.5 |
| Coat | light |
| Roughness | map mixed with a constant |
| Tone multiplier | matched to the reference; the default is a cool match |
| Scanned base | retone: desaturate, then scale the measured mean to the target |
| Fresh-break tint | barely above the surface |

### 4.2 Zone masks (Normal Z)
- **Monolithic but one material:** floor, walls, ceiling, beams and columns share one material. Vary
  it by world-space masks inside the shader, not by separate materials.
- Geometry › Normal Z separates *up* (floor), *down* (ceilings) and *vertical* (walls).

| Parameter | Value |
|---|---|
| Mask source | Geometry › Normal Z, world space |
| Up (floor) | lower roughness, sealed-slab sheen, softer stains |
| Down (ceilings) | less grunge |
| Vertical (walls) | damp band at the foot (§4.4) |

### 4.3 Grunge patches
- Grunge comes in patches, not streaks (RULES MAT_05); check the reference before adding any streak.
- Shape, all world-space Noise: a low-frequency patch field (with some Distortion) plus a centred
  high-frequency field at low amplitude, summed *before* a narrow threshold. That sum gives ragged,
  speckled borders instead of soft blobs.
- Inside a patch: mid-frequency mottle × speckle. Keep clean gaps between patches.
- Floor stains: use separate decorrelated fields (Mapping › Location offset) so they don't echo the wall.
- Multiplying several 0..1 masks washes them out fast. Remap the inner masks into a narrow high range
  before multiplying, or the patches disappear.

| Parameter | Value |
|---|---|
| Patch field | low frequency, with some Distortion |
| Speckle field | centred, high frequency, low amplitude |
| Threshold | narrow, applied after the sum |
| Inside a patch | mid-frequency mottle × speckle |
| Floor stains | decorrelated fields via Mapping › Location offset |
| Inner masks | remapped to a narrow high range before multiplying |

### 4.4 Damp band at the foot
- Damp band at the foot of walls and columns: world Z thresholded, plus the same ragged noise so the
  top edge isn't a straight line.

| Parameter | Value |
|---|---|
| Band | world Z threshold, at walls and columns |
| Top edge | the same ragged noise, not a straight line |

### 4.5 Leak stain
- Procedural, no bitmap: `add_leak_field` on the object, then `add_runoff` on its `weathered_concrete`
  material. Method and parameters: [edge-wear.md](../../effects/edge-wear.md) › Run-off.

### 4.6 Concave-corner grime
- AO node set to **Outside**, not Inside, × fine noise, into the grunge darkening. Method and related
  runoff: [edge-wear.md](../../effects/edge-wear.md) › Concave corners.

| Parameter | Value |
|---|---|
| AO node | Outside |
| Noise | fine |
| Drives | grunge darkening |

### 4.7 Monolithic but not identical
- A drum or infill of the "same" concrete often measures darker than the walls under the same light.
  Match the measured ratio by giving it its own albedo rather than relighting it.

| Parameter | Value |
|---|---|
| Method | own albedo, matched to the measured ratio |
| Not used | relighting |

### 4.8 Burnished gloss and tone clouds
- Reads glossy, not matte: low roughness varied in soft clouds; the plaster relief mostly polished off
  (sub-millimetre bump).
- Tone clouds at two scales. Lighting gradients swallow small tone differences, so a variation that
  looks right in the node preview can render perfectly clean. Judge it in a render.

| Parameter | Value |
|---|---|
| Roughness | low, varied in soft clouds |
| Bump | sub-millimetre |
| Tone clouds | two scales |
| Judge | in a render, not the node preview |

### 4.9 Trowel marks
- Moderately stretched noise (a strong stretch draws parallel lines), rotated, high distortion,
  thresholded to its top few percent and clustered by a patch mask; lighter and smoother than the field.

| Parameter | Value |
|---|---|
| Stretch | moderate (a strong stretch draws parallel lines) |
| Rotation | rotated |
| Distortion | high |
| Threshold | top few percent |
| Clustering | patch mask |
| Tone and roughness | lighter and smoother than the field |

### 4.10 Faint arris dirt on huge meshes
- Faint dirty arris on huge meshes (30 m slabs, canopies): use the shader **Bevel normal vs true
  normal** as the edge mask (no dicing needed). GN `edge_dist` would need the mesh diced.
- "Very faint" sits just above visibility: set the darkening with a control (RULES VAL_02), since a
  value that looks faint in the shader can vanish entirely in the render.

| Parameter | Value |
|---|---|
| Edge mask | Bevel normal vs true normal |
| Dicing | not needed (GN `edge_dist` would need it) |
| Darkening | set with a control (RULES VAL_02) |

### 4.11 Bounce colour
- A neutral white next to a strongly coloured surface takes its bounce colour (a soffit over a
  turquoise pool renders cyan). Correct the albedo toward the reference rather than relighting.

| Parameter | Value |
|---|---|
| Fix | albedo corrected toward the reference |
| Not used | relighting |

### 4.12 Exposed-aggregate precast
- For columns and slab edges, box-map the same aggregate map at real size on the fascia and soffit bands.
- Assign downward faces to a second material slot using the settings below.

| Parameter | Value |
|---|---|
| Soffit test | Normal Z < −0.5 |
| Soffit material | smoother, darker concrete |

### Generic layers, concrete settings
| Layer | Reference | Note for this material |
|---|---|---|
| Surface wear | [surface-wear.md](../../effects/surface-wear.md) | grunge, scratches, dried marks and worn-through coatings |
| Concave corners | [edge-wear.md](../../effects/edge-wear.md) › Concave corners | method behind §4.6 |
| Runoff streaks, cracks | [edge-wear.md](../../effects/edge-wear.md) › §4.9–4.11 | for the weathered scanned base (§4.1) |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Patches vanish | several 0..1 masks multiplied without a remap | remap inner masks into a narrow high range (§4.3) |
| Patch borders are soft blobs | low-frequency field alone | add the centred high-frequency field before a narrow threshold (§4.3) |
| Floor stains echo the wall | shared noise fields | decorrelated fields via Mapping › Location offset (§4.3) |
| Streaks on horizontal faces | stain without the vertical mask | streaks only run down verticals (§4.5) |
| Top edge of the damp band is a straight line | no ragged noise | add the same ragged noise (§4.4) |
| Reads blue-grey beside a warm reference | default cool tone multiplier | match the tone to the reference (§4.1) |
| Fresh breaks read as white paint flecks | tint too light | tint barely above the surface (§4.1) |
| Burnished variation missing in render | judged in the node preview; lighting swallows the tone | judge in a render (§4.8) |
| Faint arris disappears in render | darkening just above visibility | set it with a control (§4.10) |
| Drum or infill does not match the walls | relit instead of given its own albedo | own albedo from the measured ratio (§4.7) |
| Soffits look like the fascia | one material slot | assign the soffit slot (§4.12) |
| Neutral white turns cyan | bounce colour | correct the albedo toward the reference (§4.11) |
| No stain on the wall | no leak field on the object, or `leak_ok` 0 | view it with `mask_view=attr: leak_ok`; edge-wear.md › Run-off (§4.5) |
| Streaks look like a regular pattern | presence and length too even | vary `presence` and `max_len` in `add_runoff(leak=…)`; edge-wear.md › Run-off (§4.5) |

No generic problems are listed in this file. The general list is in troubleshooting.md (named here,
not linked, so this file adds no reference loop).
