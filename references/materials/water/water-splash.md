# Water splash and the impact zone

## 1. Overview
Where falling water meets a pool: the landing line, crowns, splash drops, and (when a still is not
enough) a simulated plunge zone. Shared by [water-free-falling-film.md](water-free-falling-film.md),
[water-attached-film.md](water-attached-film.md) and fountains. Ripples from the impacts:
[water-ripple.md](water-ripple.md); foam and bubbles: [water-foam.md](water-foam.md).

## 2. Layers and node-editor diagram
Specific layers are described in §4. Generic layers are written once, in their own reference, and
used here with splash settings.

```
                          SPLASH AND THE IMPACT ZONE
 ┌──────────────────────────────────────────────────────────────────────────┐
 │ SPECIFIC (§4)                                                            │
 │   §4.1 Landing line and impacts         → one strength per impact        │
 │   §4.2 Crowns                           → thin-wall rings, strongest     │
 │   §4.3 Splash drops                     → drops from strong impacts      │
 │   §4.4 Simulated plunge zone            → optional, replaces procedural  │
 │ GENERIC (own reference)                                                  │
 │   Ripples from the impacts              → water-ripple.md                │
 │   Foam and bubbles                      → water-foam.md                  │
 └──────────────────────────────────────────────────────────────────────────┘
```

Flow:
```
   falling film bottom row + drops through its gaps (§4.1) ──► strength (local thickness / 90th percentile)
   strength ──► crowns (§4.2), splash (§4.3), ripples and foam (generic layers)
   §4.4 (when used) replaces the procedural foot: a short stretch, instanced along the line;
   film, crest and pool stay procedural
```

- One impact strength drives crater/crown size, crowns, foam and bubbles, and splash, so they
  cluster together, never as a regular array of identical elements.

## 3. Code
`scripts/blender/materials/water/`:
- `foot_impacts.py`: `impacts(lip, land_mid, land_keep, land_thick, drops, pool_z, p)` (§4.1).
- `foot_crowns.py`: `crowns(pts, strength, p)` (§4.2).
- `foot_splash.py`: `splash(lip, pts, strength, pool_z, p)` (§4.3).
- Parameters: `FootParams` in `foot_config.py`. The falling film calls these from `build.py`
  (`falling_film()`).

No script is named in this file for the simulated plunge zone (§4.4); the simulator it names is the
FLIP Fluids add-on. No control scene is named.

## 4. Instructions and parameters, per layer

### 4.1 Landing line and impacts
- **Take impacts from the water itself,** not a drawn line: the bottom row of the falling film
  (where it is water), weighted by local thickness, plus the drops falling through its gaps
  (weaker). The line is then as ragged as the throw, and heavy streams land harder.
- One impact strength drives crater/crown size ([water-ripple.md](water-ripple.md)), crowns, foam
  and bubbles ([water-foam.md](water-foam.md)) and splash — so they cluster together, never as a
  regular array of identical elements.

| Parameter | Value |
|---|---|
| Impacts | ~1 per 2 cm of landing line + one per drop reaching the pool (weaker) |
| Strength | local thickness / its 90th percentile, clipped 0.15–1.5 |

### 4.2 Crowns
- Clear water crowns standing up at the strongest impacts: a tilted ring with an irregular,
  spiky rim. Each one different in size, height and tilt.
- **Material: thin-wall water.** Open shells with a solid water material trap light and glow white.

| Parameter | Value |
|---|---|
| Share of impacts | strongest ~35 % |
| Radius / height | 6–20 mm / 3–14 mm, × strength |
| Rim | 14 segments, spikes up to +60 %, tilt ±0.3 rad |

### 4.3 Splash drops
- Drops thrown up and out from the strongest impacts (weight strength²), heights exponential,
  elongated with speed; none left sitting in the surface.
- Maximum height ≈ v²/2g of the splash speed (≈ 0.2 m at 2 m/s); typical mean a few cm.
- In soft light clear drops read **dark**, and dense low drops form a black band; drops sparkle only
  where they catch a bright reflection. Fewer, higher, spread.

| Parameter | Value |
|---|---|
| Count | ~40 per m of landing line |
| Size | 1–5 mm (median ~2 mm) |
| Height above the surface | exponential, mean ~3 cm |
| Throw from the wall | 0–12 cm |

### 4.4 Simulated plunge zone (when the still procedural foot is not enough)
- **Where simulation pays:** the plunge zone (splash, foam clumps, spray) in motion. Hybrid:
  simulate a short stretch (~1 m domain, 3–5 mm cells) with secondary particles (spray / foam /
  bubble), instance it along the line with random offsets and flips; keep film, crest and pool
  procedural. Method choice: [index.md](../index.md) › Water.
- **Thin-sheet inlets:** compute liquid thickness before choosing a domain: δ = q / V. If δ is
  below one voxel, a fully occupied one-cell source cannot preserve both speed and discharge: a
  q-matched source slows to V′ = q / dx; a speed-matched source over-discharges by dx / δ. State the
  deficit or excess; neither is a matched-physics benchmark.
- An oblique velocity also emits through the side faces of a source box: for a prism of width w in X
  with velocity in YZ, Q = w·(|vz|·dy + |vy|·dz). Align the source's extrusion axis with velocity,
  width transverse; geometry × speed is not the solver's injected volume — instrument it for a flux
  claim.
- Open domain sides drain a finite pool: measure far-field level drift. A perimeter reserve held at
  level approximates the surrounding pool; refilling the whole submerged domain also fills impact
  cavities. Record that boundary bias.
- A stitched slice needs an actual pool opening; extract the near-waterline boundary separately
  from the tall inlet curtain and detached spray. Clip particles to the same per-slice footprint as
  their water surface: overlapping mirrored copies make a false dense foam seam. Inspect joins in
  wide and close views.
- Matching a nonlinear wave function at shared grid vertices is insufficient after refining one
  side: intermediate points must interpolate the unchanged neighbour's boundary, or refine both.
- Bake completion does not prove settled flow: check stabilisation over several frames.
- FLIP Fluids add-on: verify the edition (the public demo release watermarks meshes). Houdini
  Apprentice is non-commercial and watermarked.

| Parameter | Value |
|---|---|
| Domain | ~1 m |
| Cell size | 3–5 mm |
| Secondary particles | spray, foam, bubble |
| Thin-sheet thickness | δ = q / V, compared with one voxel |
| Oblique side flux | Q = w·(|vz|·dy + |vy|·dz) |

Sources: [FLIP Fluids inflow settings](https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Inflow-Object-Settings),
[domain and open boundaries](https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Domain-Simulation-Settings),
[v1.8.8 demo limitations](https://github.com/rlguy/Blender-FLIP-Fluids/tree/v1.8.8#readme#readme). The
δ and projected-area formulas are continuity geometry, not solver guarantees.

Generic layers, splash settings:

| Layer | Reference | Note for this material |
|---|---|---|
| Ripples from the impacts | [water-ripple.md](water-ripple.md) | driven by the strengths of §4.1 |
| Foam and bubbles | [water-foam.md](water-foam.md) | impact parents from §4.1 |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Splash and bubbles in one array, same size and direction | elements placed along a fixed line at a fixed pitch | impacts from the water's landing (§4.1) |
| White glowing clumps at the foot | open crown shells with solid water | thin-wall crowns (§4.2) |
| Splash drops read as a dark band | many low clear drops in soft light | fewer, higher, spread (§4.3) |

Generic problems: `references/workflow/troubleshooting.md` (not linked from this file: a link here
would close a reference loop).
