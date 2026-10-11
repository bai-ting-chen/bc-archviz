# Caustics

## Decision (RULES 2)
| Case | Method | Why |
|---|---|---|
| Large light source, any refractor | Cycles path tracing | unbiased; converges when the key subtends a real angle, never for a sun-sized source |
| Lamps above calm water, submerged surfaces | **MNEE** | cheap and clean, but under-delivers energy and ignores volumes on the light leg |
| Sun through a rippled pool | **GN wavefront** `gn_caustics.add_caustic_sheet()` | native, exact, noise-free; MNEE fails outright on real ripples |
| Sun through glassware | `caustic_photons.py` (external, CPU) | the most faithful of the three on a measured shadow/lit ratio; MNEE and path tracing both fall short |
| **Sun through patterned glass / glass block / several interfaces, room-scale receivers** | **LuxCore PATH + light tracing**, GPU camera paths + CPU light tracing (luxcore.md, RULES 2a) | unbiased and energy-correct; the only engine that converged |

Measured on sun (0.53°) → 4 glass interfaces with a wavy relief → diffuse floor, equal 120 s,
scored against a 900 s reference: LuxCore CPU light tracing 18 % rel. error, −0.5 % bias;
LuxCore GPU caustic cache 40 % (−24 % bias, blur); LuxCore BIDIR 105 % (noise); Cycles path
tracing ~1000 %, Cycles CPU path guiding ~3500 % (fireflies only), MNEE −82 % (gives up after
one interface); LuxCore GPU with light tracing but *Use CPUs* off = camera paths only, no caustic (light tracing runs on
CPU threads; with them on, GPU + CPU is the same caustic 2–6× faster, luxcore.md). The ranking is
the knowledge; rerun the comparison when the scene is unlike these cases.

## Comparing renderers (do this before trusting one)
1. A minimal scene with the real refractor next to an **identical empty opening**: its sunlit
   patch calibrates units between engines (must agree within a few %) and is the energy baseline.
2. **Equal wall-clock time** per engine on its natural device, one job at a time (a second GPU
   or CPU job distorts timings); a long run of the best candidate as reference; score relative
   RMSE and bias per region (caustic, glass seen from inside, wall).
3. **Energy control:** black room, no sky, orthographic top camera, so pixel sums ∝ flux. Same
   frame with the glass as a Transparent BSDF (no refraction, no Fresnel) → baseline. Real glass
   should pass ≈ (1 − R)ⁿ of it (n interfaces, R ≈ 4–5 % at 30–45°). A caustic that looks right
   but integrates far off is wrong.
4. Look at the glass from the camera side too: sun glints *through* the glass need a light camera
   rays can hit (Cycles sun via transmission rays; LuxCore `sun`, not `distant`).

## Designing a refractive relief (patterned glass, glass block, wavy acrylic)
Model the relief as geometry: bump and normal maps do not bend a caustic.
- **Each curved patch is a lens.** f ≈ 1 / ((n − 1)·κ), κ the curvature; for a relief of
  amplitude A and wavelength λ, κ ≈ A(2π/λ)². The caustic network is sharpest at one to a few
  focal lengths; far beyond, neighbouring patches overlap into a flat glow. **Size the relief
  from the receiver distance** (here 1.5–3 m), and choose between two looks:
  - *Separate patches* — each unit's light stays inside its own footprint, a grid of rippled
    squares: RMS slope ≈ 0.015–0.02 over λ ≈ 40–150 mm.
  - *One tangled net across units* (what real wavy glass block shows) — the light must travel
    further than half a unit: **long waves at a higher slope**, λ ≈ 120–400 mm, slope ≈ 0.04
    (relief 3–5 mm peak to peak in a 190 mm block): 20–40 % of each unit's light lands outside
    it at 2–3 m and the lines stay sharp. A higher slope on *short* waves (λ < 100 mm) focuses
    within centimetres and is a grey mush by the far wall; slope 0.17 washed out by 2 m.
  The glass still looks rippled from inside because the background is far: a 0.5° deflection
  moves a tree 30 m away by 25 cm.
- **A single-frequency pattern draws fold lines.** A sine spends most of its length near its
  steepest slope, so every ridge sends that light to the same maximum deflection: one bright line
  per ridge set (an S-shape if the ridge meanders), repeated per tile. Real pressed glass varies:
  sum ~12 waves of random direction, log-uniform λ, amplitude ∝ λ^0.8, a slow depth envelope
  (1 ± 0.45), scaled to the target RMS slope; a mild vertical stretch reads as poured/flowing.
- **Preview before modelling:** a thin-lens numpy sketch — deflection = (n − 1)∇h per face,
  land at x + D·θ, histogram, blur by the sun's angular size — shows the network at several D in
  seconds, before any modelling or render. Over a 6×6 patch of units, measure the **share of
  light landing outside its own unit** (tangling) and p99/mean (line contrast) per candidate.
