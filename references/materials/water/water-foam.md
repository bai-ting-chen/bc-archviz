# Water foam, bubbles and whitewater

## 1. Overview
Foam, bubbles and whitewater in a pool. Where the impacts are: water-splash.md.

## 2. Layers and node-editor diagram
Specific layers are described in §4. The impacts that seed the flecks and bubbles are written once,
in their own reference, and used here with foam settings.

```
               WATER FOAM, BUBBLES, WHITEWATER — LAYER DIAGRAM
 ┌──────────────────────────────────────────────────────────────────────────┐
 │ SPECIFIC (§4)                                                            │
 │   §4.1 Foam flecks (surface)            → white flecks, drift past ends  │
 │   §4.2 Floating bubbles                 → clear domes, sparkle far out   │
 │   §4.3 Whitewater (plunge zones)        → opaque milky surface           │
 │ GENERIC (own reference)                                                  │
 │   Impacts: landing line, crowns, splash → water-splash.md                │
 └──────────────────────────────────────────────────────────────────────────┘
```

Flow:
```
   impacts (water-splash.md) ──► parents weighted by strength^0.4 (flecks, §4.1), strength^0.3 (bubbles, §4.2)
   flecks and bubbles ──► carried out with a sideways drift that grows with the distance travelled
   whitewater (§4.3) ──► bursts along the line drive foam width, boil height and splash density together
```

- Flecks and bubbles share the same impact parents and the same growing sideways drift, so the
  foam carries past both ends of the fall.
- Whitewater is the only milky layer. Clear pools keep their clear optical body.

## 3. Code
`scripts/blender/materials/water/`:
- `impact_foam.py`: `foam(lip, pts, strength, pool_z, p)` (flecks, §4.1).
- `impact_bubbles.py`: `bubbles(lip, pts, strength, pool_z, p)` (floating bubbles, §4.2).
- Parameters: `ImpactParams` in `impact_config.py`.

No script for whitewater (§4.3). Control: `scripts/controls/water/falling_film_check.py` builds flecks and
bubbles with the film.

## 4. Instructions and parameters, per layer

### 4.1 Foam flecks (surface)
- **Spawned at impacts, not along a band:** parents are impacts weighted by strength^0.4 (strong
  landings make more, but not all), so foam clusters without piling into white clumps.
- **Drift:** distance from the impact exponential; direction away from the wall with a spread;
  sideways drift grows with the distance travelled, so foam carries **past both ends of the fall**.
- **Shape:** irregular polygons (7–13 vertices, radius noise ±45 %), size lognormal, stretched
  along the drift the further they travel. Identical discs in a row read as fake at once.
- **Size from the final view** (RULES MAT_02): flecks under ~1 px vanish; at ~4–10 mm/px the
  median must be ~1 cm.
- Flat, just above the surface; a short subsurface.

| Parameter | Value |
|---|---|
| Count | ~350 per m of landing line |
| Size | lognormal median ~1 cm, 1.5 mm–4 cm |
| Reach from the wall | exponential, mean ~18 cm |
| Sideways drift | σ = 3 cm + 0.5 × distance travelled |
| Stretch | 1 + Exp(0.8) × min(1, distance/0.1 m) |
| Material | off-white (~0.7), rough ~0.2 |

### 4.2 Floating bubbles
- Clear domes sitting on the water, single or in small rafts; they travel much further than foam
  and give the scattered sparkle far from the fall.
- Dome = upper hemisphere squashed to ~0.85 of its radius, sunk ~20 % of the radius; material:
  thin-wall water ([water-surface.md](water-surface.md) §4.5).
- Spawned at impacts, carried out with the same growing sideways drift.

| Parameter | Value |
|---|---|
| Count | ~600 per m of landing line |
| Diameter | 2–15 mm, median ~6 mm |
| Rafts | ~15 % of spawns, 3–11 bubbles, spread ~6 mm·√n |
| Reach | 5 cm + exponential mean 0.5 m (some past 1.5 m) |
| Spawn weight | strength^0.3 |
| Dome | ~0.85 of radius, sunk ~20 % of radius |

### 4.3 Whitewater (plunge zones)
- **Optics:** a bubble cloud scatters σ_s ≈ 1.5·α / r (void fraction α, bubble radius r). Ten
  centimetres is optically thick: the floor under churning water never shows.
- **Render it as an opaque milky surface, not a volume.** A scattering volume in a shaded slot
  renders dark grey and slow. Use Burley subsurface under a wet sheen, foam (rougher, short radius)
  blended in as soft marbled streaks and lace; a few darker, less aerated streaks — never clear holes.
- **Never a hard foam switch.** Opaque white beside clear water over a dark floor reads as snow
  with black holes.
- **Milky below the surface too.** Whitewater is opaque in depth: put a milky body just under the
  wave troughs, so no sight line through the chop reaches a dark void (whitewater only; clear pools
  keep their clear body).
- **Bursts, not a uniform band:** one along-line burst field (every 0.15–0.6 m) scales the impact
  strength (water-splash.md §4.1), so foam width, boil height and splash density follow it together.
- The chop and boils under the whitewater are geometry: water-ripple.md §4.3.

| Parameter | Value |
|---|---|
| Scatter | σ_s ≈ 1.5·α/r; 10 %, 1 mm → 150 /m; 30 %, 0.5 mm → ~900 /m |
| Subsurface | Burley, radius 3–4 cm |
| Wet sheen | IOR 1.333, roughness ~0.06 |
| Base albedo | 0.35–0.45 |
| Foam albedo | 0.8 (rougher, short radius) |
| Burst spacing | 0.15–0.6 m |

Generic layers, foam settings:

| Layer | Reference | Note for this material |
|---|---|---|
| Impacts, crowns, splash | water-splash.md | the impact parents for §4.1 and §4.2; crowns are thin-wall |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Foam in one line of identical discs | one band, one size | impact-spawned, lognormal, irregular (§4.1) |
| Foam invisible at the final view | sizes under a pixel | size from mm/px (§4.1) |
| Foam stops where the fall stops | no sideways drift | drift growing with distance (§4.1) |
| Only white foam, no sparkle far out | no floating bubbles | bubbles (§4.2) |
| Snow cones with black holes | spiky short boils and a hard foam switch over a dark floor | rounded chop (`references/materials/water/water-ripple.md`), soft mask, milky body (§4.3) |
| Dark band or holes through the troughs | sight lines through the chop reach a dark void | milky body under the troughs (§4.3); a clear pool keeps its clear body |

Generic problems: `references/workflow/troubleshooting.md` (not linked from this file: a link here
would close a reference loop).
