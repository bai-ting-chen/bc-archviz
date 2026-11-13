# Wood

## 1. Overview
Solid wood and veneer: boards, cladding, battens, floors, furniture. A wood material has three layers:
the base wood, an optional coat on top, and an optional under-layer that chipping exposes.

## 2. Layers and node-editor diagram
```
 +-- WOOD — LAYER DIAGRAM ------------------------------------------------+
 | SPECIFIC                                                               |
 | 4.2 Coat (optional)        → varnish, oil or lacquer on top            |
 | 4.1 Base wood              → grain colour, roughness, normal           |
 | 4.3 Under-layer (optional) → raw wood or particle board, seen in chips |
 | GENERIC                                                                |
 | wear/wear.md               → dirt, scratches, water marks, chipping    |
 | variation-macro-tone.md    → macro tone: colour                        |
 +------------------------------------------------------------------------+
```
Base maps → Principled Base Color / Roughness / Normal; the coat is the same BSDF's Coat inputs.
Chipping masks → coat worn off (base shows) or wood broken (under-layer shows).

## 3. Code
All in `scripts/blender/materials/wood/wood.py` (`materials.wood.wood`):
- `coated_wood()`: base and coat (§4.1, §4.2).
- `raw_wood_under(graph, color, normal)`: the raw-wood under-layer shader (§4.3).
- `weathered_wood()`: coated wood + worn coat and grime on the arrises + `raw_wood_under` where chipped.
- `WOOD_CHIPS`: wood settings for the shared chip group,
  `effects.wear.add_edge_wear(obj, edge_wear_group(**WOOD_CHIPS))`: dents and grain-wise breaks
  (`GrainBreaks`) that write the `chip` and `break` attributes the shader reads. Run it on a rounded
  mesh (`effects.wear.round_geometry`). Control: `scripts/controls/material_graph_check.py` topic `wood_wear`.
- No particle-board under-layer builder yet: pass it as the `under_shader` of the chipping layer
  ([chipping.md](../../effects/wear/chipping.md)).

## 4. Instructions and parameters, per layer

### 4.1 Base wood
- Use the species' scanned maps at real size, levels solved to a natural albedo
  ([physical-ranges.md](../physical-ranges.md)).
- Grain follows the boards: `archviz.directional_uv(obj, tex_size_m, axis)`; `along="V"` when the map's
  grain runs up the image.

| Parameter | Value |
|---|---|
| Roughness | the map's, spread toward matte (`rough_toward_matte`) |
| IOR | 1.5; do not lower it to fake a duller look |
| Edges | rounded geometry, not only a shaded bevel |

### 4.2 Coat (optional)
- Leave it off for raw, oiled-matte or weathered wood.
- Satin varnish is a low coat weight with tight coat roughness, not a strong rough coat.
- Battens, veneers and dark floors seen at a low angle usually want a matte coat or none: a glossy
  coat mirrors lenses as halos and turns a dark floor light grey at grazing angles (Fresnel).

| Parameter | Satin starting value |
|---|---|
| Coat weight | ~0.2 |
| Coat roughness | ~0.04 |
| Coat IOR | 1.5 |
| Coat › Normal | can stay smooth over the bumped wood |

### 4.3 Under-layer (optional)
- What a chip or break exposes: raw wood for solid timber, particle board for veneer.
- Raw wood is the same grain, lighter and a little yellower than the coated base, rough, with fine
  torn fibres along the grain; it is not a flat tint.
- Wood breaks run along the grain: stretch the break noise along the board's long axis (`grain_stretch`).
- The break share responds steeply: a little reads as wear, a little more as damage. Bisect it in a render.

| Parameter | Raw-wood starting value |
|---|---|
| Colour | base ×~1.7, mixed ~0.3 toward raw tint (0.80, 0.60, 0.36) |
| Roughness | ~0.85 |
| Break share | bisect from 0.5 |

### Generic layers, wood settings
| Layer | Reference | Note for this material |
|---|---|---|
| Wear family | [wear.md](../../effects/wear/wear.md) | dirt (hand grime on worn edges), scratches, water marks |
| Chipping | [chipping.md](../../effects/wear/chipping.md) | shared chip group with `WOOD_CHIPS` (§3) and the under-layer (§4.3) |
| Macro tone | [variation-macro-tone.md](../../effects/variation-macro-tone.md) | vary base colour across the surface |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Satin varnish looks plasticky | strong, rough coat | low weight, tight roughness (§4.2) |
| Grain runs across the boards | grain along V not set | `along="V"` (§4.1) |
| Halos on battens; dark floor reads grey at a low angle | glossy coat | matte coat or none (§4.2) |
| Chips read as flat pale spots | under-layer is a flat tint | keep the grain and fibres (§4.3) |
| Worn wood reads as damaged | break share too high | bisect the break share (§4.3) |

Generic problems that show up in any material are in troubleshooting.md.
