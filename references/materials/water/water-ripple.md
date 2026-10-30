# Water ripples and waves

## 1. Overview
Ripples and waves on a water surface caused by something: falling water landing, impacts, wind
near a plunge. Shared by any water material that hits a pool (water-free-falling-film.md,
water-attached-film.md, fountains). The pool body and plain wind ripples:
water-surface.md.

**Use when:** a ripple or wave is caused by something (a landing, an impact, a plunge). Plain wind
ripples and the pool body: water-surface.md.

## 2. Layers and node-editor diagram
Specific layers are described in §4. Generic layers are written once, in their own reference, and
used here with ripple settings.

```
                           WATER RIPPLES AND WAVES
 ┌──────────────────────────────────────────────────────────────────────────┐
 │ SPECIFIC (§4)                                                            │
 │   §4.1 Impact field (float height, mm)  → height image                   │
 │   §4.2 Bump on the pool material        → shading (surface normal)       │
 │   §4.3 Choppy pool (geometry wavelets)  → pool geometry, boils           │
 │ GENERIC (own reference)                                                  │
 │   Landing line, crowns, drops           → water-splash.md                │
 │   Pool body, wind ripples as geometry   → water-surface.md               │
 └──────────────────────────────────────────────────────────────────────────┘
```

Flow:
```
   landing line, weighted by local thickness (water-splash.md) ──► §4.1 height field (mm)
   §4.1 ──► float EXR ──► §4.2 bump (top faces only) ──► pool Principled normal
   §4.3 wave field ──► shared by every mesh touching the pond ──► pool geometry
```

**Bump or geometry?**

| Case | Build | Why |
|---|---|---|
| Ripples a few mm high whose job is to break reflections and wobble what is seen through the surface | **bump on the pool's own material** from a float height map | only the slope reads; no extra surface |
| Wind ripples carrying caustics, or crests seen in silhouette | geometry (Ocean / height field), water-surface.md | caustics and silhouettes need real surface |
| Rounded chop and boils in a plunge zone | geometry, see §4.3 | amplitude of cm |

- **Never a second water skin over the pool** for ripples: a thin transparent sheet above the pool
  adds its own Fresnel reflection, and its area reads as a lighter rectangle. A thin-wall skin is
  fine only for small standing features (crowns, water-splash.md).

## 3. Code
`scripts/blender/materials/water/`:
- `ripple.py`: `height_field(lip, impact_pts, strength, p)` builds the impact field (§4.1); parameters
  in `RippleParams`.
- `height_image.py`: `save_height_exr(H, path)` writes the float EXR (§4.2).
- `ripple_bump.py`: `install_bump(material, image, lip, s_range, o_range)` puts the bump on the pool
  material (§4.2).
- `build.py`: `falling_film()` runs these for a falling film.

No script is named in this file for the choppy pool (§4.3). No control scene is named either.

## 4. Instructions and parameters, per layer

### 4.1 Impact field (from a falling sheet or drops)
- Sources come from where the water actually lands (the landing line, weighted by local thickness;
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

### 4.2 Bump on the pool material
- Write the height (mm) into a **float image**, save it as an EXR in the study library, and point
  the image datablock at that file (a generated image is lost on reload): blender-api-traps ›
  Render / images.
- Pool material: Geometry Position → map world XY to UV over the field → Image Texture (CLIP
  outside, Cubic, Non-Color) × (True Normal z > 0.5, top faces only) → Bump (Distance 0.001 for
  mm) → Principled Normal.
- **Slope decides visibility:** ripples that visibly break reflections need slopes of ~3–8°
  (0.05–0.15 rad). Amplitudes giving ~1° are invisible however wide the field.
- Declare it: the surface shading moves, the geometry does not (mm amplitude, invisible in
  silhouette).
- Proof: reload the saved scene in a fresh Blender and read the image's min/max back; then a
  render beside the same render without the bump.

| Parameter | Value |
|---|---|
| Image interpolation | Cubic |
| Image extension | CLIP outside the field |
| Colour space | Non-Color |
| Top-face mask | True Normal z > 0.5 |
| Bump distance | 0.001 (mm) |
| Slope for visible breakup | ~3–8° (0.05–0.15 rad) |

### 4.3 Choppy pool that hides the floor (plunge zones)
- Geometry wavelets everywhere, rougher within ~0.4 m of a plunge, under a slow gust envelope.
  28 cosines read as a cross-hatch, use ~64.
- **One wave field object shared by every mesh touching the pond**, so near grid, crest band and
  far plane meet without seams; the far plane gets a hole matching the near region.
- At grazing view (~70°) water reflects only 6–10 %: the **floor sets the pool's tone**. Polished
  near-black stone (albedo 0.02–0.05) + absorption ~1.5 /m + chop removes the floor from view.
- Rounded, not spiky: boils as domes (positive part^1.5); short boils at large amplitude on a fine
  grid draw cones.

| Parameter | Value |
|---|---|
| Wavelets | λ 3–25 cm, steepness ~0.09 |
| Rougher zone | within ~0.4 m of a plunge |
| Gust envelope | 0.3–1.6, λ 0.6–2.5 m |
| Cosines | ~64 |
| Chop (rounded) | λ 4–15 cm |
| Boils | domes of 5–12 cm |
| Grazing view / reflection | ~70° / 6–10 % |
| Floor albedo / absorption | 0.02–0.05 / ~1.5 /m |

Generic layers, ripple settings:

| Layer | Reference | Note for this material |
|---|---|---|
| Landing line, crowns, drops | water-splash.md | the impact sources for §4.1 |
| Pool body, wind ripples as geometry | water-surface.md | plain wind ripples and caustics; the pool body |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Lighter rectangle on the pool | ripples on a separate skin over the pool | bump on the pool material (§2, §4.2) |
| Bump has no effect | image wiped (colour space set after the pixels, see api-traps); or slope ~1° | colour space before pixels, read min/max back; slopes 3–8° (§4.2) |
| Cm-high bumps at strong impacts | overlapping impacts summed | soft cap (§4.1) |
| Waves stop dead at the field edge | no border fade | fade to zero at the borders (§4.1) |
| Cross-hatched chop | too few cosines | ~64 (§4.3) |

Generic problems: `references/workflow/troubleshooting.md` (not linked from this file: a link here
would close a reference loop).
