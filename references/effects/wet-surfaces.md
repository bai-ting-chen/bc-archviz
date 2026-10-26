# Wet Surfaces

## 1. Overview
Wet = darker and more saturated (internal reflection in the film, Lekner-Dorf): albedo becomes dry^gamma
(1.4 for soil/stone; grass reads better at ~1.7) plus a water coat (IOR 1.33). This file covers the wet
surround (pool coping, splash zone), dew on plants, and the wet wall behind falling water. The water body
itself is in the water reference (water-surface.md).

**Use when:** a surface beside or behind water is wet (coping, splash zone, the wall behind a falling sheet),
or dew sits on plants. The water body itself: water-surface.md.

## 2. Layers and node-editor diagram
Specific layers are described in §4. Generic layers are written once, in their own reference.

```
                           WET SURFACES
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ SPECIFIC (§4)                              GENERIC (own reference)        │
 │ 1 Wet albedo and coat → colour, roughness  Water body → water-surface.md  │
 │ 2 Dew beads and sheen → glossy beads                                      │
 │ 3 Wet surround        → wet mask, edge     Patchy extent → RULES MAT_05   │
 │ 4 Wet wall proxy      → wet mask on wall                                  │
 └───────────────────────────────────────────────────────────────────────────┘
   dry albedo ─► 1 dry^gamma + coat ─► wet albedo and roughness
   wet mask (3, 4) ─► decides where the wet values apply
   dew beads (2) ─► on broad leaves and grass, faded by camera distance
```

- **Mask and colour:** the wetness masks (3, 4) decide where; layer 1 sets how wet a surface looks.
- **Dew:** layer 2 adds beads only where the camera can resolve them (§4.2).

## 3. Code
- `scripts/blender/materials/vegetation/`: `blade_config.py` holds `DEW_GRASS` and `DEW_BROAD`; imported as
  `materials.vegetation.vegetation`.
- `scripts/blender/materials/water/wet.py` (`materials.water.wet`): `proxy(lip, pool_z, WetParams)`, the wet-wall
  proxy behind falling water (§4.4).

## 4. Instructions and parameters, per layer
### 4.1 Wet albedo and water coat
- Wet = darker and more saturated (internal reflection in the film, Lekner-Dorf): albedo → dry^gamma (1.4 for
  soil/stone; grass reads better at ~1.7) + a water coat (IOR 1.33).

| Parameter | Value |
|---|---|
| Gamma, soil and stone | 1.4 |
| Gamma, grass | ~1.7 |
| Water coat IOR | 1.33 |

### 4.2 Dew beads and grazing sheen
- A wet lawn seen from a low camera is mostly grazing angles: the film's Fresnel sheen of a grey sky greys it out
  (saturation drops). A darker base keeps the "wet" reading; the sheen is physically right (dewy lawns look
  silvery under fog).
- Dew beads are sub-pixel beyond a few metres (1 mm at 4 m < 1 px at 2400 px): their sum is the sheen. Near the
  camera they read only where large — broad waxy leaves (clover) hold 2–5 mm beads.
- Under an even sky a bead is bright through refraction + total reflection inside it, not its ~4 % surface
  reflection: a coat-only bead bump was invisible even at 0.4 m. Model them as effective-reflectance glossy beads
  (declared approximation), faded with camera distance (`DEW_GRASS`, `DEW_BROAD`). The denoiser smooths isolated
  sub-pixel glints, so size and density must carry them.

| Parameter | Value |
|---|---|
| Bead size, grass at 4 m | 1 mm (sub-pixel at 2400 px) |
| Bead size, broad leaves (clover) | 2–5 mm |
| Bead model | effective-reflectance glossy; faded with camera distance |
| Base | darker base keeps the wet reading at grazing angles |

### 4.3 Wet surround (pool coping, splash zone)
- Wet porous albedo falls non-linearly and saturates (Lekner & Dorf 1988; Jensen et al. 1999) → wet colour =
  dry ** ~1.4 (Gamma node; 1.8 turns a warm white beige-brown and reads as dirt), roughness ~0.1, plus a water film
  as Principled coat (IOR 1.33, rough ~0.03).
