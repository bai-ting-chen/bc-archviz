# Water ripples and waves

Code: `water.ripple.height_field` (field), `water.shading.save_height_exr` + `install_bump` (material) (used by `water.build.falling_film`).

Ripples and waves on a water surface caused by something: falling water landing, impacts, wind
near a plunge. Shared by any water material that hits a pool ([water-free-falling-film.md](water-free-falling-film.md),
[water-attached-film.md](water-attached-film.md), fountains). The pool body and plain wind ripples:
[water-surface.md](water-surface.md).

## 1. Bump or geometry?
| Case | Build | Why |
|---|---|---|
| Ripples a few mm high whose job is to break reflections and wobble what is seen through the surface | **bump on the pool's own material** from a float height map | only the slope reads; no extra surface |
| Wind ripples carrying caustics, or crests seen in silhouette | geometry (Ocean / height field), [water-surface.md](water-surface.md) | caustics and silhouettes need real surface |
| Rounded chop and boils in a plunge zone | geometry, see *Choppy pool* below | amplitude of cm |

- **Never a second water skin over the pool** for ripples: a thin transparent sheet above the pool
  adds its own Fresnel reflection, and its area reads as a lighter rectangle. A thin-wall skin is
  fine only for small standing features (crowns, [water-splash.md](water-splash.md)).
- **Slope decides visibility:** ripples that visibly break reflections need slopes of ~3–8°
  (0.05–0.15 rad). Amplitudes giving ~1° are invisible however wide the field.

## 2. Impact field (from a falling sheet or drops)
Sources come from where the water actually lands (the landing line, weighted by local thickness;
drops through the gaps land weaker), so the line is ragged and heavy streams hit harder.
- **Per impact:** a crater (−0.7 A, Gaussian, r < 0.6 R), a crown ring A at radius R with 3–7
  lobes, then damped capillary ripples outside it.
- **Spreading waves:** short capillary-gravity rings die within tens of cm; longer gravity waves
  travel metres (damping length ~8–12 wavelengths); amplitude falls ~1/√r.
- **From the whole landing line:** irregular, roughly wall-parallel fronts heading out across the
  pool, bending along the wall; they fade past the ends of the fall.
- **Chop near the wall:** short irregular waves, many directions, strongest at the impact line.
- **Never stack:** overlapping impacts sum to centimetres. Soft-limit each component
  (A_cap·tanh(H/A_cap)).
- Fade the field to zero at its borders.

| Parameter | Value |
|---|---|
| Impacts | ~1 per 2 cm of landing line + drops through the gaps |
| Crater/crown | R 1.2–4 cm × strength, A 1.5–5 mm × strength, cap ±4 mm |
| Capillary ripples after the crown | λ 1.2–2.2 cm, decay 4–12 cm |
| Ring waves | λ 2–6 cm (decay ~8 λ) and 8–25 cm (decay ~12 λ), on the stronger half of impacts |
| Line fronts | ~36 trains, λ 5–40 cm log-uniform, within ±40° of the wall normal, decay ~10 λ, cap ±3 mm |
| Chop | λ 2–9 cm, ~1.8 mm, fading over ~0.6 m from the wall |
| Field extent | ~2 m out from the wall, ~1 m past each end |

## 3. Bump on the pool material
- Write the height (mm) into a **float image**, save it as an EXR in the study library, and point
  the image datablock at that file (a generated image is lost on reload): blender-api-traps ›
  Render / images.
- Pool material: Geometry Position → map world XY to UV over the field → Image Texture (CLIP
  outside, Cubic, Non-Color) × (True Normal z > 0.5, top faces only) → Bump (Distance 0.001 for
  mm) → Principled Normal.
- Declare it: the surface shading moves, the geometry does not (mm amplitude, invisible in
  silhouette).
- Proof: reload the saved scene in a fresh Blender and read the image's min/max back; then a
  render beside the same render without the bump.

## 4. Choppy pool that hides the floor (plunge zones)
- Geometry wavelets everywhere (λ 3–25 cm, steepness ~0.09), rougher within ~0.4 m of a plunge,
  under a slow gust envelope (0.3–1.6, λ 0.6–2.5 m). 28 cosines read as a cross-hatch, use ~64.
- **One wave field object shared by every mesh touching the pond**, so near grid, crest band and
  far plane meet without seams; the far plane gets a hole matching the near region.
- At grazing view (~70°) water reflects only 6–10 %: the **floor sets the pool's tone**. Polished
  near-black stone (albedo 0.02–0.05) + absorption ~1.5 /m + chop removes the floor from view.
- Rounded, not spiky: chop λ 4–15 cm, boils as domes (positive part^1.5) of 5–12 cm; short boils at
  large amplitude on a fine grid draw cones.

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Lighter rectangle on the pool | ripples on a separate skin over the pool | bump on the pool material (§1) |
| Bump has no effect | image wiped (colour space set after the pixels, see api-traps); or slope ~1° | colour space before pixels, read min/max back; slopes 3–8° (§1, §3) |
| Cm-high bumps at strong impacts | overlapping impacts summed | soft cap (§2) |
| Waves stop dead at the field edge | no border fade | fade to zero at the borders (§2) |
| Cross-hatched chop | too few cosines | ~64 (§4) |
