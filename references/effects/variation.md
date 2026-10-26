# Variation

## 1. Overview
Repeated units and tiled maps need three kinds of variation: per-unit, macro, and anti-tiling (RULES MAT_06).
Cycles has no built-in stochastic tiling (5.2 manual: no such texture node), so it is built from nodes.
Grunge strength is set by what reaches the image, not by the shader parameter (§4.5).
Weathering shape, dust and cracks are in [edge-wear.md](edge-wear.md).

## 2. Layers and node-editor diagram
Specific layers are described in §4. Generic layers are written once, in their own reference.

```
                          VARIATION
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ SPECIFIC (§4)                              GENERIC (own reference)        │
 │ 1 Per-unit key       → tint, rough, bump,  Weathering shape, dust, cracks │
 │                        UV offset per unit          → edge-wear.md         │
 │ 2 Macro noise        → albedo, roughness   Previews, strength choice      │
 │ 3 Anti-tiling        → offsets of one map                → validation.md  │
 │ 4 Box projection     → UV-less geometry                                   │
 │ 5 Grunge strength    → multiplier per layer                               │
 │ 6 Patchy extent      → masks (wet, stain, wear)                           │
 └───────────────────────────────────────────────────────────────────────────┘
   per-unit values and map lookups (1, 3, 4)  what it drives
   key (1) ─► per-unit tint, roughness, bump strength, UV offset
   macro noise (2) ─► albedo ±, roughness + on the whole surface
   anti-tiling (3) and box projection (4) ─► the lookup itself (offsets, blend, bump from height)
   grunge (5) and patchy extent (6) ─► masks and multipliers on each layer's AOV
```

- **Per-unit values come from the key** read through Attribute › Instancer, so every part of one unit shares it
  (§4.1).
- **Macro variation** multiplies albedo and adds to roughness (§4.2); **grunge fields multiply** (§4.5).
- **Each layer's strength is measured on its AOV**, not set on the shader value (§4.5).

## 3. Code
- `scripts/blender/effects/variation.py`: `random_tone_material` (a per-unit tone material).
- The rest is node setups inside each material; no other script is named in this file.

## 4. Instructions and parameters, per layer
### 4.1 Per-unit key and per-unit variation
- **Per-unit key.** *Object Info › Random*: one value per object instance (a hash of the name; collection
  instances each get their own). A Rhino block made of several objects (frame + glass) gets a *different* value
  per part — for one value per unit store it on the instance (custom property or *Store Named Attribute*,
  Instance domain) and read it with *Attribute › Instancer*. *Geometry › Random per Island* (Cycles only) varies
  the pieces of one joined mesh (bricks, planks); it repeats across instances of that mesh, so combine it with
  the instance key.
- **Per-unit variation** from that key: tint ±2–5 % value, roughness ±0.05, bump strength, a random UV
  *offset* (offsets keep normal maps valid; rotations do not).

| Parameter | Value |
|---|---|
| Tint | ±2–5 % value |
| Roughness | ±0.05 |
| Bump strength | varied per unit |
| UV offset | random; offsets only (rotations break normal maps) |

### 4.2 Macro variation
- Cheapest, biggest payoff: a 2–8 m world-space noise multiplied into albedo (±5–10 %) and added to roughness;
  hides a repeat without removing it.

| Parameter | Value |
|---|---|
| Scale | 2–8 m, world space |
| Albedo | ±5–10 % (multiplied) |
| Roughness | added |

### 4.3 Anti-tiling
- Where a repeat would still show: 2–3 lookups of the same map with different offsets mixed by a noise (cost
  ×2–3, robust), or hex tiling (3 lookups over a random hex grid with weight-sharpened blending, Mikkelsen 2022).
  Voronoi-cell offsets are cheap but seam at cell edges unless blended there.
- Any UV rotation breaks a tangent-space normal map — drive relief from the height map through a Bump node
  instead. Free add-on to compare against: Patchwork (MIT).
- Offset lookup copies keep the original Image Texture projection, blend, interpolation and image colour space.
  Vary both coordinates used by that projection: zero Z offsets leave front-wall XZ texture rows in the same phase
  even when X/Y offsets differ.
- **LuxCore:** native Image › Randomized Tiling and 2D Mapping › Randomized UV; Object Info › Random converts per
  instance (luxcore.md › Native LuxCore materials).
- Generated maps with no recognisable feature (cloudy tone + grain) cannot show a repeat; a scanned map with stains
  or cracks repeats visibly along every joint it is box-mapped onto.

