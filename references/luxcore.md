# LuxCore — the caustics renderer (RULES 2a)

When to use it: RULES 2a; the measured comparison is in caustics.md › Decision.

## Install (BlendLuxCore 2.11, official support for Blender 4.5 LTS and 5.2 LTS)
- `gh release download <tag> -R LuxCoreRender/BlendLuxCore -p "BlendLuxCore-*.zip"` into an
  empty folder; compare the asset's sha256 (`gh release view --json assets`).
- `blender -b -c extension install-file -r user_default --enable <zip>`. On first enable it
  installs the `pyluxcore` wheel (needs online access). Check: `pyluxcore.Init();
  pyluxcore.GetOpenCLDeviceList()` lists the GPU as OPENCL_GPU and CUDA_GPU.
- Extension module name: `bl_ext.user_default.blendluxcore`. GPU backend (OpenCL / CUDA) is an
  add-on preference: `preferences.addons[...].preferences.gpu_backend`.
- The first GPU render compiles kernels for minutes (cached afterwards in
  `%TEMP%\luxcorerender.org\ocl_kernel_cache`).

## Engine settings that converge caustics
```python
sc.render.engine = "LUXCORE"; cfg = sc.luxcore.config
cfg.engine = "PATH"; cfg.device = "CPU"
cfg.path.hybridbackforward_enable = True            # "Add Light Tracing": light paths splat on the film
cfg.path.depth_total, depth_diffuse, depth_glossy, depth_specular = 32, 4, 16, 32
h = sc.luxcore.halt                                 # tests/previews: a time budget; finals: h.enable = False
h.enable = h.use_time = True; h.time = secs
h.use_samples = False; h.use_noise_thresh = False   # halt-by-samples is ON by default (stops at "100 %")
tm = cam.data.luxcore.imagepipeline.tonemapper      # linear, no auto, for measurement and AgX later
tm.type = "TONEMAP_LINEAR"; tm.use_autolinear = False; tm.linear_scale = 1.0
```
- **Light tracing is CPU-only in practice.** On the GPU (PATHOCL, OpenCL or CUDA) the image is
  identical at 20/50/90 % light rays — it does nothing. GPU PATH without it is just camera
  paths: no caustic. BlendLuxCore's light-ray % is inverted into LuxCore's
  `path.hybridbackforward.partition` (100 % → 0).
- BIDIR (CPU only) converges the same caustic far more noisily. The PhotonGI caustic cache
  (GPU) is fast but biased: blurred by its lookup radius and ~25 % dark in a measured case.
- Memory is small with instancing: ~800 instances of a 73 k-quad mesh peaked under 1 GB RAM.
- Resolution vs time: noise ∝ 1/√(samples per pixel), samples ∝ time / pixels. Measure one
  preview, then scale (4× pixels for 5.3× time = 1.33× samples per pixel).

## Daylight in LuxCore
Daylight is the HDRI (RULES 8a): LuxCore's `infinite` light importance-samples the map, so its
sun disc both casts the caustics (light tracing emits from it) and appears as glints through
glass (camera paths hit it). The lamp settings below are for tests and controls without an HDRI.

## Matching Cycles units (do this once per scene; check on an open sunlit patch)
- Render the same frame in both engines; a floor patch lit through an *open* opening is the
  calibration. Agreement within ~2 % means lights and sky match; differences elsewhere are
  light transport, not units.
- **Sun lamp (tests/controls only):** `light.luxcore.light_type = "sun"` (physical, spectral, warm, hittable). The
  `distant` type with `theta` = half-angle and Normalize on takes `gain` = W/m² like Cycles, but
  **camera rays never hit it** → no sun glints through glass. Calibrate `sun_sky_gain` for the
  physical sun: measured 3.62e-5 ≙ Cycles sun Strength 3 W/m² normal (scales linearly; turbidity
  2.2). Re-measure if turbidity or the version changes.
- **Sky:** `world.luxcore.use_cycles_settings = True` converts a flat Background colour. An HDRI
  through the Cycles world is converted **without the Mapping rotation** — set the native light:
  `world.luxcore.light = "infinite"`, `.image`, `.gain = Cycles Background Strength`,
  `.rotation = −radians(Cycles Mapping Z)` (sign verified: the sun patch lands on the same
  pixels at the same brightness in both engines).

## Materials LuxCore can render
Build Cycles node materials and set `material.luxcore.use_cycles_nodes = True`. The converter
handles: Principled, Glass, Diffuse, Glossy, Refraction, Transparent, Translucent, Emission,
Mix/Add shader, Image Texture, Normal Map, Bump, MixRGB (incl. clamp), Math, Map Range, Color
Ramp, Hue/Sat, Bright/Contrast, Gamma, Invert, RGB, Value, Separate/Combine XYZ, Object Info,
Geometry, Checker. **Not:** Noise/Voronoi/Wave or any procedural texture, Mapping, Texture
Coordinate, Separate Color. So:
- real-size UVs written into the mesh (`archviz.box_uv(obj, texture_size_m)`), no Mapping node;
- procedural looks (terrazzo, speckle, grime) **baked to images** first (numpy or a Cycles bake);
- roughness from an ARM map via Separate XYZ (`Y` = green).
Setting `use_cycles_nodes` from a script logs a harmless traceback (it tries to show a node
editor); the value still applies.

## Output
- The OIDN result (`sc.luxcore.denoiser.enabled = True`) is a **separate `DENOISED` pass**; a
  plain EXR saves the raw pipeline. Route it through the 5.x compositor:
  `ct = bpy.data.node_groups.new("Comp", "CompositorNodeTree")`, an `Image` output socket on
  `ct.interface`, Render Layers `DENOISED` → Group Output, `sc.compositing_node_group = ct`,
  `sc.render.use_compositing = True` (after the engine and denoiser are set and
  `view_layer.update()`, so the pass exists).
- Save the linear EXR, then graded PNGs from it (AgX at a few EVs) with `img.save_render(p, scene=sc)`.

## Final in the open UI
Mechanics: pipeline.md › *Final render in the open UI*. LuxCore specifics: `halt.enable =
False`; on Esc it still draws the final film and produces the OIDN pass, so the saved
`Render Result` (composited = DENOISED) is the clean image — check it. The live view refreshes in
an Image Editor on `Render Result`; the first light-tracing passes look like scattered dots.
