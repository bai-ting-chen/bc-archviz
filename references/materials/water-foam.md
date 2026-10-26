# Water foam, bubbles and whitewater

Code: `water.foot.foam`, `water.foot.bubbles` (used by `water.build.falling_film`).

Aerated water on and in a pool: white foam flecks, clear floating bubbles, and dense milky
whitewater in plunge zones. Shared by every water material that lands in a pool
([water-free-falling-film.md](water-free-falling-film.md), [water-attached-film.md](water-attached-film.md)). Where the
impacts are: [water-splash.md](water-splash.md).

## 1. Foam flecks (surface)
- **Spawned at impacts, not along a band:** parents are impacts weighted by strength^0.4 (strong
  landings make more, but not all), so foam clusters without piling into white clumps.
- **Drift:** distance from the impact exponential; direction away from the wall with a spread;
  sideways drift grows with the distance travelled, so foam carries **past both ends of the fall**.
- **Shape:** irregular polygons (7–13 vertices, radius noise ±45 %), size lognormal, stretched
  along the drift the further they travel. Identical discs in a row read as fake at once.
- **Size from the final view** (RULES MAT_03): flecks under ~1 px vanish; at ~4–10 mm/px the
  median must be ~1 cm.
- Flat, just above the surface; material: off-white (~0.7), rough ~0.2, a short subsurface.

| Parameter | Value |
|---|---|
| Count | ~350 per m of landing line |
| Size | lognormal median ~1 cm, 1.5 mm–4 cm |
| Reach from the wall | exponential, mean ~18 cm |
| Sideways drift | σ = 3 cm + 0.5 × distance travelled |
| Stretch | 1 + Exp(0.8) × min(1, distance/0.1 m) |

## 2. Floating bubbles
- Clear domes sitting on the water, single or in small rafts; they travel much further than foam
  and give the scattered sparkle far from the fall.
- Dome = upper hemisphere squashed to ~0.85 of its radius, sunk ~20 % of the radius; material:
  thin-wall water (glints and rim, no bending).
- Spawned at impacts (weight strength^0.3), carried out with the same growing sideways drift.

| Parameter | Value |
|---|---|
| Count | ~600 per m of landing line |
| Diameter | 2–15 mm, median ~6 mm |
| Rafts | ~15 % of spawns, 3–11 bubbles, spread ~6 mm·√n |
| Reach | 5 cm + exponential mean 0.5 m (some past 1.5 m) |

## 3. Whitewater (plunge zones, trenches)
- **Optics:** a bubble cloud scatters σ_s ≈ 1.5·α / r (void fraction α, bubble radius r): 10 %,
  1 mm → 150 /m; 30 %, 0.5 mm → ~900 /m. Ten centimetres is optically thick: the floor of a
  churning trench never shows.
- **Render it as an opaque milky surface, not a volume.** A scattering volume in a shaded slot
  renders dark grey and slow. Use Burley subsurface (radius 3–4 cm) under a wet sheen (IOR 1.33,
  rough ~0.06), base around 0.35–0.45 albedo; foam (0.8, rougher, short radius) blended in as
  soft marbled streaks and lace; a few darker, less aerated streaks — never clear holes.
- **Never a hard foam switch.** Opaque white beside clear water over a dark trench reads as
  snow with black holes.
- **Fill below the surface.** An open water sheet over a void lets sight lines bent through
  adjacent glass end on the dark floor → a black band at the waterline. Put an opaque milky body
  just under the wave troughs (whitewater only; clear pools keep their clear body).
- **Bursts, not a uniform band:** one along-line "scallop" field (bursts every 0.15–0.6 m) drives
  foam width, boil height and splash density together.

## 4. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Foam in one line of identical discs | one band, one size | impact-spawned, lognormal, irregular (§1) |
| Foam invisible at the final view | sizes under a pixel | size from mm/px (§1) |
| Foam stops where the fall stops | no sideways drift | drift growing with distance (§1) |
| White clumps at strong impacts | crowns as open shells (light trapped), not foam | thin-wall crowns ([water-splash.md](water-splash.md)) |
| Only white foam, no sparkle far out | no floating bubbles | bubbles (§2) |
| Snow cones with black holes | hard foam switch over a dark trench | soft mask, milky body (§3) |
