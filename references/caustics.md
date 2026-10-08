# Caustics

## Decision (RULES 2)
| Case | Method | Why |
|---|---|---|
| Large light source, any refractor | Cycles path tracing | unbiased; converges when the key subtends a real angle, never for a sun-sized source |
| Lamps above calm water, submerged surfaces | **MNEE** | cheap and clean, but under-delivers energy and ignores volumes on the light leg |
| Sun through a rippled pool | **GN wavefront** `gn_caustics.add_caustic_sheet()` | native, exact, noise-free; MNEE fails outright on real ripples |
| Sun through glassware | `caustic_photons.py` (external, CPU) | the most faithful of the three on a measured shadow/lit ratio; MNEE and path tracing both fall short |

The ranking is the knowledge; the measured ratios behind it are in the study. Rerun the
comparison when the scene is unlike these cases.

## MNEE build rules (measured, `tools/controls/mnee_water.py`)
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

## Third-party (unverified until our glass test passes)
Caustica (~$59, GPU progressive photon mapping in a Cycles build — best candidate), Reblend
(~$49, photon caustics / BDPT / VCM build), LuxCore (free, own material system), Octane (paid).
Fakes — Voronoi textures, gobo area lights, shadow-ray Transparent — only as a declared fallback.
