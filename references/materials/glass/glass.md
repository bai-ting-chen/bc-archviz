# Glass

## 1. Overview
Glass in five cases: the clear glazing base (transmission, IOR, roughness), the optical distortion of
glazing (roller waves and pillowing), cast glass relief, pressed glass block walls, and liquid in
glass. The first three are layers of one pane; the block and the liquid are objects of their own.
Glass under a water film is covered by [water-attached-film.md](../water/water-attached-film.md).

## 2. Layers and node-editor diagram
Specific layers are described in §4. Generic layers are written once, in their own reference, and
used here with glass settings.

```
                                GLASS
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ PANE (one glazed pane)                                                    │
 │ 1 Clear glazing base    → transmission, IOR, roughness                    │
 │ 2 Roller waves, pillow  → bump                                            │
 │ 3 Cast relief           → relief (folds, creases, crinkle)                │
 │                                                                           │
 │ OBJECTS (own geometry)                                                    │
 │ 4 Glass block units     → geometry (two pressed halves, sealed)           │
 │ 5 Liquid in glass       → three surfaces (glass, interface, water)        │
 └───────────────────────────────────────────────────────────────────────────┘
   pane: base (1) ─► Principled transmission and IOR; roller wave + dome (2) ─► Bump
   cast relief (3) ─► tiles, faded at the border ─► relief over the untouched body
   block (4) and liquid (5): built as geometry; no shader layer stack
```

- Assembly, pane: the cast relief (§4.3) is built tile by tile, each tile its own cast, so the grid
  meets the untouched body at a faded border.
- Assembly, block and liquid: each is its own object, separate from the pane layers above.

## 3. Code
- `scripts/blender/materials/glass/`: `glass.py` (module `materials.glass.glass`),
  `glass_distortion.py` (`glass_distortion(mat, obj)`), `glass_assembly.py` (`glass_of_water`),
  `glassware.py` (`glassware.glass_of_water()`).
- Glass block units: no script is named in this file.
- Control: none named in this file.

## 4. Instructions and parameters, per layer

### 4.1 Clear glazing base
- Principled transmission 1, IOR 1.52, roughness 0. Thin Film for coated glazing (to try).

| Parameter | Value |
|---|---|
| Transmission | 1 |
| IOR | 1.52 |
| Roughness | 0 |
| Thin Film | for coated glazing (to try) |

### 4.2 Roller waves and pillowing (bump)
- Glazing is not optically flat. Float glass has roller waves (~0.1 mm peak-to-valley over ~0.3 m,
  ~1 mrad slope). The visible wobble of real windows is insulated-unit **pillowing**: panes bowed a few
  mm, strongest towards the frame.
- `materials.glass.glass.glass_distortion(mat, obj)` gives a bump of a sine roller wave plus a dome over
  the pane. 0.25 mm of wave read as blinds; the dome carries the effect.
- A glass that "looks too reflective" is usually a dark room behind it. Fresnel is physical; distortion
  and something to reflect make it read.

| Parameter | Value |
|---|---|
| Roller wave | ~0.1 mm peak-to-valley over ~0.3 m; ~1 mrad slope |
| Pillowing | panes bowed a few mm, strongest towards the frame |
| Wave amplitude | 0.25 mm read as blinds; the dome carries the effect |

### 4.3 Cast glass relief
- Multi-scale: soft folds λ 8–40 cm, ridged creases, and very weak crinkle. Each tile has its own cast,
  faded flat over ~30 mm at the border so the grid meets the untouched body.
- Strong fine crinkle reads as squiggles.
- A slight roughness on the dry faces gives the satin haze of cast glass.
- Sized for the final view (RULES MAT_03).

| Parameter | Value |
|---|---|
| Soft folds | λ 8–40 cm |
| Creases | ridged |
| Crinkle | very weak |
| Border fade | ~30 mm, flat |
| Dry-face roughness | ~0.05 |

### 4.4 Glass block units (geometry)
- Pressed hollow unit: two pressed halves fused hot and sealed hollow (partial vacuum). The pattern is
  on the **inner** faces; outer faces are smooth with slight pressing waviness; coated sides key to the
  mortar.
- Common units 190×190×80 mm (2.3 kg) and 240×240×80 (4.1 kg): from the weight, ~8 mm face glass and
  ~7 mm sides.
- Stack bond, 10 mm joints, perimeter bands ≥ 15 mm, panels ≤ ~15 m².
- Curved walls: the concave-side joint stays constant and the convex one opens, E = (L + g)(1 + s/r) − L.
  With g 10 / E 25 mm, the inner radius is ≥ ~1.05 m (190 units), ≥ ~1.33 m (240).
- Model the relief as geometry (caustics.md › Designing a refractive relief). Leave a fraction of a
  millimetre of air between mortar and glass so the surfaces never coincide.

| Parameter | Value |
|---|---|
| Unit sizes | 190×190×80 mm (2.3 kg); 240×240×80 mm (4.1 kg) |
| Face / side glass | ~8 mm / ~7 mm (from the weight) |
| Bond and joints | stack bond, 10 mm joints |
| Perimeter band | ≥ 15 mm |
| Panel area | ≤ ~15 m² |
| Joint on a curve | E = (L + g)(1 + s/r) − L; g 10 / E 25 mm |
| Minimum inner radius | ≥ ~1.05 m (190); ≥ ~1.33 m (240) |
| Mortar-to-glass gap | a fraction of a millimetre |

### 4.5 Liquid and glassware
- Cycles has no nested-IOR priority, so model three surfaces: GLASS (1.52), INTERFACE below the
  waterline (1.52/1.333) and WATER_SURFACE (1.333), built by `glassware.glass_of_water()`. Check the
  normals per wall.
- Re-lathe Rhino glassware at a high segment count for close-ups.

| Parameter | Value |
|---|---|
| GLASS | IOR 1.52 |
| INTERFACE below the waterline | IOR 1.52/1.333 |
| WATER_SURFACE | IOR 1.333 |
| Glassware segments | high count for close-ups |

### Generic layers, glass settings
| Layer | Reference | Note for this material |
|---|---|---|
| Glass under a water film | [water-attached-film.md](../water/water-attached-film.md) | wetted face IOR 1.14 |
| Refractive relief design | caustics.md › Designing a refractive relief | glass block relief is modelled as geometry (§4.4) |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Glass looks too reflective | dark room behind it | Fresnel is physical; add distortion and something to reflect (§4.2) |
| Pane reads as blinds | roller wave too strong (0.25 mm) | let the dome carry the effect (§4.2) |
| Cast glass reads as squiggles | strong fine crinkle | keep the crinkle very weak (§4.3) |
| Cast glass has no satin haze | dry faces fully glossy | slight roughness on the dry faces (§4.3) |
| Hard tile edge on cast glass | no border fade | fade flat over ~30 mm at the border (§4.3) |
| Block mortar and glass flicker or z-fight | surfaces coincide | leave a fraction of a millimetre of air (§4.4) |
| Curved block joints wrong | convex joint not opened | E = (L + g)(1 + s/r) − L; check the inner radius (§4.4) |
| Water in glass looks wrong at the waterline | nested IOR not handled | three surfaces: glass, interface, water (§4.5) |
| Glassware faceted in close-up | low segment count | re-lathe at a high count (§4.5) |

No generic problems are listed in this file. The general list is in troubleshooting.md (named here,
not linked, so this file adds no reference loop).
