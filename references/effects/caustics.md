# Caustics

## 1. Overview
Caustics are the focused light patterns that refraction throws onto a receiver: sun through glass,
through a pool, through patterned glass. Choose the method by the case below; the procedures that
back each method are in §4.

### Applying REN_02 to caustics
Apply the [renderer and method procedures](../renderer/renderer-choice.md) to the cases below.
| Case | Method | Why |
|---|---|---|
| Large light source, any refractor | Cycles path tracing | unbiased; converges when the key subtends a real angle, never for a sun-sized source |
| Lamps above calm water, submerged surfaces | **MNEE** | cheap and clean, but under-delivers energy and ignores volumes on the light leg |
| Sun through a rippled pool | **GN wavefront** `gn_caustics.add_caustic_sheet()` | native, exact, noise-free; MNEE fails outright on real ripples |
| Sun through glassware (glass, glass of water) | LuxCore, as the row below ([RULES REN_03](../renderer/renderer-choice.md#ren_03-procedure#ren_03-procedure)); `caustic_photons.py` (external, CPU) only when the scene must stay in Cycles | photons were the most faithful of the Cycles-side options on a measured shadow/lit ratio; MNEE and path tracing fall short |
| **Sun through patterned glass / glass block / several interfaces, room-scale receivers** | **LuxCore PATH + light tracing**, GPU camera paths + CPU light tracing ([LuxCore setup](../renderer/luxcore.md), [RULES REN_03](../renderer/renderer-choice.md#ren_03-procedure#ren_03-procedure)) | unbiased and energy-correct; the only engine that converged |

The measured ranking behind this table is in §4.1.

## 2. Layers and node-editor diagram
Caustics is a single light-transport effect, not a stack of layers, so there is no diagram. It sits
between the light source, the refractor and the receiver. Its parts are the procedures in §4.

## 3. Code
- `scripts/blender/effects/caustics/`: `gn_caustics.py` (GN wavefront; `add_caustic_sheet` is defined in
  `caustic_objects.py`), `caustic_photons.py` (photon bake), `photon_geometry.py` (`export_geometry`,
  receiver grid), `photon_shading.py` (`add_caustic_light`).
- MNEE: `scripts/controls/water/mnee_water.py` (control scene), water caster
  `scripts/blender/materials/water/water_mesh.py` (`water_surface`), glassware
  `scripts/blender/materials/glass/glass_assembly.py` (`glass_of_water_mnee`).
- The refractive relief has no builder named in this file; it is modelled geometry (§4.2).

## 4. Instructions and parameters, per layer
### 4.1 Comparing renderers (do this before trusting one)
- **Calibrate:** a minimal scene with the real refractor next to an **identical empty opening**. Its
  sunlit patch calibrates units between engines (must agree within a few %) and is the energy baseline.
- **Time:** equal wall-clock time per engine on its natural device, one job at a time (a second GPU or
  CPU job distorts timings). Use a long run of the best candidate as reference. Score relative RMSE and
  bias per region (caustic, glass seen from inside, wall).
- **Energy control:** black room, no sky, orthographic top camera, so pixel sums ∝ flux. The same frame
  with the glass as a Transparent BSDF (no refraction, no Fresnel) is the baseline. Real glass should pass
  ≈ (1 − R)ⁿ of it (n interfaces, R ≈ 4–5 % at 30–45°). A caustic that looks right but integrates far off
  is wrong.
- **Camera side:** look at the glass from the camera side too. Sun glints *through* the glass need a light
  camera rays can hit (Cycles sun via transmission rays; LuxCore `sun`, not `distant`).
- **Measured** on sun (0.53°) → 4 glass interfaces with a wavy relief → diffuse floor, equal 120 s,
  scored against a 900 s reference: LuxCore CPU light tracing 18 % rel. error, −0.5 % bias;
  LuxCore GPU caustic cache 40 % (−24 % bias, blur); LuxCore BIDIR 105 % (noise); Cycles path
  tracing ~1000 %, Cycles CPU path guiding ~3500 % (fireflies only), MNEE −82 % (gives up after
  one interface); LuxCore GPU with light tracing but *Use CPUs* off = camera paths only, no caustic (light
  tracing runs on CPU threads; with them on, GPU + CPU is the same caustic 2–6× faster, luxcore.md).
  The ranking is the knowledge; rerun the comparison when the scene is unlike these cases.

| Parameter | Value |
|---|---|
| Calibration tolerance (empty opening vs refractor) | a few % |
| Energy pass for real glass | ≈ (1 − R)ⁿ of the Transparent BSDF baseline |
| R (reflection per interface) | ≈ 4–5 % at 30–45° |
| Timing | equal wall-clock, one job at a time |
| Score | relative RMSE and bias per region |

### 4.2 Designing a refractive relief (patterned glass, glass block, wavy acrylic)
Model the relief as geometry: bump and normal maps do not bend a caustic.
- **Each curved patch is a lens.** f ≈ 1 / ((n − 1)·κ), κ the curvature; for a relief of amplitude A and
  wavelength λ, κ ≈ A(2π/λ)². The caustic network is sharpest at one to a few focal lengths; far beyond,
  neighbouring patches overlap into a flat glow. **Size the relief from the receiver distance** (in a room,
  typically 1.5–3 m), and choose between two looks (table below).
- The glass still looks rippled from inside because the background is far: a 0.5° deflection moves a
  tree 30 m away by 25 cm.
- **A single-frequency pattern draws fold lines.** A sine spends most of its length near its steepest
  slope, so every ridge sends that light to the same maximum deflection: one bright line per ridge set
  (an S-shape if the ridge meanders), repeated per tile. Real pressed glass varies: sum ~12 waves of random
  direction, log-uniform λ, amplitude ∝ λ^0.8, a slow depth envelope (1 ± 0.45), scaled to the target RMS
  slope; a mild vertical stretch reads as poured/flowing.
- **Preview before modelling:** a thin-lens numpy sketch — deflection = (n − 1)∇h per face, land at
  x + D·θ, histogram, blur by the sun's angular size — shows the network at several D in seconds, before
  any modelling or render. Over a 6×6 patch of units, measure the **share of light landing outside its
  own unit** (tangling) and p99/mean (line contrast) per candidate.
- **Pattern families** (manufacturers' names: Wave, Iceberg, Bubble, Diamond, Pristal, Quadra…):
  - *Wave* — a few long cosines. Crest orientation steers the light: horizontal crests throw it up and
    down (vertical streaks on a wall), diagonal crests cross into loops; mixing both 1:1 across the wall
    breaks any single direction.
  - *Iceberg* — ridged noise, h = −√(f² + (0.08·rms)²) of a sum of broad cosines: soft creases that fold
    the light into crisp, crossing lines.
  - Faceted *Diamond / Pristal / Quadra* are prisms: sharp-edged repeating geometric patches.
- **Straight features draw straight lines.** Rounded block edges, cavity corners and the strip where the
  relief fades to its border are cylindrical lenses along the unit's edges; where one focuses at the
  receiver's distance it casts a thin straight streak. Real blocks do it too; a wider fade or larger radii
  weaken it.
- **Lay tilt varies reflections, not caustics:** a hollow block is two parallel faces, so a random tilt of
  a few tenths of a degree shifts its light by millimetres. Use it for the reflections; vary the caustics
  through the relief itself.
- **Variety without memory:** ~16 relief variants as block definitions, each placed at random with random
  180° turns/flips (64 looks), instanced; unique meshes per element would be tens of millions of faces.
  Instanced, the modelled relief is cheap to trace (flat boxes were only 1.1–1.3× faster); displacement or
  normal maps are no speedup (luxcore.md). Fade the relief to a flat border over ≥ 25 mm — a short fade
  lenses into bright square outlines.
- **Light for caustics:** the HDRI's own sun casts them (RULES LGT_02) — pick a map by its sun share
  (lighting-camera.md › Pick the HDRI by its sun).
- **Contrast of light against the surface is set by the fill, not the caustic.** Sky through a large
  glazed wall plus white walls bouncing it lift the "shade" the caustics sit in. A clearer, bluer map —
  less sky illuminance for the same sun, i.e. a higher sun share — separates light from surface far more
  than a matter material or grading does; an AgX "High Contrast" look adds a little on top.
- **Judge pattern shape on a surface seen face-on.** A wall seen at a grazing angle squeezes every shape
  4–5× sideways, so any caustic on it reads as vertical streaks.

| Look | λ | Slope | Notes |
|---|---|---|---|
| Separate patches | 40–150 mm | RMS slope ≈ 0.015–0.02 | each unit's light stays inside its own footprint; a grid of rippled squares |
| One tangled net (wavy glass block) | 120–400 mm | slope ≈ 0.04; relief 3–5 mm peak to peak in a 190 mm block | light must travel further than half a unit; 20–40 % of each unit's light lands outside it at 2–3 m; lines stay sharp |
| Short waves (avoid) | < 100 mm | slope 0.17 | focuses within centimetres; grey mush by the far wall, washed out by 2 m |

### 4.3 MNEE build rules (measured, `scripts/controls/water/mnee_water.py`)
- Flags: `obj.cycles.is_caustics_caster` / `is_caustics_receiver`, `light.cycles.is_caustics_light`.
- The caster must be **tessellated and smooth**. One flat quad or a closed box gives no light at all; water
  as a diced, smoothed top plane works (`materials.water.water.water_surface`).
- Any refractive object in the path that is *not* a caster blocks MNEE, and the solver gives up after a few
  refractions — so glassware has to be built for it (`glassware.glass_of_water_mnee()`).
- Bump and normal maps are ignored by the solver, as are volumes on the light leg and Filter Glossy (per the
  manual). Relief you can see will not bend the caustic.
- Bevel and AO shader nodes are invalid on casters and receivers — use the Bevel *modifier*.

| Item | Setting |
|---|---|
| Caster flags | `obj.cycles.is_caustics_caster` (and `is_caustics_receiver` on receivers) |
| Light flag | `light.cycles.is_caustics_light` |
| Caster geometry | tessellated, smooth; diced top plane for water |
| Bevel | Bevel modifier, not the shader node |

### 4.4 GN wavefront (`gn_caustics.add_caustic_sheet()`)
- Refract each water vertex (Vector Math Refract, 1/IOR), Raycast onto the receivers, Raycast to the sun for
  shadow, then `E = E_sun·T·A_perp/A_landed`, Blur Attribute to about the sun's angular size, and a
  transparent emissive overlay carrying `albedo·E/π`. Set Material *after* Object Info.
- Stacked overlays need a high `transparent_max_bounces`.
- Validate by integrating the sheet's irradiance against `E_sun·cos θ` — if they agree it is conserving
  energy and the pattern can be trusted.

| Parameter | Value |
|---|---|
| Blur | about the sun's angular size |
| Overlay | transparent emissive, `albedo·E/π` |
| Material order | set after Object Info |
| `transparent_max_bounces` | high when overlays are stacked |
| Validation | sheet irradiance vs `E_sun·cos θ` |

### 4.5 Photon bake (`caustic_photons.py`)
- Forward photon tracing on CPU -> irradiance EXR -> `albedo·E/π` emission on the receiver, with Cycles
  refractive caustics off. Cost scales with photon count and core count; a quality bake is minutes, not
  seconds. Re-bake on any light or object change — it is a bake, not a shader.
- The receiver grid (`export_geometry(grid=…)`) travels with every stage as `<file>.grid.json` beside the
  .npy / .exr, so a bake in a fresh Blender uses the same plane; `add_caustic_light` can be re-run on the
  same material after a re-bake.

| Parameter | Value |
|---|---|
| Output | irradiance EXR → `albedo·E/π` emission on the receiver |
| Cycles refractive caustics | off (for this bake only) |
| Cost | photon count × cores; minutes for a quality bake |
| Receiver grid | `<file>.grid.json` beside the .npy / .exr |

### 4.6 Third-party options and fakes
| Option | Status |
|---|---|
| LuxCore (free, GPL) | tested, adopted for caustics (luxcore.md) |
| Caustica (~$59, GPU progressive photon mapping in a Cycles build) | unverified |
| Reblend (~$49, photon caustics / BDPT / VCM) | unverified |
| Octane (paid) | unverified |
| Fakes: Voronoi textures, gobo area lights, shadow-ray Transparent | only as a declared fallback |

### Generic layers
| Layer | Reference | Note for this material |
|---|---|---|
| Renderer and method choice | [renderer-choice.md](../renderer/renderer-choice.md) | the case table in §1 and the procedure in §4.1 |
| LuxCore setup | [luxcore.md](../renderer/luxcore.md) | PATH + light tracing; *Use CPUs* on for the caustic (§4.1) |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| No light at all from a MNEE caster | flat quad or closed box as the caster | tessellated, smooth caster; diced water top plane (§4.3) |
| MNEE caustic gone after one interface | a refractive non-caster in the path; the solver gives up after a few refractions | build the glassware for MNEE (§4.3) |
| Visible relief does not bend the caustic | bump and normal maps ignored by the solver | model the relief as geometry (§4.2) |
| Bevel or AO shader nodes on a caster or receiver | invalid there | Bevel modifier (§4.3) |
| Pool floor goes black for no visible reason | `caustics_refractive = False` also blocks sky and lamp light reaching submerged surfaces through water | do not switch it off to remove a caustic; the photon bake is the one place it is off on purpose (§4.5) |
| Path-traced caustic blurred away | Filter Glossy above 0 blurs what path tracing is trying to resolve | Filter Glossy 0 for path-traced caustics; check the method against §4.1 |
| Caustic looks right but integrates far off | not checked against the energy baseline | energy control and baseline (§4.1) |
| No sun glints through the glass from the camera side | light type camera rays cannot hit (LuxCore `distant`) | LuxCore `sun` (§4.1) |
| LuxCore GPU shows camera paths only, no caustic | *Use CPUs* off; light tracing runs on CPU threads | turn it on; GPU + CPU is the faster caustic (§4.1) |
| Caustic does not follow a moved light or object | photon bake is a bake, not a shader | re-bake after any light or object change (§4.5) |
| Caustic lines read as vertical streaks on a wall | grazing angle squeezes shapes 4–5× sideways | judge the pattern on a face-on surface (§4.2) |
| One bright fold line per ridge set | single-frequency sine | random wave sum, log-uniform λ (§4.2) |
| Thin straight streak along unit edges | cylindrical lenses at rounded edges and fades | wider fade or larger radii (§4.2) |
| Flat glow by the far wall, or grey mush | relief not sized to the receiver distance; short waves at high slope | size from the receiver distance; long waves at slope ≈ 0.04 (§4.2) |

Generic problems: troubleshooting.md.
