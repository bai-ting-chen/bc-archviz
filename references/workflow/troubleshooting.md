# Troubleshooting

## Connection and execution

### MCP port 9876 not listening

Cause: A missing listener has several possible causes; no crash log is not proof of a clean exit.
Fix: Inspect Blender process, port 9876, add-on state and Allow Online Access before relaunching. See [pipeline.md](../scene/pipeline.md).

### `refmatch.py` / `imgstats.py`: No module named numpy

Cause: The host interpreter lacks numpy or Pillow.
Fix: `pip install numpy pillow` into the MCP venv. See [pipeline.md](../scene/pipeline.md).

### Edited look script fails to run

Cause: A scripted edit put a `#` comment mid-call.
Fix: Syntax-check the scripts in the runner (pipeline). See [pipeline.md](../scene/pipeline.md).

### Poly Haven download `HTTP Error 52x`

Cause: The download endpoint returned a server-side 52x response.
Fix: Check any existing download, then retry the same request a bounded number of times; stop and report persistent server failures. See [pipeline.md](../scene/pipeline.md).

### Script works headless, fails in the UI ("Context missing active object")

Cause: UI startup scripts have a different operator context from background runs.
Fix: Operators need `temp_override` in a UI startup script (api-traps). See [api-traps.md](../scene/api-traps.md).

### Rook call hangs / "dispatcher busy" / file won't open

Cause: A long script may still be running or a modal dialog may block the dispatcher.
Fix: Inspect responsiveness, CPU/process state and target state before any further write. Wait for active work; split future calls and use closed-form layouts instead of per-element curve queries. Never blindly retry or terminate Rhino; destructive termination needs the user’s decision. See [pipeline.md](../scene/pipeline.md).

## Camera and lighting

### Camera framing far off after setting lens shift

Cause: Shift units/sign trap.
Fix: Probe with `world_to_camera_view` (lighting-camera). See [lighting-camera.md](../scene/lighting-camera.md).

### One long line runs down the camera axis on floor and ceiling

Cause: A texture's panel joint at UV 0 = world 0.
Fix: Offset the UVs (materials). See [texture-selection.md](../materials/texture-selection.md).

### Material/light change has no visible effect

Cause: The mesh or dependency graph may be stale.
Fix: Check stale mesh/depsgraph state with update_tag() and view_layer.update(); prove the result using VAL_02. See [validation.md](../review/validation.md).

### Colour cast from a pool or glass

Cause: A lens seen through water by transmission rays.
Fix: `interior.lit_once()` (lighting-camera) Ray visibility here is an emitter-path approximation; declare its bias under REN_02. See [lighting-camera.md](../scene/lighting-camera.md).

### Unwanted scallops on a washed wall

Cause: Spots used as washers.
Fix: A linear source along the wall (lighting-camera). See [lighting-camera.md](../scene/lighting-camera.md).

### Image too cold after white balance

Cause: White balance temperature denotes the light rendered neutral; warming depends on the current neutral point and tint.
Fix: Use the current warming/tint procedure and compare the entire reference image before changing temperature. See [lighting-camera.md](../scene/lighting-camera.md).

### `bpy_struct[key] = val: id properties not supported` on a GN modifier

Cause: The GN interface socket needs the Blender-version-specific setter.
Fix: 5.2 inputs: `materials.edge_wear.set_input(mod, name, value)`. See [api-traps.md](../scene/api-traps.md).

### IES / point light much dimmer than the hand calc

Cause: Its sphere (radius) is partly inside the ceiling or housing.
Fix: Centre it radius + 2 mm clear (lighting-camera › IES). See [lighting-camera.md](../scene/lighting-camera.md).

### Scripted camera faces the wrong way / huge lens shift

Cause: `matrix_world` stale after setting rotation.
Fix: `view_layer.update()` (fixed in `straighten_verticals`). See [lighting-camera.md](../scene/lighting-camera.md).

### Lamp/bulb invisible in render

