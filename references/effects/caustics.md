# Caustics

## 1. Overview
Caustics are the light patterns a refractor focuses onto a receiver: sun through glass, a pool or
patterned glass. Choose the method by the case below (RULES REN_02, REN_03), say which and why, then
build and check it (§4). The engine rules are in `references/renderer/renderer-choice.md`; the
glass-block wall that carries a relief is in `references/materials/glass/glass.md`.

### Choosing the method
| Case | Method | Why |
|---|---|---|
| Large light source, any refractor | Cycles path tracing | unbiased; converges when the key subtends a real angle, never for a sun-sized source |
| Lamps above calm water, submerged surfaces | MNEE (step 3c) | cheap and clean, but under-delivers energy and ignores volumes on the light leg |
| Sun through a rippled pool | GN wavefront (step 3b) | native, exact, noise-free; MNEE fails on real ripples |
| Sun through glassware | LuxCore (step 3a); photon bake (step 3d) only when the scene must stay in Cycles | photons were the best Cycles-side option on a measured shadow/lit ratio |
| Sun through patterned glass, glass block, several interfaces; room-scale receivers | LuxCore (step 3a) | unbiased, energy-correct; the only engine that converged (step 1) |

Fallback, declared (RULES REN_02): fakes (Voronoi textures, gobo area lights, shadow-ray Transparent).
Untested: Caustica, Reblend (photon caustics in Cycles builds), Octane.

## 2. Layers and node-editor diagram
```
 ┌─ CAUSTICS — PROCEDURE DIAGRAM ───────────────────────────────────────────┐
 │ Choose   case table (§1); rerun the comparison for an unlike scene       │
 │   ▼                                                                      │
 │ Relief   patterned glass only: size it from the receiver distance        │
 │   ▼                                                                      │
 │ Build    ┬─ LuxCore PATH + light tracing ─► the render itself            │
 │          ├─ GN wavefront sheet ─► emissive overlay above the receivers   │
 │          ├─ MNEE flags ─► Cycles shadow caustics                         │
 │          └─ photon bake ─► emission in the receiver's material           │
 │   ▼                                                                      │
 │ Check    energy against a Transparent-glass baseline; pattern face-on    │
 └──────────────────────────────────────────────────────────────────────────┘
```
- Off switches: `render_variant.py caustics=off` (MNEE flags and Cycles refractive caustics) or
  `mnee=off`; hide the `CAUSTIC_SHEET` object; `add_caustic_light(…, scale=0)`.

## 3. Code
- GN wavefront: `scripts/blender/effects/caustics/gn_caustics.py`:
  `add_caustic_sheet(caster, receivers, occluders, sun_obj, ior=…, floor_tex=…, floor_albedo=…)`.
- Photon bake: `scripts/blender/effects/caustics/caustic_photons.py`: `export_geometry`, `trace`
  (command line), `bake_irradiance`, `add_caustic_light`; the stages are in step 3d.
- MNEE: water caster `materials.water.water.water_surface`, glassware
  `materials.glass.glassware.glass_of_water_mnee`; control `scripts/controls/water/mnee_water.py`.
- LuxCore: `renderer.luxcore.engine.engine_setup` ([luxcore.md](../renderer/luxcore.md)).
- Relief: no builder; modelled geometry (step 2).
- Regression: `scripts/controls/regression/stage_b_graph_check.py` (sheet graph, overlay, photon stages).

## 4. Instructions and parameters
### Step 1. Choose the method
- Take the §1 row; record the method and why in the study notes.
- **Measured** (sun 0.53° → 4 glass interfaces with a wavy relief → diffuse floor, equal 120 s, against
  a 900 s reference): LuxCore light tracing 18 % relative error, −0.5 % bias; LuxCore GPU caustic cache
  40 % (−24 % bias, blur); LuxCore BIDIR 105 % (noise); Cycles path tracing ~1000 %; Cycles CPU path
  guiding ~3500 % (fireflies only); MNEE −82 % (gives up after one interface).
- **Rerun the comparison** when the scene is unlike this one:
  1. Calibrate: the real refractor beside an identical empty opening. Its sunlit patch matches units
     between engines and is the energy baseline.
  2. Time: equal wall-clock per engine on its own device, one job at a time (a second job distorts
     timings); a long run of the best candidate is the reference.
  3. Score: relative RMSE and bias per region (caustic, glass seen from inside, wall).

| Parameter | Value |
|---|---|
| Calibration (empty opening across engines) | within a few % |
| Timing | equal wall-clock, one job at a time |
| Score | relative RMSE and bias per region |

