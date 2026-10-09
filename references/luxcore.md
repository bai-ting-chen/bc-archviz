# LuxCore — the caustics renderer (RULES 2a)

Cycles stays the default. Switch to LuxCore when caustics or heavy refraction carry the shot:
sun through patterned glass or glass block, glass on water, any multi-interface glass. Measured
on sun → 4 glass interfaces → diffuse floor (caustics.md › Decision): only LuxCore CPU light
tracing gave a clean, energy-correct caustic.

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
h = sc.luxcore.halt; h.enable = h.use_time = True; h.time = secs
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
- Memory is small: a corridor of ~770 instanced 73 k-quad blocks peaked at 0.7 GB RAM.
- Resolution vs time: noise ∝ 1/√(samples per pixel), samples ∝ time / pixels. Measure one
  preview, then scale (4× pixels for 5.3× time = 1.33× samples per pixel).

## Matching Cycles units (do this once per scene; check on an open sunlit patch)
- Render the same frame in both engines; a floor patch lit through an *open* opening is the
  calibration. Agreement within ~2 % means lights and sky match; differences elsewhere are
  light transport, not units.
- **Sun:** `light.luxcore.light_type = "sun"` (physical, spectral, warm, hittable). The
  `distant` type with `theta` = half-angle and Normalize on takes `gain` = W/m² like Cycles, but
  **camera rays never hit it** → no sun glints through glass. Calibrate `sun_sky_gain` for the
  physical sun: measured 3.62e-5 ≙ Cycles sun Strength 3 W/m² normal (scales linearly; turbidity
  2.2). Re-measure if turbidity or the version changes.
- **Sky:** `world.luxcore.use_cycles_settings = True` converts a flat Background colour. An HDRI
  through the Cycles world is converted **without the Mapping rotation** — set the native light:
  `world.luxcore.light = "infinite"`, `.image`, `.gain = Cycles Background Strength`,
  `.rotation = −radians(Cycles Mapping Z)`. The sign was verified on a sun patch
  (Cycles 579/146 px 0.678 vs LuxCore 582/146 px 0.684).

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

## Final in the open UI (RULES 10b)
No halt condition on a final (`halt.enable = False`): it renders until the user presses Esc.
On Esc LuxCore still draws the final film, but Blender fires `render_cancel`, not
`render_complete` — register the save handler on **both** (and remove it from both), or a
user-stopped final is never saved. The OIDN pass is produced when the session stops; check the
saved EXR is the denoised one.
Build the scene in the UI session, save the .blend, then from a timer
`bpy.ops.render.render("INVOKE_DEFAULT")` inside `temp_override(window=…)` with a
`render_complete` handler that saves `Render Result` (`save_render`, composited = denoised)
and the graded PNGs. If no render window opens, switch the largest area to an Image Editor on
`Render Result` — LuxCore refreshes it live. The first passes look like scattered dots; the
denoiser runs once at the end.