Cause: Camera visibility depends on light type and Blender version.
Fix: Check visible_camera and confirm the actual source in a small control. See [lighting-camera.md](../scene/lighting-camera.md).

### Glazing far darker than the reference

Cause: The transmitted room or reflected environment may be too dark; Fresnel depends on angle and IOR.
Fix: Check room lighting and HDRI reflection direction against the reference; declare any added room light. See [lighting-camera.md](../scene/lighting-camera.md).

### Render white / exposure ignored

Cause: `archviz.render_setup` sets view exposure.
Fix: Call it before `physical_camera`. See [lighting-camera.md](../scene/lighting-camera.md).

### Light triangles hanging below an arris

Cause: The leak/raycast field was evaluated after chip geometry.
Fix: Compute the leak field on the clean shell before chip geometry. See [edge-wear.md](../materials/edge-wear.md).

### House edge crisp against a soft HDRI backplate

Cause: The rendered subject and photographed HDRI backplate have different depth-of-field softness.
Fix: Slight DOF in front of the subject (lighting-camera.md > Soft backplate). See [lighting-camera.md](../scene/lighting-camera.md).

### Camera from a Rhino named view frames wider/narrower

Cause: Rhino's lens length refers to the frame's short side on a square view.
Fix: Match the frustum (pipeline.md). See [pipeline.md](../scene/pipeline.md).

## Materials and geometry

### Whole floor/slab gets edge grime

Cause: Object without the GN modifier reads `edge_dist` = 0 = "on an arris".
Fix: Gate it (edge-wear). See [edge-wear.md](../materials/edge-wear.md).

### Imported object has 0 faces

Cause: No cached render mesh in the .3dm.
Fix: Force render meshes in an owned export mesh. Extract mesh data without modifying or saving the user’s source document. See [pipeline.md](../scene/pipeline.md).

### GN geometry renders with source's material

Cause: Object Info instances inherit their source material.
Fix: Set Material. See [api-traps.md](../scene/api-traps.md).

### An area renders black that is bright in the ref

Cause: The model may be roofed where the reference is open to the sky.
Fix: Check sky access. See [lighting-camera.md](../scene/lighting-camera.md).

### Visible joint grid on walls / a curved wall

Cause: Texture tile edges.
Fix: Rotate/flatten the map (materials › Tiled maps). See [texture-selection.md](../materials/texture-selection.md).

### Water/haze/fog volume murky and dark

Cause: Check the volume-bounce setting for this Blender version.
Fix: `cycles.volume_bounces` defaults to 0 (api-traps › Render). See [api-traps.md](../scene/api-traps.md).

### Rhino boxes/slabs hang below their datum

Cause: `Extrusion.Create` follows the curve normal.
Fix: `Surface.CreateExtrusion` (pipeline). See [pipeline.md](../scene/pipeline.md).

### Ripples look fake or stretched

Cause: A shader noise bump or stretched mapping does not reproduce the sampled water geometry.
Fix: Ocean geometry on a finer mesh, never stretch (materials › Water). See [water.md](../materials/water.md).

### Imported .max: trunk/twigs missing, leaves rendered as bark, bark squashed

Cause: Stock io_scene_max import.
Fix: Use `max_import.load` and its checks (max-import.md). See [max-import.md](../scene/max-import.md).

### Back-lit leaves glint white

Cause: The imported glossiness scalar can override the wired map.
Fix: The importer's stored glossiness scalar used instead of the wired glossiness map (max-import.md › Materials). See [max-import.md](../scene/max-import.md).

### Grass sinks dark / lawn reads grey when wet

Cause: Canopy albedo and grazing-angle wet-film reflection can suppress saturation.
Fix: Canopy albedo is ~0.05-0.1 (softer AgX look); wet sheen at grazing - darker base ([README.md](../materials/wet-surfaces.md)). See [wet-surfaces.md](../materials/wet-surfaces.md).

### Foam reads as snow cones with black holes

Cause: Spiky short boils + a hard foam switch over a dark trench.
Fix: Rounded chop, milky subsurface whitewater, soft foam mask ([water-features.md](../materials/water-features.md)). See [water-features.md](../materials/water-features.md).

