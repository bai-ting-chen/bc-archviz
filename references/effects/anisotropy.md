# Anisotropy

## 1. Overview
Anisotropy is directional roughness: parallel microscopic grooves spread light across the
grooves more than along them. On metal it stretches reflected highlights; on glass it also
stretches the blur of objects seen through the surface. It describes an aggregate microfacet
response, not the lensing or silhouette of individually visible ribs. Visible relief belongs
to the material's geometry or bump method (`references/materials/glass/glass.md`).

Both the Glass BSDF and Principled transmission support directional blur.

**Use when:** brushed or ground metal; reeded, fluted or ribbed glass whose ribs are too small
to model at the shot's distance; brushed or linearly ground glass; brushed acrylic (RULES MAT_03, MAT_04).
**Not when:** clear float glass, or evenly frosted or sandblasted glass with no preferred direction.

## 2. Layers and node-editor diagram
```
 +-- ANISOTROPY -- PROCEDURE DIAGRAM --------------------------------------+
 | Choose response    reflection / transmission -> supported BSDF          |
 |   v                                                                     |
 | Set roughness      existing material base -> rough microfacets          |
 |   v                                                                     |
 | Set direction      world axis / directional UV -> BSDF Tangent          |
 |   v                                                                     |
 | Set amount, turn   amount + rotation -> directional BSDF response       |
 |   v                                                                     |
 | Check              off / on / 90-degree turn / off repeat -> PNG widths |
 +-------------------------------------------------------------------------+
```
The helper edits the existing BSDF. Its amount is the off switch (RULES MAT_07).
Colour, IOR, metal response and surface relief remain the material's terms (RULES MAT_01).

## 3. Code
- `scripts/blender/effects/anisotropy.py`: `anisotropy(bsdf, amount, rotation, tangent)`.
  Principled, Glass and Metallic BSDFs; sets amount, rotation and tangent.
- `scripts/blender/materials/shared/dielectric.py`: `dielectric(..., anisotropy=None,
  rotation=0.0, tangent=(1, 0, 0))`. `None` leaves the legacy graph unchanged; explicit zero
  turns the effect off. `glass_material()` keeps its existing arguments; apply the effect to
  its BSDF when needed.
- `scripts/controls/effects/anisotropy_lab.py`: headless Cycles, `--out <folder> --case glass`
  or `--case metal`. Default 1024 samples, 768 px frames. Writes off/on/rotated/
  repeated-off PNGs, a native-crop pair in that order, feature/noise diffs and measurement JSON.

## 4. Instructions and parameters
1. **Choose the response.** Use the existing
   material BSDF, rather than mixing in a second glass or metal builder.

   | Parameter | Starting choice |
   |---|---|
   | Reflection | Principled or Metallic BSDF |
   | Transmission | Principled transmission or Glass BSDF |

2. **Set roughness.** Roughness supplies the spread; anisotropy redistributes it by direction.
   A perfectly smooth surface gives no visible directional blur. Keep the material's IOR and tint.

   | Parameter | Starting value and effect |
   |---|---|
   | Roughness, brushed transparent surface | 0.24; the control resolves both grid-edge widths |
   | Roughness, reflective control | 0.12; the control resolves reflected grid-edge widths |
   | Roughness, production material | material-specific; size the appearance from the shot (RULES MAT_03) |

3. **Set direction.** Pass a nonzero world-space tangent vector lying in the surface, such as
   `(1, 0, 0)` on an XY pane. Alternatively run `archviz.directional_uv(obj, size, name, axis,
   along='U')`, then pass that map's name as `tangent`; the helper adds a UV Tangent node.
   The UV tangent follows U. In the flat controls with positive amount, the broad blur axis
   follows the supplied tangent on the Principled and Metallic BSDFs. For physical grooves along
   U, start with rotation 0.25 so the spread runs across them; for grooves along V, start at 0.
   **The Glass BSDF is the other way round:** its broad axis runs across the tangent, so start
   at rotation 0 for grooves along U. End faces need inspection.
   Explicit vectors are linked through Combine XYZ: an unlinked Tangent default did not
   produce the directional split in the transmission control.

   | Parameter | Value |
   |---|---|
   | `tangent` vector | world axis projected into the surface; avoid the normal axis |
   | `tangent` string | existing directional UV-map name |
   | `directional_uv` size | metres per UV unit (RULES MAT_01) |

4. **Set amount and rotation.** Start with a visible response, then reduce to match the material.
   In the lab, amount 0.8 broadens one edge and narrows the perpendicular edge beyond the repeated-off
   noise floor. A 90-degree turn swaps them. Pixel widths depend on the scene, not just the amount.

   | Parameter | Starting value and measured effect |
   |---|---|
   | `amount` | 0 off; 0.8 produces a directional width split in the control |
   | `amount`, Glass BSDF | the same 0.8 splits far more (edge widths 53 / 5 px against 32 / 12 px on Principled); start lower |
   | `rotation` | 0 initially; 0.25 turns = 90 degrees, swaps the broad and narrow axes |
   | Metal settings | retain the material's own anisotropy and brush-streak values |

5. **Check the response.** Run the lab and inspect its pair (left to right: off, on, rotated)
   and equally amplified feature/noise diffs (RULES VAL_02, VAL_03). The JSON measures 10–90%
   display-PNG grid-edge widths along X and Y. The directional split must exceed the repeated-off
   width variation; rotating must reverse its sign, and feature MAE must exceed baseline MAE.
   Repeat this comparison in the intended shot. Undo the directional response with amount 0.

   | Check | Expected result |
   |---|---|
   | On vs off repeat | width split and feature difference above the baseline noise |
   | Quarter turn | broad and narrow blur axes exchange |
   | Clear float / uniform frost | anisotropy off |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Blur runs along the grooves | wrong tangent convention or UV direction; a Glass BSDF where Principled was assumed, or the reverse | inspect the broad axis and turn 0.25 (step 3) |
| No visible effect | roughness zero or amount off | check both parameters (steps 2 and 4) |
| Direction changes between faces | unsuitable UV projection or end face | inspect directional U on those faces (step 3) |
| Glass loses recognisable ribs | visible refractive relief replaced by aggregate blur | use modelled ribs at that shot distance (step 1) |
| Apparent improvement disappears on repeat | sampling noise | compare widths and the repeated baseline (step 5) |

Generic render noise and exposure problems: troubleshooting.md.
