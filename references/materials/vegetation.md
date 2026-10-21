# Vegetation

- Leaf litter and foliage: one GN group (Distribute Points on Faces, selection = Z below a limit
  AND a noise patch threshold -> Instance on Points with random rotation and scale), per-instance
  tone via Object Info › Random. → `scatter.scatter(...)` + `materials.variation.random_tone_material`.
  **The patch threshold is knife-edge** — a hair too low blankets the surface, a hair too high
  clears it. Bisect it against a render rather than reasoning about it.


## Grass and meadow
- Vendor grass clumps are often real blade geometry (no opacity cards) - check the units of
  each volume against a known plant height before anything else (one grass volume was in mm
  where its tree volume was cm; read in cm, clover came out 1 m tall).
- Scatter: `scatter.meadow_layer_group(scatter.load_scatter_on_surface())` - Blender's own
  *Scatter on Surface* (native, Poisson/random, collection + Pick Instance) wrapped with mask
  fields: species patch noise, a **shared** bare-soil noise (the ground shader opens to soil with
  the same 4D noise, `terrain.BARE_W`, so bare spots show earth), clearance from the pad, and
  the **camera frustum + distance** (only what the camera can see; the crest hides the rest).
  One object per species; Align Rotation off (grass grows up, gravitropism), small random lean.
- Density is set by clump size: a few-blade lawn clump needs ~200 /m2 to close the sward
  (30 /m2 left mostly soil). ~0.5-1 M instances render fine on 8 GB; unique meshes cost memory,
  instances barely.
- Blade material `materials.vegetation.blade_material`: Principled + Translucent added (green leaf
  R ~0.10-0.15, T ~0.05-0.10 at the 550 nm green peak, lower across the rest of the visible), roughness ~0.45 (waxy cuticle), per-instance value
  0.8-1.15 and a patchy straw/dry mix on the instance location (RULES MAT_05, MAT_06). A grass canopy's
  visible albedo is only ~0.05-0.1: under a high-contrast AgX look it sinks - choose a softer
  look rather than brightening the albedo.
- Mixed species read as pasture: a dense low carpet + tuft drifts + broad-leaf (clover) patches
  + sparse seed heads/flowers.
