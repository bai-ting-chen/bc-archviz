# Wet Surfaces

## Wet surfaces and dew
- Wet = darker and more saturated (internal reflection in the film, Lekner-Dorf): albedo ->
  dry^gamma (1.4 for soil/stone; grass reads better at ~1.7) + a water coat (IOR 1.33).
- A wet lawn seen from a low camera is mostly grazing angles: the film's Fresnel sheen of a
  grey sky greys it out (saturation drops). A darker base keeps the "wet" reading; the sheen is
  physically right (dewy lawns look silvery under fog).
- Dew beads are sub-pixel beyond a few metres (1 mm at 4 m < 1 px at 2400 px): their sum is the
  sheen. Near the camera they read only where large - broad waxy leaves (clover) hold 2-5 mm
  beads. Under an even sky a bead is bright through refraction + total reflection inside it,
  not its ~4 % surface reflection: a coat-only bead bump was invisible even at 0.4 m. Model
  them as effective-reflectance glossy beads (declared approximation), faded with camera
  distance (`materials.vegetation.DEW_GRASS`, `DEW_BROAD`). The denoiser smooths isolated sub-pixel
  glints, so size and density must carry them.


- **Wet surround (pool coping, splash zone)**: wet porous albedo falls non-linearly and
  saturates (Lekner & Dorf 1988; Jensen et al. 1999) -> wet colour = dry ** ~1.4 (Gamma node;
  1.8 turns a warm white beige-brown and reads as dirt), roughness ~0.1, plus a water film as
  Principled coat (IOR 1.33, rough ~0.03). When the edge is an arc, mask by the analytic
  distance d = R - |P.xy - C| (no mesh density); ragged splash band by noise-pushed d, Voronoi
  drops thinning with d, faint darker tide rings beyond, scum band at the waterline on vertical
  faces. Gate by height so canopies and far floors stay dry. Patchy, never a band (RULES MAT_05):
  drive the band width with a slow noise along the edge (down to negative = dry), and make dried
  marks blobs darker at their rim (coffee-ring) rather than contour lines.

## Wet wall behind falling water
- **Wet where the water is, not where the film is near.** A free-falling sheet stands off the wall
  (tens of cm at the foot), so a wetness mask from distance-to-film leaves the wall behind the
  lower curtain dry. Drive it from a proxy lying **on the wall face** over the curtain's whole
  footprint (behind the water, everything is wet: spray, run-down and condensation).
- **Ragged ends:** the wet edge wanders past each end of the curtain (5–30 cm, changing with
  height), with runoff fingers hanging from the top near the ends. A straight vertical wet/dry line
  is a rigid tell.
- **Splash band:** a low band above the pool (0.2–0.6 m, varying along the wall) fading out past
  both ends of the fall (e-fold ~0.45 m). Not the whole wall (RULES MAT_05: patchy, physically shaped).
- Keep the proxy a plain hidden mesh referenced by the wetness GN; replace its mesh data in place
  (never delete the object, or every reference goes empty and the noise term draws blotches).
