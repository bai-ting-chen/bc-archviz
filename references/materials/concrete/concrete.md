# Concrete

## 1. Overview
Plain, jointless concrete in two looks: **monolithic** cast-in-place concrete (basements, car parks,
cast-in-place frames) and **burnished or polished white** concrete (microcement, soffits). The base
recipe is `concrete_study()`: a mapped base with tone matched to the reference, roughness mixed between
map and a constant, and a normal chain; world-space masks place grunge, damp and grime. Concrete with
board marks that resolve in frame is covered by board-formed-concrete.md.

**Use when:** a plain or jointless concrete surface, monolithic or burnished. Board marks that
resolve in frame: board-formed-concrete.md.

## 2. Layers and node-editor diagram
Specific layers are described in §4. Generic layers are written once, in their own reference, and
used here with concrete settings.

```
                           CONCRETE (monolithic and burnished)
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ SPECIFIC (§4)                          GENERIC (own reference)            │
 │ 1  Base recipe and tone  → colour, rough   Concave corners → edge-wear.md │
 │ 2  Zone masks (Normal Z) → masks           Runoff, cracks  → edge-wear.md │
 │ 3  Grunge patches        → colour, rough                                  │
 │ 4  Damp band at the foot → colour, rough                                  │
 │ 5  Leak stain            → colour                                         │
 │ 6  Concave-corner grime  → colour (AO)                                    │
 │ 7  Monolithic tone match → own albedo                                     │
 │ 8  Burnished gloss       → roughness, bump                                │
 │ 9  Trowel marks          → tone, roughness                                │
 │ 10 Arris dirt            → colour (edge mask)                             │
 │ 11 Bounce correction     → albedo                                         │
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
- The current build (`concrete_build.py`, `concrete_study(stain=True)`) still loads a Megascans leak
  opacity map through `stain_map`, from the study's `library/local/` (the user downloads it). It raises
  if the file is missing. The procedural stain of §4.5
  replaces it; until that is built, the bitmap path is the one that runs.
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

### 4.5 Leak stain (procedural)
- Leak stains run down vertical faces from joints, cracks and drip edges. Build them as a procedural
  mask, not a bitmap: nothing to download, no UV set, nothing that can go missing.
- A noise field in world space, stretched along Z (long streaks, short across), broken up by a finer
  noise in the same frame, and thresholded into ragged streaks (the threshold rule of §4.3).
- Streaks fade downward from a start height, so they begin at the top of the wall and never fill the
  whole face.
- Mask (1 − |N.z|), so only verticals take a stain and streaks never run on horizontal faces.
- A Megascans leak map is an alternative only when the user has downloaded one and approves it; ask first.
- **Not yet tested.** Set the stretch, start height and fade in a control, not by eye in the node
  preview (RULES VAL_02), and record the values in the study notes.

| Parameter | Value |
|---|---|
| Field | world-space noise, stretched along Z; long streaks, short across |
| Break-up | finer noise in the same frame, summed before a narrow threshold (§4.3) |
| Start height | top of the wall or the leak source; sized from the shot |
| Fade | downward from the start height |
| Mask | (1 − \|N.z\|): verticals only |

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

### Generic layers, concrete settings
| Layer | Reference | Note for this material |
|---|---|---|
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
| Neutral white turns cyan | bounce colour | correct the albedo toward the reference (§4.11) |
| No stain on the wall | start height below the visible wall, or fade too fast | raise the start height or slow the fade (§4.5) |
| Streaks look like a regular pattern | noise with no break-up | add the finer break-up before the threshold (§4.5) |

No generic problems are listed in this file. The general list is in troubleshooting.md (named here,
not linked, so this file adds no reference loop).
