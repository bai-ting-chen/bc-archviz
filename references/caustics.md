# Caustics

## Decision (RULES 2)
| Case | Method | Notes |
|---|---|---|
| Large light source, any refractor | Cycles path tracing | unbiased; converges only if the key isn't tiny (150 mm at 1.2 m yes, 1° sun no) |
| Lamps above calm water, submerged surfaces | **MNEE** | 70–80 % of expected energy; ignores volumes on the light leg |
| Sun through a rippled pool | **GN wavefront** `gn_caustics.add_caustic_sheet()` | native, exact, noise-free; MNEE fails on real ripples |
| Sun through glassware | `caustic_photons.py` (external, CPU) | validated 0.80 shadow/lit; MNEE gave 66 %, path tracing 0.46 |

## MNEE build rules (measured, `tools/controls/mnee_water.py`)
- Flags: `obj.cycles.is_caustics_caster` / `is_caustics_receiver`, `light.cycles.is_caustics_light`.
- Caster must be **tessellated and smooth**: one flat quad or a closed box → no light at all;
  water as top plane diced (10 cm), smooth → works (`interior.water_surface`).
- Any refractive object in the path that is not a caster blocks MNEE; ≤ 4 refractions for sun paths
  → glassware built for it: `glassware.glass_of_water_mnee()`.
- Bump/normal maps and volumes are ignored by the solver; Filter Glossy is ignored (manual).
- Bevel/AO shader nodes invalid on casters/receivers.

## GN wavefront (study 261006_pool)
Refract each water vertex (Vector Math Refract, 1/1.333), Raycast onto receivers, Raycast to the
sun for shadow, E = E_sun·T·A_perp/A_landed (checked 119 vs 121.5 W/m²), Blur Attribute ≈ sun
disc, transparent emissive overlay (albedo·E/π). Set Material after Object Info. Stacked overlays
need `transparent_max_bounces` 128.

## Photon bake (`caustic_photons.py`)
Forward photon tracing on CPU → irradiance EXR → albedo·E/π emission on the receiver, Cycles
refractive caustics off. 24 M photons ≈ 100 s / 6 cores. Re-bake per light/object change.

## Traps
- `caustics_refractive = False` also blocks sky/lamp light through water onto submerged surfaces.
- Path-traced caustics: Filter Glossy 0.

## Third-party (unverified until our glass test passes)
Caustica ($59, GPU progressive photon mapping in a Cycles build — best candidate), Reblend ($49,
photon caustics/BDPT/VCM build), LuxCore (free, own materials), Octane (paid). Fakes (Voronoi
textures, gobo area lights, shadow-ray Transparent) only as declared fallback.