| Method | Cost and note |
|---|---|
| 2–3 offset lookups mixed by noise | ×2–3 cost; robust |
| Hex tiling | 3 lookups; weight-sharpened blend (Mikkelsen 2022) |
| Voronoi-cell offsets | cheap; seam at cell edges unless blended there |
| Patchwork add-on | MIT; to compare against |

### 4.4 Box projection (Rhino geometry without UVs)
- Image Texture › Box, Blend 0.1–0.2; again Bump from height, not the normal map.

| Parameter | Value |
|---|---|
| Projection | Box |
| Blend | 0.1–0.2 |
| Relief | Bump from height |

### 4.5 Grunge strength that reaches the image
- Blender Noise rarely reaches the ends of a remap: a ±15 % range set on the remap extremes lands near ±3 % in the
  render. Averaging two fields shrinks it again, and masks dilute it.
- Normalise each field to a signed value with a known SD (remap around its measured mean and SD, from samples on
  the surface), then set the gain from the SD you want.
- Set the strength by what reaches the image: measure each layer's multiplier on its AOV (interior pixels of dry
  surfaces only) and on the beauty, never by the shader parameter.
- Choose a strength from previews composited from one render ([validation.md](../review/validation.md)).
- A scan used as a grunge source must be non-directional: a board-formed, panel or brushed scan brings its own lines.
  Check its preview first; isotropic cloud noise reads as smoke or blur — weathering is gravity-shaped
  ([edge-wear.md](edge-wear.md) › Runoff).

| Parameter | Value |
|---|---|
| Remap range set on the extremes | ±15 % lands near ±3 % in the render |
| Normalisation | signed, known SD, from samples on the surface |
| Strength check | each layer's AOV multiplier (dry interior pixels) and the beauty |
| Scan | non-directional; preview first |

### 4.6 Patchy extent (MAT_05 procedure)
**Nature is patchy, never continuous or uniform**. Wetness, stains, wear, dirt, splashes: large here, small there,
absent elsewhere. A constant-width band or a contour ring reads as impossible. Drive extent with a slow noise that
can reach zero, and give marks a physical shape (dried splash = blob darker at its rim, not a line).

| Parameter | Value |
|---|---|
| Extent | slow noise that can reach zero |
| Dried marks | blob darker at its rim; not a line |

### 4.7 Repetition and imperfection (MAT_06 procedure)
**Repetition and imperfection**. Every surface of repeated units or tiled maps (glass block, brick, stone, tile,
curtain wall, mortar) gets randomness: no visible texture repeat, variation per unit (tint, roughness, pattern, small
tilt), and concave joints get dust, darkest in the corner and fading outward. Plan it into the first material pass;
perfectly regular units and razor-clean corners read as CG. How: materials/variation.md

| Requirement | Value |
|---|---|
| Per unit | tint, roughness, pattern, small tilt (§4.1) |
| Concave joints | dust, darkest in the corner, fading outward (edge-wear.md › Concave corners) |

### Generic layers
| Layer | Reference | Note for this material |
|---|---|---|
| Weathering shape, dust, cracks | [edge-wear.md](edge-wear.md) | gravity-shaped run-off, not isotropic noise |
| Previews and strength choice | [validation.md](../review/validation.md) | composite from one render |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Repeat visible along every joint | identical units with no per-unit key; feature-less or repeated map | per-unit key (§4.1); anti-tiling (§4.3) |
| Repeat shows at the rotated seams | UV rotation breaks the tangent-space normal map | drive relief from the height map through Bump (§4.3) |
| Rows in the same phase on the front wall | zero Z offsets on the lookup copies | vary both coordinates used by the projection (§4.3) |
| Grunge too weak in the render | noise set on the remap extremes; averaged or masked fields | normalise by the measured SD; set gain from the image (§4.5) |
| Grunge strength does not match the shader value | strength set on the shader parameter | measure each layer's multiplier on its AOV (§4.5) |
| Directional lines in weathering | board-formed, panel or brushed scan used as grunge | non-directional scan, check its preview (§4.5) |
| Weathering reads as smoke or blur | isotropic cloud noise | gravity-shaped run-off (§4.5, edge-wear.md) |
| Constant-width band or contour ring | fixed extent | slow noise that reaches zero; blob marks (§4.6) |
| Box-mapped surface looks wrong in relief | normal map used on a box projection | Bump from height (§4.4) |
| Perfectly regular units read as CG | no per-unit variation or corner dust | per-unit variation and joint dust (§4.7) |

Generic problems that often show up with this material, in troubleshooting.md.
