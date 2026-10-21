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
