# LuxCore — setup and settings

When to choose LuxCore: [renderer-choice.md](renderer-choice.md).

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
Start every LuxCore render with `renderer.luxcore.luxcore.engine_setup()`
(`scripts/blender/renderer/luxcore/engine.py`); do not set these by hand.
```python
luxcore.engine_setup(halt_s=600)   # tests/previews: a time budget in seconds
luxcore.engine_setup()             # finals: no halt (finals.start_in_ui also clears it)
```
What it sets, against BlendLuxCore's defaults:
- PATH engine, GPU camera paths (`device = "OCL"`, CUDA backend) plus *Use CPUs*, light
  tracing on with the GPU light-ray field at 100 % (below);
- depths total / diffuse / glossy / specular 32 / 4 / 16 / 32 (default 12 / 4 / 4 / 12);
- radiance clamping 2000 on camera paths (default off; see Fireflies);
- halt by time only. **Halt by samples is on by default at 32 samples**, so a time budget set
  by hand stops at "Samples per pixel 100 %" within seconds. `set_halt(seconds)` turns samples
  and noise halts off;
- the active camera's tonemapper linear, no auto, scale 1 (for measurement and AgX later).
- **Light tracing runs only on CPU threads — on the GPU engine too.** In PATHOCL the GPU traces
  camera paths and skips the caustic ones; light paths come from the native CPU threads, which
  exist only with Devices › *Use CPUs* (`devices.use_native_cpu`, default on). With it off, GPU
  PATH + light tracing renders camera paths only: no caustic at any light-ray %. The GPU mode has
  its own light-ray field (`hybridbackforward_lightpartition_opencl`, default 100 % = the CPU
  threads trace only light paths); the CPU field (`hybridbackforward_lightpartition`, default
  20 %) does nothing there. BlendLuxCore's % is inverted into LuxCore's
  `path.hybridbackforward.partition` (100 % → 0).