- When the edge is an arc, mask by the analytic distance d = R − |P.xy − C| (no mesh density).
- Ragged splash band by noise-pushed d, Voronoi drops thinning with d, faint darker tide rings beyond, scum band at
  the waterline on vertical faces.
- Gate by height so canopies and far floors stay dry.
- Patchy, never a band (RULES MAT_05): drive the band width with a slow noise along the edge (down to negative =
  dry), and make dried marks blobs darker at their rim (coffee-ring) rather than contour lines.

| Parameter | Value |
|---|---|
| Colour | dry ** ~1.4 (1.8 reads as dirt) |
| Roughness | ~0.1 |
| Water coat | Principled coat, IOR 1.33, rough ~0.03 |
| Edge distance | d = R − \|P.xy − C\| |
| Band width | driven by slow noise; negative = dry |

### 4.4 Wet wall behind falling water
- **Wet where the water is, not where the film is near.** A free-falling sheet stands off the wall (tens of cm at
  the foot), so a wetness mask from distance-to-film leaves the wall behind the lower curtain dry. Drive it from a
  proxy lying **on the wall face** over the curtain's whole footprint (behind the water, everything is wet: spray,
  run-down and condensation).
- **Ragged ends:** the wet edge wanders past each end of the curtain (5–30 cm, changing with height), with runoff
  fingers hanging from the top near the ends. A straight vertical wet/dry line is a rigid tell.
- **Splash band:** a low band above the pool (0.2–0.6 m, varying along the wall) fading out past both ends of the
  fall (e-fold ~0.45 m). Not the whole wall (RULES MAT_05: patchy, physically shaped).
- Code: `water.wet.proxy(lip, pool_z, WetParams)`.
- Keep the proxy a plain hidden mesh referenced by the wetness GN; replace its mesh data in place (never delete the
  object, or every reference goes empty and the noise term draws blotches).

| Parameter | Value |
|---|---|
| Splash band height | 0.2–0.6 m, varying along the wall |
| Fade past each end of the fall | e-fold ~0.45 m |
| Wet edge wander | 5–30 cm past each end, changing with height |
| Runoff fingers | hanging from the top near the ends |
| Proxy | plain hidden mesh; replace mesh data in place |

### Generic layers
| Layer | Reference | Note for this material |
|---|---|---|
| Water body (pool, clear water) | water-surface.md | the wet surround is here; the water itself is there |
| Patchy extent of wet, stains, dried marks | RULES MAT_05 | slow noise that reaches zero; blob marks (§4.3) |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Wet lawn goes silvery-grey, loses saturation | grazing-angle Fresnel sheen of a grey sky | darker base keeps the wet reading; the sheen itself is right (§4.2) |
| Dew invisible, or isolated glints smoothed away | sub-pixel beads; the denoiser smooths isolated glints | size and density carry them; effective-reflectance beads (§4.2) |
| Coat-only bead bump invisible, even at 0.4 m | bright through refraction and total reflection inside the bead | effective-reflectance glossy beads (§4.2) |
| Wet colour reads as dirt, beige-brown | gamma too high (1.8) | gamma ~1.4 (§4.3) |
| Wall behind the lower curtain stays dry | wetness from distance-to-film; the sheet stands off the wall | proxy on the wall face over the whole footprint (§4.4) |
| Straight vertical wet/dry line | no wander at the curtain ends | ragged ends, runoff fingers (§4.4) |
| Whole wall wet | band not limited to the splash zone | splash band 0.2–0.6 m, fading past the ends (§4.4) |
| Constant-width band or ring at the edge | band width fixed | slow noise drives the width; blob marks (§4.3) |
| Dried marks read as contour lines | marks drawn as lines | blobs darker at their rim (§4.3) |
| Canopies or far floors wet | no height gate | gate by height (§4.3) |
| Blotches in the wetness noise term | proxy object deleted, references emptied | replace the proxy's mesh data in place (§4.4) |

Generic problems that often show up with this material, in troubleshooting.md.