### Black band at a waterline seen through glass

Cause: An open water sheet may expose a dark void below troughs.
Fix: In whitewater/trough contexts, check for an open water sheet over a void and add the scoped milky body below troughs. Clear pools keep their clear optical body; do not silently make them opaque. See [water-features.md](../materials/water-features.md).

### Splash drops read as a dark band

Cause: Clear drops in soft light refract the dark surroundings.
Fix: Fewer, higher, spread ([water-features.md](../materials/water-features.md)). See [water-features.md](../materials/water-features.md).

## LuxCore and caustics

### Submerged surfaces black under lamps

Cause: Shadow rays can't pass refraction.
Fix: MNEE with a diced top plane (caustics.md). This is a transport/tessellation diagnostic, subject to [renderer selection REN_03](../renderer/renderer-choice.md). See [caustics.md](../materials/caustics.md).

### LuxCore render stops after a few seconds at "100 %"

Cause: Halt-by-samples is on by default.
Fix: `halt.use_samples = False` (luxcore.md). See [luxcore.md](../renderer/luxcore.md).

### LuxCore GPU light tracing changes nothing

Cause: CPU light tracing may be disabled even with GPU camera paths.
Fix: Light tracing runs on CPU threads: Devices › *Use CPUs* on, GPU light-ray field (`_opencl`) 100 % (luxcore.md). See [luxcore.md](../renderer/luxcore.md).

### LuxCore caustic final takes many hours

Cause: Camera paths may be running CPU-only.
Fix: Check GPU plus Use CPUs for CPU light tracing; benchmark this hardware and scene rather than assuming a fixed speedup. Preserve required relief geometry. See [luxcore.md](../renderer/luxcore.md).

### LuxCore test sun casts but never glints through glass

Cause: `distant` lights are never hit by camera rays.
Fix: Use the `sun` type (luxcore.md). Use this only in an isolated non-HDRI control (LGT_02), never as a second scene daylight source. See [luxcore.md](../renderer/luxcore.md).

### LuxCore saved image noisy though OIDN ran

Cause: The denoised image is a separate DENOISED pass.
Fix: Route it through the compositor (luxcore.md). See [luxcore.md](../renderer/luxcore.md).

### Caustics a flat glow on far surfaces / one S-shaped bright line per pattern tile

Cause: Relief too steep (focal length cm) / single-frequency pattern.
Fix: Size relief slope from receiver distance, randomise (caustics.md › Designing a refractive relief). See [caustics.md](../materials/caustics.md).

### Cloudy blotches on smooth walls/ceiling after OIDN (LuxCore)

Cause: Fireflies from caustic-bounce paths.
Fix: Radiance clamping, not more time (luxcore.md › Fireflies). Clamping is biased; disclose it under REN_02. See [luxcore.md](../renderer/luxcore.md).

### LuxCore crashes at export, `EXCEPTION_ACCESS_VIOLATION` in pyluxcore

Cause: A native mapping references a missing UV layer.
Fix: Create and validate the referenced UV layer, or correct uvindex before export. See [luxcore.md](../renderer/luxcore.md#native-luxcore-materials-scriptsblendermaterialsluxcorepy).

### Caustics on a wall look like vertical streaks

Cause: A grazing receiver view stretches the apparent caustic pattern.
Fix: Seen at a grazing angle; judge on a face-on surface (caustics.md). See [caustics.md](../materials/caustics.md).

## Final output

### Saved final is grainy after a stop or cancel

Cause: Stopping/cancelling may skip the denoiser and compositor.
Fix: Cycles: `finals.py -- denoise` from the passes EXR; LuxCore: `from_passes.py`. See [render-settings.md](../renderer/render-settings.md).

### No-limit final renders only one block ("0/4 tiles")

Cause: Cycles auto-tiling is still enabled.
Fix: Auto-tiling: tile off + tile size > frame (`finals.setup_unlimited`). See [render-settings.md](../renderer/render-settings.md).