- **GPU + CPU is the fast setup**, same image as CPU-only (bias < 1 %). Measured at equal time
  against a 14 h CPU reference, per region (6-core CPU + mid-range RTX): walls and ceiling — whose
  noise is camera paths — reached equal noise 4–6× sooner, glass seen from inside 4×, a floor
  lit purely by the caustic 2.2× (it is still bound by the CPU's light tracing). Never render LuxCore CPU-only (RULES REN_03).
- **Speed — what did not help** (same comparison): more light-ray share on CPU-only (the 20 %
  default was best overall; 50/80 % helped one wall and hurt everything camera-path lit);
  `light_strategy` POWER vs LOG_POWER (no change when the sun dominates); the env-light cache
  (no gain, −8 % bias on one wall). Light and sun paths are emitted over a disk of the scene's
  bounding sphere (`sunlight.cpp`, `infinitelight.cpp`), so far geometry — a large ground
  plane, a sky-dome mesh, distant context — wastes light paths: keep the scene tight to what
  the camera and the caustic need.
- **Geometry is not the cost; variance is.** Replacing a modelled relief (67 k faces per
  instanced block) by 12-face boxes raised throughput only 1.1–1.3× (camera / light paths) —
  the ceiling for any flat-glass shortcut, and it removes the caustic. Displacement is no
  shortcut: LuxCore tessellates it into real triangles at load (`shapes/displacement.cpp`),
  per object, losing instancing. A normal map does bend light-traced caustics (shading normals
  are used on light paths, with the adjoint correction), but costs texture lookups, loses
  parallax and edge refraction close up, and steep normals give dark seams. Model the relief.
- Measuring a speedup: render each variant raw for equal time at reduced resolution, score
  per region the relative RMSE of luminance against a long reference of the same scene
  (downsampled), and convert: k× lower error = k²× faster (noise ∝ 1/√t). Check bias too; a
  "faster" variant with a few % bias is a different image. Read LuxCore's own counters
  (`stats.renderengine.pass.eye` / `.pass.light`, `total.samplesec`) for throughput.
- BIDIR (CPU only) converges the same caustic far more noisily. The PhotonGI caustic cache
  (GPU) is biased: blurred by its lookup radius and ~25 % dark in one measured case; on a whole
  room (50 M photons, radius 0.03 m) it came out 50–220 % too bright and slower — not a shortcut.
- Memory is small with instancing: ~800 instances of a 73 k-quad mesh peaked under 1 GB RAM.
- Resolution vs time: noise ∝ 1/√(samples per pixel), samples ∝ time / pixels. Measure one
  preview, then scale (4× pixels for 5.3× time = 1.33× samples per pixel).

## Fireflies, clamping and the denoiser
- **Where they come from.** Hybrid back/forward splits the work (LuxCore source,
  `pathtracer.cpp`): light tracing renders light → specular… → one diffuse hit → camera (the
  caustic itself); camera paths skip exactly those. The *bounce of that caustic light* onto other
  surfaces (sun → glass → floor → ceiling → camera) is left to camera paths that must hit a
  0.53° sun through wavy glass by chance: rare, enormous samples. In a measured case two
  thirds of a ceiling's mean radiance sat in such samples, and **6 h left the raw noise where
  10 min had it** — time does not cure them.
- **OIDN turns them into blotches.** Fireflies are the worst denoiser input: the network keeps
  them as features and smears them into large soft clouds. A strongly textured surface hides
  the clouds; a smooth white one shows every one.
- **Fix: radiance clamping** (`engine_setup` sets it: `clamp=2000`; `clamp=None` turns it off; LuxCore
  `path.clamping.variance.maxvalue`). LuxCore clamps **only camera-path samples** ("I clamp only
  eye paths samples", `pathtracer.cpp`), each to the pixel's running mean + √value, so the
  light-traced caustics are untouched: caustic medians moved < 2 %, the ceiling's mean/median
  went 3.35 → 1.15 and its brightest raw pixel 21 698 → 38. 2000 and 10 000 gave the same image —
  the energy removed sits > 100× the pixel mean. BlendLuxCore's printed "recommended clamp value"
  is (mean film luminance × 10)², inflated by the fireflies themselves: an upper bound only.
  Check the clamped brightness with an energy balance (bounce ≈ albedo × view factor × source
  radiance) rather than trusting an unconverged unclamped mean.
- **Diagnose before fixing:** per region, raw *mean / median* (≈ 1 = clean; ≫ 1 = energy in rare
  samples) and the brightest pixel. Bright spots that sit on the **same pixels in an independent
  render** and span several pixels are caustic hot spots; single random pixels are fireflies.
- **Trap — a scripted sun hits glass:** BlendLuxCore's sun UI defaults Visibility › Specular
  (indirect) to off, but that default only reaches the exporter when the box is edited; a sun
  made by script exports `visibility.indirect.specular.enable = 1`, the developers' "fireflies
  generator". Light tracing ignores visibility flags, so setting
  `light.luxcore.visibility_indirect_specular = False` keeps the caustics; it does drop all
  sun-through-glass light reaching camera paths (bounce glow, glints), so try clamping first.
- **Do not:** use Architectural glass or a white Shadow Color on the glass — the light tracer
  stops at any shadow-transparent surface, so the caustics vanish; or raise the glossiness
  threshold above a glossy floor's roughness (the floor then counts as specular and its
  caustics fall between both halves).

## Daylight in LuxCore
Daylight is the HDRI (RULES LGT_02): LuxCore's `infinite` light importance-samples the map, so its
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
- **Per-instance variation converts:** Object Info › Random → `objectidnormalized`, and every
  instance of a collection gets its own ID automatically (do not set a manual LuxCore object ID
  on the source meshes). `renderer.luxcore.luxcore.glass_instance_tint()`.

## Native LuxCore materials (`scripts/blender/renderer/luxcore/luxcore.py`)
Needed when the converter cannot express it — notably **Image › Randomized Tiling**
(histogram-preserving blending after Burley: removes visible tile repeat; only when Wrap =
Repeat) and **2D Mapping › Randomized UV** (random rotation/scale/offset per object ID or mesh
island). Build: `bpy.data.node_groups.new(n, "luxcore_material_nodes")`,
`mat.luxcore.node_tree = tree; mat.luxcore.use_cycles_nodes = False`; nodes
`LuxCoreNodeMatOutput`, `LuxCoreNodeMatDisney`, `LuxCoreNodeTexImagemap` (`gamma` 2.2 colour /
1.0 data, `randomized_tiling`), `LuxCoreNodeTexMapping2D` (`uvindex` = the mesh's UV layer index),
`LuxCoreNodeTexColorMix` (`mode` "scale"/"mix"), `LuxCoreNodeTexSplitFloat3`.
`renderer.luxcore.luxcore.lux_textured(name, folder, mesh, dust_png)` does it from a map folder.
- **A `uvindex` that points at a missing UV layer (-1) crashes pyluxcore** at export
  (EXCEPTION_ACCESS_VIOLATION in `pyluxcore.pyd`, no Python error). Build every UV layer the
  tree references on every run, even when the map itself is cached.
- No AO texture and no usable dirt texture in LuxCore (Pointiness has no width control and cannot
  see where two objects meet): bake corner dust with Cycles ([edge-wear.md](../effects/edge-wear.md) › Concave corners).

## Output
- The OIDN result (`sc.luxcore.denoiser.enabled = True`) is a **separate `DENOISED` pass**; a
  plain EXR saves the raw pipeline. Route it through the 5.x compositor:
  `ct = bpy.data.node_groups.new("Comp", "CompositorNodeTree")`, an `Image` output socket on
  `ct.interface`, Render Layers `DENOISED` → Group Output, `sc.compositing_node_group = ct`,
  `sc.render.use_compositing = True` (after the engine and denoiser are set and
  `view_layer.update()`, so the pass exists).
- Save the linear EXR, then graded PNGs from it (AgX at a few EVs) with `img.save_render(p, scene=sc)`.

## Final in the open UI
Mechanics: [pipeline.md](../scene/pipeline.md) › *Final render in the open UI*. LuxCore specifics: no halt (`start_in_ui` clears it).
- **Two ways to stop, different results.** LuxCore's own Stop (render-window button;
  scriptable as `LuxCoreDisplaySettings.stop_requested = True` from
  `bl_ext.user_default.blendluxcore.properties.display`) ends normally: OIDN, compositor,
  `render_complete`. **Blender's cancel** (Esc in a Blender window, or the ✕ beside "Rendering…"
  in the main window's status bar) also runs OIDN but fires `render_cancel` and **skips the
  compositor, so the composited Render Result is the raw image.** An accidental click there ends
  a no-limit final; warn the user.
- So the save handler writes a **multilayer EXR of all passes** (api-traps › multilayer) and
  builds the finals from its `DENOISED` layer with `scripts/blender/renderer/finals/from_passes.py` — never from
  the composite. Check the result (grain on a smooth wall = raw saved by mistake).
- A cancelled LuxCore session cannot be resumed; the time spent is in the passes file only.
- The live view refreshes in an Image Editor on `Render Result`; the first light-tracing passes
  look like scattered dots. A snapshot mid-render: `Render Result.save_render(...)` over MCP.
