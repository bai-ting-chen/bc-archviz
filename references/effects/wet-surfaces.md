# Wet Surfaces

## 1. Overview
A surface wet with a thin film of water. The water body itself: water-surface.md.

## 2. Layers and node-editor diagram
Specific layers are described in §4. Generic layers are written once, in their own reference.

```
                          WET SURFACES — LAYER DIAGRAM
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ SPECIFIC (§4)                              GENERIC (own reference)        │
 │ 1 Wet look   → colour, roughness, coat     Water body → water-surface.md  │
 │ 2 Wet extent → mask for layer 1            Patchy extent → RULES MAT_05   │
 └───────────────────────────────────────────────────────────────────────────┘
   wet extent (2) ─► mask 0–1 ─► mixes dry and wet values
   dry albedo ─► 1 dry^gamma ─► Base Color;  roughness and water coat ─► Principled
```

- **Mask and look:** layer 2 decides where, layer 1 how wet it looks. A material that is wet all over (a lawn
  after rain) uses layer 1 with a soft patch noise as its mask.

## 3. Code
- Wet look, grass blades: `materials.vegetation.vegetation.blade_material(wet=WET)` (gamma, water coat, soft
  patch mask).
- Wet look, soil: `materials.ground.ground.ground_material(wet_gamma=1.4)` darkens the whole ground and
  multiplies its roughness by `wet_rough` (0.6). It adds no coat and no mask: damp soil, not a water film.
- Other materials: the Gamma node and coat values of §4.1 on their own Principled.
- Wet extent behind falling water: `scripts/blender/materials/water/wet.py` (`materials.water.wet`),
  `proxy(lip, pool_z, WetParams)`; `build.falling_film(wet_proxy=...)` replaces the proxy mesh in place.
- No builder for a wet band along a standing water edge: it is node graph only (§4.2).
- Controls: `scripts/controls/material/vegetation_graph_check.py` and `ground_graph_check.py` (wet cases),
  `scripts/controls/water/water_numeric_check.py` (the proxy).

## 4. Instructions and parameters, per layer
### 4.1 Wet look
- Why: light reflects inside the water film and is absorbed again, so wet reads darker, more
  saturated and glossier (Lekner & Dorf 1988; Jensen et al. 1999).
- Colour: wet = dry ** gamma (Gamma node). Albedo falls non-linearly: a bright surface darkens less than a
  dark one, which a plain multiply cannot do.
- A water film on top: Principled coat, IOR 1.33.
- A wet lawn from a low camera is mostly grazing angles: the film reflects the sky and greys the grass out. That
  sheen is right; a higher gamma (~1.7) keeps the lawn reading as wet.

| Parameter | Value |
|---|---|
| Gamma, soil and stone | ~1.4 (1.8 turns a warm white beige-brown and reads as dirt) |
| Gamma, grass | ~1.7 |
| Roughness, wet stone | ~0.1 |
| Water coat | Principled coat, IOR 1.33, roughness ~0.03 (grass 0.08) |

### 4.2 Wet extent
- **Wet where the water reaches, not where it is near.** Measure the mask on the wet surface itself, from the
  place the water lands or touches:
  - a standing water edge (pool coping, basin rim): distance from the edge. For an arc edge use the analytic
    distance d = R − |P.xy − C|, which needs no mesh density;
  - falling water in front of a wall: the sheet stands off the wall (tens of cm at the foot), so distance to the
    water leaves the wall behind it dry. Use a proxy mesh lying on the wall face over the whole footprint of the
    fall (`water.wet.proxy`); behind the water everything is wet from spray, run-down and condensation.
- **Ragged edge (RULES MAT_05).** A slow noise along the edge drives the wet width, down to negative (dry). Behind
  falling water the wet edge wanders past each end of the fall, with run-off fingers hanging from the top near
  the ends. A constant-width band or a straight wet/dry line is a rigid tell.
- **Splash fades with distance.** Splash drops (Voronoi) thin out away from the water. Above a pool the splash
  band is low and fades past both ends of the fall; it never covers the whole wall.
- **Gate by height** so canopies and far floors stay dry.
- Dried marks and tide rings: [surface-wear.md](surface-wear.md) §4.3.
- Keep the proxy a plain hidden mesh referenced by the wetness GN and replace its mesh data in place. Deleting
  the object empties every reference and the noise term draws blotches.

| Parameter | Value |
|---|---|
| Arc edge distance | d = R − \|P.xy − C\| |
| Wet width along an edge | slow noise; negative = dry |
| Wet edge past each end of a fall | 5–30 cm, changing with height |
| Splash band above the pool | 0.2–0.6 m, varying along the wall |
| Splash fade past each end of a fall | e-fold ~0.45 m |

### Generic layers
| Layer | Reference | Note for this material |
|---|---|---|
| Water body (pool, clear water) | water-surface.md | the wet surfaces are here; the water itself is there |
| Patchy extent of wet | RULES MAT_05 | slow noise that reaches zero (§4.2) |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Wet colour reads as dirt, beige-brown | gamma too high (1.8) | gamma ~1.4 (§4.1) |
| Wet lawn goes silvery-grey, loses saturation | grazing-angle sheen of a grey sky | gamma ~1.7 keeps the wet reading; the sheen itself is right (§4.1) |
| Wall behind falling water stays dry | mask from distance to the water; the sheet stands off the wall | proxy on the wall face over the whole footprint (§4.2) |
| Constant-width band, or a straight wet/dry line | wet width fixed | slow noise drives the width; wander and run-off fingers at the ends (§4.2) |
| Whole wall wet | splash not limited | low splash band, fading past the ends (§4.2) |
| Dried marks read as contour lines | marks drawn as lines | surface-wear.md §4.3 |
| Canopies or far floors wet | no height gate | gate by height (§4.2) |
| Blotches in the wetness noise term | proxy object deleted, references emptied | replace the proxy's mesh data in place (§4.2) |

Generic problems that often show up with this material, in troubleshooting.md.
