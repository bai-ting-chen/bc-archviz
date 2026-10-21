# Glass

- Principled transmission 1, IOR 1.52, roughness 0. Thin Film for coated glazing (to try).
- Re-lathe Rhino glassware at a high segment count for close-ups.

- **Glass block** (pressed hollow unit): two pressed halves fused hot and sealed hollow (partial
  vacuum); the pattern is on the **inner** faces, outer faces smooth with slight pressing
  waviness; coated sides key to the mortar. Common units 190×190×80 mm (2.3 kg) and 240×240×80
  (4.1 kg) — from the weight, ~8 mm face glass, ~7 mm sides. Stack bond, 10 mm joints, perimeter
  bands ≥ 15 mm, panels ≤ ~15 m². Curved walls: the concave-side joint stays constant and the
  convex one opens, E = (L + g)(1 + s/r) − L; with g 10 / E 25 mm the inner radius is ≥ ~1.05 m
  (190 units), ≥ ~1.33 m (240). Model the relief as geometry (caustics.md › Designing a
  refractive relief), and leave a fraction of a millimetre of air between mortar and glass so the
  surfaces never coincide.
- **Liquid in glass**: Cycles has no nested-IOR priority, so model three surfaces — GLASS (1.52),
  INTERFACE below the waterline (1.52/1.333) and WATER_SURFACE (1.333) →
  `glassware.glass_of_water()`. Check normals per wall.

- **Glazing is not optically flat.** Float glass has roller waves (~0.1 mm peak-to-valley over
  ~0.3 m, ~1 mrad slope); the visible wobble of real windows is insulated-unit **pillowing**
  (panes bowed a few mm), strongest towards the frame. `materials.glass.glass_distortion(mat, obj)`:
  bump of a sine roller wave + a dome over the pane. 0.25 mm of wave read as blinds; the dome
  carries the effect. A glass that "looks too reflective" is usually a dark room behind it -
  Fresnel is physical; distortion and something to reflect make it read.
