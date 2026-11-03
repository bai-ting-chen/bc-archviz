# Caustics

## 1. Overview
Caustics are the light patterns a refractor focuses onto a receiver: sun through a pool, glass or
patterned glass. Two methods: the fast one, GN wavefront in Cycles, for sunlight through a water body;
the accurate one, LuxCore, for everything else (RULES REN_02, REN_03). Say which and why, then build and
check it (§4). The engine rules are in `references/renderer/renderer-choice.md`; the glass-block wall
that carries a relief is in `references/materials/glass/glass.md`.

### Choosing the method
| Case | Method | Why |
|---|---|---|
| Sun through a water body (pool, pond, water feature) onto matte surfaces below | GN wavefront (step 3b) | native, noise-free, energy-exact for one refraction |
| Any glass (glassware, patterned glass, glass block), lamps, or several interfaces | LuxCore (step 3a) | unbiased, energy-correct; the only engine that converged (step 1) |

## 2. Layers and node-editor diagram
```
 ┌─ CAUSTICS — PROCEDURE DIAGRAM ───────────────────────────────────────────┐
 │ Choose   water body + sun, or glass / lamps (§1)                         │
 │   ▼                                                                      │
 │ Relief   patterned glass only: size it from the receiver distance        │
 │   ▼                                                                      │
 │ Build    ┬─ LuxCore PATH + light tracing ─► the render itself            │
 │          └─ GN wavefront sheet ─► emissive overlay above the receivers   │
 │   ▼                                                                      │
 │ Check    energy against a baseline; pattern face-on                      │
 └──────────────────────────────────────────────────────────────────────────┘
```
- Off switch: hide the `CAUSTIC_SHEET` object (GN wavefront); LuxCore caustics are part of the render.

## 3. Code
- GN wavefront: `scripts/blender/effects/caustics/gn_caustics.py`:
  `add_caustic_sheet(caster, receivers, occluders, sun_obj, ior=…, floor_tex=…, floor_albedo=…)`.
- LuxCore: `renderer.luxcore.engine.engine_setup` ([luxcore.md](../renderer/luxcore.md)).
- Relief: no builder; modelled geometry (step 2).
- Regression: `scripts/controls/regression/stage_b_graph_check.py` (sheet graph and overlay).

## 4. Instructions and parameters
### Step 1. Choose the method
- Take the §1 row; record the method and why in the study notes.
- **Why glass goes to LuxCore, measured** (sun 0.53° → 4 glass interfaces with a wavy relief → diffuse
  floor, equal 120 s, against a 900 s reference): LuxCore light tracing 18 % relative error, −0.5 % bias;
  LuxCore GPU caustic cache 40 % (−24 % bias, blur); LuxCore BIDIR 105 % (noise); Cycles path tracing
  ~1000 %; Cycles CPU path guiding ~3500 % (fireflies only); Cycles MNEE −82 % (gives up after one interface).

### Step 2. Design the relief (patterned glass, glass block, wavy acrylic)
- **Model it as geometry.** In LuxCore a normal map bends the caustic but gives dark seams and no
  parallax (luxcore.md).
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
- **Light, both methods:** the HDRI's own sun (RULES LGT_02); choose the map by its sun share
  (lighting-camera.md › Pick the HDRI by its sun). The fill sets the contrast between caustic and
  surface: a clearer, bluer map (higher sun share) separates them far more than a material or grade does.

#### 3a. LuxCore
- PATH with light tracing, GPU camera paths + CPU light tracing; setup in [luxcore.md](../renderer/luxcore.md).
- *Use CPUs* on: light tracing runs on CPU threads, so without them the GPU renders no caustic.
- Glints through the glass from the camera side come from the HDRI sun. In a control without an HDRI use
  a LuxCore `sun` lamp, not `distant`, which camera rays cannot hit.

#### 3b. GN wavefront (`add_caustic_sheet`)
- The water surface mesh is the light's wavefront. Each vertex refracts the sun (Vector Math Refract,
  1/IOR) and is raycast onto the receivers and to the sun for shadow. Each face carries
  E = E_sun·T·A_perp / A_landed, blurred to the sun's angular size, shown by a transparent emissive
  overlay of albedo·E/π.
- Limits: sun only, one refraction (exact for a water body), constant T, matte receivers. Receivers are
  sorted into floor (`floor_albedo` or `floor_tex`) and walls (`wall_albedo` in `caustic_sheet_material`).
- The water caster: the diced, smooth top plane (`materials.water.water.water_surface`).

| Parameter | Value |
|---|---|
| `ior` | 1.333 (water) |
| `floor_albedo` or `floor_tex` | the receiver's real albedo or its texture |
| `transparent_max_bounces` | high when overlays stack |

### Step 4. Check
- **Energy, GN wavefront:** the sheet's integrated irradiance equals E_sun·cos θ over its area.
- **Energy, LuxCore:** black room, no sky, orthographic top camera, so pixel sums ∝ flux. The same frame
  with the glass as a Transparent BSDF is the baseline; real glass passes ≈ (1 − R)ⁿ of it (n interfaces,
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
| Pool floor black, no visible reason | `caustics_refractive = False` also blocks sky and lamp light through water | leave it on (step 3b) |
| Submerged surfaces black under lamps | Cycles shadow rays cannot pass refraction; GN wavefront is sun only | LuxCore (step 3a) |
| Caustic looks right, integrates far off | never checked | energy check (step 4) |
| Caustic lines read as vertical streaks | grazing view | judge it face-on (step 4) |
| One bright fold line per ridge set | single-frequency sine | random wave sum (step 2) |
| Thin straight streaks along unit edges | rounded edges and fades focus | wider fade, larger radii (step 2) |
| Flat glow or grey mush by the far wall | relief not sized to the receiver distance | size it; long waves at slope ≈ 0.04 (step 2) |

Generic problems: troubleshooting.md.