### Step 2. Design the relief (patterned glass, glass block, wavy acrylic)
- **Model it as geometry.** MNEE ignores bump and normal maps; in LuxCore a normal map bends the caustic
  but gives dark seams and no parallax (luxcore.md).
- **Each curved patch is a lens:** f ≈ 1 / ((n − 1)·κ), with κ ≈ A(2π/λ)² for amplitude A and
  wavelength λ. The network is sharpest at one to a few focal lengths; far beyond, patches overlap into a
  flat glow. Size the relief from the receiver distance (1.5–3 m in a room) for one of the looks below.
  From inside the glass still reads rippled: 0.5° moves a tree 30 m away by 25 cm.
- **One frequency draws fold lines.** A sine sends most of its light to its maximum deflection: one bright
  line per ridge set, repeated per tile. Sum ~12 waves instead: random direction, log-uniform λ, amplitude
  ∝ λ^0.8, a slow depth envelope (1 ± 0.45), scaled to the target RMS slope; a mild vertical stretch reads
  as poured glass.
- **Preview in numpy first:** deflection = (n − 1)∇h per face, land at x + D·θ, histogram, blur by the
  sun's angular size; seconds per D. Over a 6×6 patch of units measure the share of light landing outside
  its own unit (tangling) and p99/mean (line contrast).
- **Pattern families** (trade names Wave, Iceberg, Bubble, Diamond, Pristal, Quadra):
  - *Wave*: a few long cosines. Horizontal crests throw vertical streaks, diagonal crests cross into
    loops; mixing both 1:1 across the wall breaks any single direction.
  - *Iceberg*: ridged noise, h = −√(f² + (0.08·rms)²) of a sum of broad cosines; crisp crossing lines.
  - *Diamond, Pristal, Quadra*: prisms, sharp-edged repeating patches.
- **Straight features draw straight lines.** Rounded block edges, cavity corners and the fade to the
  border are cylindrical lenses; one that focuses at the receiver casts a thin streak. Fade over ≥ 25 mm
  (shorter lenses into bright square outlines) and use larger radii.
- **Lay tilt varies reflections, not caustics:** a hollow block's two parallel faces shift its light by
  millimetres. Vary the caustics through the relief.
- **Variants:** ~16 reliefs as block definitions, placed at random with 180° turns and flips (64 looks),
  instanced. Instanced relief is cheap to trace (flat boxes only 1.1–1.3× faster, luxcore.md).

| Look | λ | Slope | Notes |
|---|---|---|---|
| Separate patches | 40–150 mm | RMS ≈ 0.015–0.02 | each unit's light stays in its footprint; a grid of rippled squares |
| One tangled net | 120–400 mm | ≈ 0.04; 3–5 mm peak to peak in a 190 mm block | 20–40 % of each unit's light lands outside it at 2–3 m; lines stay sharp |
| Short waves (avoid) | < 100 mm | 0.17 | focuses within centimetres; grey mush by 2 m |

### Step 3. Build
- **Light, every method:** the HDRI's own sun (RULES LGT_02); choose the map by its sun share
  (lighting-camera.md › Pick the HDRI by its sun). The fill sets the contrast between caustic and
  surface: a clearer, bluer map (higher sun share) separates them far more than a material or grade does.

#### 3a. LuxCore
- PATH with light tracing, GPU camera paths + CPU light tracing; setup in [luxcore.md](../renderer/luxcore.md).
- *Use CPUs* on: light tracing runs on CPU threads, so without them the GPU renders no caustic.
- Glints through the glass from the camera side come from the HDRI sun. In a control without an HDRI use
  a LuxCore `sun` lamp, not `distant`, which camera rays cannot hit.

#### 3b. GN wavefront (`add_caustic_sheet`)
- Each water vertex refracts the sun (Vector Math Refract, 1/IOR) and is raycast onto the receivers and
  to the sun for shadow. Each face carries E = E_sun·T·A_perp / A_landed, blurred to the sun's angular
  size, shown by a transparent emissive overlay of albedo·E/π.
- One refraction (exact for a pool), constant T, matte receivers only.
- Check: the sheet's integrated irradiance equals E_sun·cos θ over its area.

| Parameter | Value |
|---|---|
| `ior` | 1.333 (water) |
| `floor_albedo` or `floor_tex` | the receiver's real albedo or its texture |
| `transparent_max_bounces` | high when overlays stack |