- **Pattern families** (manufacturers' names: Wave, Iceberg, Bubble, Diamond, Pristal, Quadra…):
  - *Wave* — a few long cosines. Crest orientation steers the light: horizontal crests throw it
    up and down (vertical streaks on a wall), diagonal crests cross into loops; mixing both 1:1
    across the wall breaks any single direction.
  - *Iceberg* — ridged noise, h = −√(f² + (0.08·rms)²) of a sum of broad cosines: soft creases
    that fold the light into crisp, crossing lines.
  - Faceted *Diamond / Pristal / Quadra* are prisms: sharp-edged repeating geometric patches.
- **Straight features draw straight lines.** Rounded block edges, cavity corners and the strip
  where the relief fades to its border are cylindrical lenses along the unit's edges; where one
  focuses at the receiver's distance it casts a thin straight streak. Real blocks do it too;
  a wider fade or larger radii weaken it.
- **Lay tilt varies reflections, not caustics:** a hollow block is two parallel faces, so a
  random tilt of a few tenths of a degree shifts its light by millimetres. Use it for the
  reflections; vary the caustics through the relief itself.
- **Variety without memory:** ~16 relief variants as block definitions, each placed at random
  with random 180° turns/flips (64 looks), instanced; unique meshes per element would be
  tens of millions of faces. Instanced, the modelled relief is cheap to trace (flat boxes were
  only 1.1–1.3× faster); displacement or normal maps are no speedup (luxcore.md). Fade the relief to a flat border over ≥ 25 mm — a short fade
  lenses into bright square outlines.
- **Light for caustics:** the HDRI's own sun casts them (RULES 8a) — pick a map by its sun share
  (lighting-camera.md › Pick the HDRI by its sun).
- **Contrast of light against the surface is set by the fill, not the caustic.** Sky through a
  large glazed wall plus white walls bouncing it lift the "shade" the caustics sit in. Lowering
  the sky from ~18 to ~10 klux (a clear blue sky; sun share ~89 %) separated light from concrete
  far more than matte concrete or grading did; an AgX "High Contrast" look adds a little on top.
- **Judge pattern shape on a surface seen face-on.** A wall seen at a grazing angle squeezes
  every shape 4–5× sideways, so any caustic on it reads as vertical streaks.

## MNEE build rules (measured, `scripts/controls/mnee_water.py`)
- Flags: `obj.cycles.is_caustics_caster` / `is_caustics_receiver`, `light.cycles.is_caustics_light`.
- The caster must be **tessellated and smooth**. One flat quad or a closed box gives no light at
  all; water as a diced, smoothed top plane works (`interior.water_surface`).
- Any refractive object in the path that is *not* a caster blocks MNEE, and the solver gives up
  after a few refractions — so glassware has to be built for it
  (`glassware.glass_of_water_mnee()`).
- Bump and normal maps are ignored by the solver, as are volumes on the light leg and Filter
  Glossy (per the manual). Relief you can see will not bend the caustic.
- Bevel and AO shader nodes are invalid on casters and receivers — use the Bevel *modifier*.

## GN wavefront
Refract each water vertex (Vector Math Refract, 1/IOR), Raycast onto the receivers, Raycast to
the sun for shadow, then `E = E_sun·T·A_perp/A_landed`, Blur Attribute to about the sun's angular
size, and a transparent emissive overlay carrying `albedo·E/π`. Set Material *after* Object Info.
Stacked overlays need a high `transparent_max_bounces`.

Validate by integrating the sheet's irradiance against `E_sun·cos θ` — if they agree it is
conserving energy and the pattern can be trusted.

## Photon bake (`caustic_photons.py`)
Forward photon tracing on CPU -> irradiance EXR -> `albedo·E/π` emission on the receiver, with
Cycles refractive caustics off. Cost scales with photon count and core count; a quality bake is
minutes, not seconds. Re-bake on any light or object change — it is a bake, not a shader.

## Traps
- `caustics_refractive = False` *also* blocks ordinary sky and lamp light reaching submerged
  surfaces through water, so a pool floor goes black for reasons that look unrelated.
- Path-traced caustics need Filter Glossy at 0, or the thing you are trying to resolve is blurred
  away by the setting meant to denoise it.

## Third-party
LuxCore (free, GPL) — tested, adopted for caustics (luxcore.md). Unverified: Caustica (~$59, GPU
progressive photon mapping in a Cycles build), Reblend (~$49, photon caustics / BDPT / VCM),
Octane (paid).
Fakes — Voronoi textures, gobo area lights, shadow-ray Transparent — only as a declared fallback.
