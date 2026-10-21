# Variation

## Randomness and anti-tiling (RULES MAT_06)
Repeated units and tiled maps need three kinds of variation. Cycles has no built-in stochastic
tiling (5.2 manual: no such texture node); build it from nodes.
- **Per-unit key.** *Object Info › Random*: one value per object instance (a hash of the name;
  collection instances each get their own). A Rhino block made of several objects (frame + glass)
  gets a *different* value per part — for one value per unit store it on the instance (custom
  property or *Store Named Attribute*, Instance domain) and read it with *Attribute › Instancer*.
  *Geometry › Random per Island* (Cycles only) varies the pieces of one joined mesh (bricks,
  planks); it repeats across instances of that mesh, so combine it with the instance key.
- **Per-unit variation** from that key: tint ±2–5 % value, roughness ±0.05, bump strength,
  a random UV *offset* (offsets keep normal maps valid; rotations do not).
- **Macro variation** — cheapest, biggest payoff: a 2–8 m world-space noise multiplied into
  albedo (±5–10 %) and added to roughness; hides a repeat without removing it.
- **Anti-tiling** where a repeat would still show: 2–3 lookups of the same map with different
  offsets mixed by a noise (cost ×2–3, robust), or hex tiling (3 lookups over a random hex grid
  with weight-sharpened blending, Mikkelsen 2022 — the method behind V-Ray's Stochastic
  Tiling); Voronoi-cell offsets are cheap but seam at cell edges unless blended there. Any UV
  rotation breaks a tangent-space normal map — drive relief from the height map through a Bump
  node instead. Free add-on to compare against: Patchwork (MIT).
- Offset lookup copies keep the original Image Texture projection, blend, interpolation and
  image colour space. Vary both coordinates used by that projection: zero Z offsets leave
  front-wall XZ texture rows in the same phase even when X/Y offsets differ.
- **Box projection** (Image Texture › Box, Blend 0.1–0.2) for Rhino geometry without UVs; again
  Bump from height, not the normal map.
- **LuxCore:** native Image › Randomized Tiling and 2D Mapping › Randomized UV; Object Info ›
  Random converts per instance (luxcore.md › Native LuxCore materials).
- Generated maps with no recognisable feature (cloudy tone + grain) cannot show a repeat; a
  scanned map with stains or cracks repeats visibly along every joint it is box-mapped onto.


## MAT_05 procedure

**Nature is patchy, never continuous or uniform**. Wetness, stains,
    wear, dirt, splashes: large here, small there, absent elsewhere. A constant-width band or a
    contour ring reads as impossible. Drive extent with a slow noise that can reach zero, and
    give marks a physical shape (dried splash = blob darker at its rim, not a line).


## MAT_06 procedure

**Repetition and imperfection**. Every surface of repeated units or tiled maps (glass block,
    brick, stone, tile, curtain wall, mortar) gets randomness: no visible texture repeat, variation
    per unit (tint, roughness, pattern, small tilt), and concave joints get dust, darkest in the
    corner and fading outward. Plan it into the first material pass; perfectly regular units and
    razor-clean corners read as CG. How: [materials/variation.md](variation.md)