#### 3c. MNEE
- Flags: `obj.cycles.is_caustics_caster`, `is_caustics_receiver`, `light.cycles.is_caustics_light`.
- The caster must be tessellated and smooth: one flat quad or a closed box passes no light; a diced,
  smoothed top plane works (`water_surface`).
- Every refractor in the path must be a caster, and the solver gives up after a few refractions: build
  glassware for it (`glass_of_water_mnee`).
- Ignored by the solver: bump and normal maps, volumes on the light leg, Filter Glossy. Bevel and AO
  shader nodes are invalid on casters and receivers; use the Bevel modifier.

| Item | Setting |
|---|---|
| Caster | tessellated, smooth; diced top plane for water |
| Bevel | modifier, not the shader node |

#### 3d. Photon bake (`caustic_photons.py`, CPU)
Forward photons through the exact glass and water meshes (Snell, Fresnel, total internal reflection)
land on a receiver plane; their irradiance map is added to the receiver as emission albedo·E/π.
1. `export_geometry(path, surfaces, axis, grid)` in Blender: surfaces {object: IOR ratio} and the
   receiver grid to `.npz`; the defaults match `glassware.glass_of_water`.
2. `blender -b --factory-startup --python caustic_photons.py -- trace <geom.npz> <out.npy> <n> <seed> <source json>`,
   several seeds in parallel. Source: `{"type": "sun", "dir": [x,y,z] toward the light, "half_angle_deg": 0.2665, "irradiance": W/m²}`
   or `{"type": "area", "centre", "normal" (facing the scene), "size": m, "power": W}`.
3. `bake_irradiance(npy_paths, exr_path, sigma_cells)`: averages the runs, smooths, writes a float EXR (W/m²).
4. `add_caustic_light(mat, exr_path, scale, albedo_label)`: emission on up-facing faces; re-run it on the
   same material after a re-bake.
- Cycles refractive caustics off in this scene: the bake replaces them.
- The grid travels as `<file>.grid.json` beside each stage's output, so a fresh Blender uses the same plane.
- A bake, not a shader: re-bake after any light or object change. A quality bake takes minutes.

### Step 4. Check
- **Energy:** black room, no sky, orthographic top camera, so pixel sums ∝ flux. The same frame with the
  glass as a Transparent BSDF is the baseline; real glass passes ≈ (1 − R)ⁿ of it (n interfaces,
  R ≈ 4–5 % at 30–45°). A caustic that looks right but integrates far off is wrong.
- **Pattern:** judge it on a surface seen face-on; a grazing wall squeezes shapes 4–5× into vertical streaks.

### Generic layers
| Layer | Reference | Note for this material |
|---|---|---|
| Renderer choice | `references/renderer/renderer-choice.md` | the §1 table applies REN_02 and REN_03 |
| LuxCore setup | [luxcore.md](../renderer/luxcore.md) | PATH + light tracing, *Use CPUs* on (step 3a) |
| HDRI sun | `references/scene/lighting-camera.md` | the sun share sets crispness and contrast (step 3) |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| LuxCore GPU: camera paths only, no caustic | *Use CPUs* off | turn it on (step 3a) |
| No sun glints through the glass in a LuxCore control | `distant` lamp | `sun` lamp, only without an HDRI (step 3a) |
| No light from an MNEE caster | flat quad or closed box | diced, smoothed caster (step 3c) |
| MNEE caustic stops after one interface | a refractor that is not a caster, or too many interfaces | build the glassware for MNEE (step 3c) |
| Relief does not bend an MNEE caustic | bump and normal maps ignored | model the relief (step 2) |
| Submerged surfaces black under lamps | shadow rays cannot pass refraction | MNEE with a diced top plane (step 3c) |
| Pool floor black, no visible reason | `caustics_refractive = False` also blocks sky and lamp light through water | leave it on; only the photon bake turns it off (step 3d) |
| Path-traced caustic blurred away | Filter Glossy above 0 | Filter Glossy 0; check the method (step 1) |
| Caustic looks right, integrates far off | never checked | energy check (step 4) |
| Caustic ignores a moved light or object | photon bake is a bake | re-bake (step 3d) |
| Caustic lines read as vertical streaks | grazing view | judge it face-on (step 4) |
| One bright fold line per ridge set | single-frequency sine | random wave sum (step 2) |
| Thin straight streaks along unit edges | rounded edges and fades focus | wider fade, larger radii (step 2) |
| Flat glow or grey mush by the far wall | relief not sized to the receiver distance | size it; long waves at slope ≈ 0.04 (step 2) |

Generic problems: troubleshooting.md.
