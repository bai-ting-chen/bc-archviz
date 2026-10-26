# Water surface (pools, still water)

The pool body and its surface. Which water file to read: [index.md](../index.md) › Water. Ripples and
waves caused by falling water or impacts: [water-ripple.md](water-ripple.md); choppy plunge pools:
[water-ripple.md](water-ripple.md) › Choppy pool.

## Pool water
- `materials.water.pool_water()`: Principled transmission 1, IOR 1.333, a shallow ripple bump, and
  **Volume Absorption** for the tint — depth does the colour work, so a pool reads green in the
  deep end and clear at the step without any gradient map.
- Geometry: `materials.water.water_surface(obj, …)` = top face only, diced, smooth (MNEE-ready; the
  volume still works over an opaque basin). Keep the waterline just under the coping.
- Rippled sunlit pool: Ocean modifier on a diced plane — no choppiness on short waves, and
  `wave_scale_min` >= 5 x grid spacing or the waves alias. Short wavelengths give the tight
  caustic networks; long swell does not.
- **Wind ripples are geometry, not a bump** when they carry caustics or are read as shapes (mm-high
  impact ripples that only break reflections can be a bump: [water-ripple.md](water-ripple.md) › Bump
  or geometry). A noise bump faking short ripples reads artificial,
  and stretching it "because ripples look flat" doubles what perspective already does — never
  stretch. Dice the surface finer, sized from the ripples visible in the shot, and let the Ocean
  carry them (wave_scale_min >= 5 x cell, a little choppiness for crisp crests; check for
  downward faces = folds). Keep only a millimetre-scale micro bump in the shader. Size the swell
  by RMS slope, not just amplitude.

- **Opaque pool look** (a stylisation, only when asked): opaque diffuse body under an exact IOR 1.333
  surface. Declare it; near-field sky reflection is Fresnel-limited (~6-12 % at 55-65 deg), so a
  reference that is near-white there is showing a pale floor through clear water.
- To try (manual-confirmed): **Volume Coefficients** node (absorption per channel in 1/m, from
  measured water absorption) + Volume Scatter phase **Fournier-Forand** (IOR 1.0-1.2,
  backscatter) for haze and light shafts; noise -> roughness for wind patches; Gabor texture for
  directional ripples.
- Steam: `materials.volumes.steam()` — Principled Volume, noise x height fade, anisotropy ~0.5.
