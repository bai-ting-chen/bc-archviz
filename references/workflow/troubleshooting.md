# Troubleshooting

Use when: an error message appears, or a render shows something unexpected and the cause is not yet
known. Generic problems only: a problem that belongs to one material or effect is in that file's
§5 Troubleshooting.

Each entry: the symptom as you meet it; **Seen as:** the exact text, for problems that print one;
**Cause**; **Check:** the order to test, where one symptom has several causes; **Fix**.

## Connection and execution

### Blender MCP cannot connect
Seen as: `Cannot connect to Blender at 127.0.0.1:9876. Ensure Blender is running with the MCP addon enabled and the server started.`
Cause: nothing listens on port 9876: Blender is closed, the `mcp` add-on is off or its server did not
start, or *Allow Online Access* is off (needed even for localhost). No crash log is not proof of a
clean exit.
Check: Blender process running → add-on enabled with autostart → *Allow Online Access* → port 9876 listening.
Fix: correct the first check that fails, then relaunch. See [pipeline.md](../scene/pipeline.md) › Install.

### Blender MCP times out
Seen as: `Blender connection timed out at 127.0.0.1:9876`
Cause: Blender is running but has not answered in time: a render or a long script holds it.
Fix: check what Blender is doing before sending more; never relaunch while a render runs (RULES AGT_04).
Split long scripts into shorter calls. See [pipeline.md](../scene/pipeline.md) › MCP tools.

### Blender MCP returns nothing or garbage
Seen as: `Empty response from Blender`, `Invalid response from Blender at 127.0.0.1:9876: …` or
`Socket error communicating with Blender at 127.0.0.1:9876: …`
Cause: Blender closed or the add-on failed during the call (on Windows a closed Blender usually gives
the socket error).
Fix: check whether Blender is still running and re-read the scene state before retrying a write.

### Host tool cannot import numpy or Pillow
Seen as: `ModuleNotFoundError: No module named 'numpy'` (or `'PIL'`) from `refmatch.py` / `imgstats.py`
Cause: the script ran on an interpreter without numpy and Pillow.
Fix: run host tools with the MCP venv python (`%LOCALAPPDATA%\BlenderMCP\venv\Scripts\python`), or
`pip install numpy pillow` into that venv. See [pipeline.md](../scene/pipeline.md) › Install.

### Edited look script fails to run
Seen as: `syntax error, nothing sent to Blender: <file>:<line>: <msg>` from `study_run.py`
Cause: a scripted edit appended a `# reason` comment to a line that continues a call, so the rest of
the call became a comment.
Fix: put the comment on its own line above the value, or edit with the Edit tool. See
[pipeline.md](../scene/pipeline.md) › Iteration loop.

### Poly Haven download fails with HTTP 52x
Seen as: `HTTP Error 520: …` to `HTTP Error 525: …` from `polyhaven_fetch.py`
Cause: Cloudflare in front of Poly Haven returned a server-side error.
Fix: check for a partial or existing download, then retry the same request a bounded number of
times; stop and report a persistent failure. See [pipeline.md](../scene/pipeline.md) › Assets.

### Script works headless, fails in the UI
Seen as: `RuntimeError: Operator bpy.ops.… .poll() Context missing active object` from a UI startup script
Cause: a UI startup script runs operators in a different context from a background run.
Fix: wrap operators in `temp_override`. See [blender-api-traps.md](../scene/blender-api-traps.md).

### Rook call hangs, "dispatcher busy", or a file won't open
Seen as: a Rook call that returns nothing for ~2 min, then a timeout or "dispatcher busy"
Cause: a long script still running on Rhino's UI thread, or a modal dialog (save changes?, crash
report) blocking every call.
Check: Rhino process CPU → a dialog on Rhino's screen → the target document's state.
Fix: wait for active work; a dialog only the user can dismiss. Split future calls and use
closed-form layouts instead of per-element curve queries. Never blindly retry writes or terminate
Rhino; that is the user's decision. See [pipeline.md](../scene/pipeline.md) › Rhino reference.

### `bpy_struct[key] = val: id properties not supported` on a GN modifier
Seen as: `bpy_struct[key] = val: id properties not supported`
Cause: Geometry Nodes interface inputs need the Blender-version-specific setter.
Fix: 5.2 inputs: `effects.edge_wear.set_input(mod, name, value)`. See [blender-api-traps.md](../scene/blender-api-traps.md).

### LuxCore crashes at export
Seen as: `EXCEPTION_ACCESS_VIOLATION` in `pyluxcore.pyd`, no Python error
Cause: a native mapping's `uvindex` points at a missing UV layer (-1).
Fix: build every UV layer the tree references on every run, even when the map itself is cached; or
correct `uvindex` before export. See [luxcore.md](../renderer/luxcore.md#native-luxcore-materials-scriptsblenderrendererluxcoreluxcorepy).

## Camera and lighting

### Camera framing far off after setting lens shift
Cause: with `sensor_fit = HORIZONTAL`, `shift_x/shift_y` are fractions of the frame **width** even on a
portrait frame, and +shift_x moves the frame right.
Fix: the shift formulas in lighting-camera.md › Recreating a reference › 1. Camera; check by
projecting a far point with `world_to_camera_view`. See [lighting-camera.md](../scene/lighting-camera.md).

### Scripted camera faces the wrong way, or a huge lens shift
Cause: `matrix_world` is stale after setting the rotation.
Fix: `view_layer.update()` before reading it (done in `straighten_verticals`). See [lighting-camera.md](../scene/lighting-camera.md).

### Camera from a Rhino named view frames wider or narrower
Cause: Rhino's lens length on a square view is the FOV of a 24 mm frame side.
Fix: same lens with `sensor_width = 24` and a square render; match the frustum. See
[pipeline.md](../scene/pipeline.md) › Rhino reference.

### Render white, or exposure ignored
Cause: `archviz.render_setup` resets the view exposure, so calling it after `physical_camera` wipes it.
Fix: call `render_setup` before `physical_camera`. See [blender-api-traps.md](../scene/blender-api-traps.md).

### Material or light change has no visible effect
Cause: a stale mesh or dependency graph, so the render still uses the old data.
Fix: `update_tag()` and `view_layer.update()`, then prove the change with a control (RULES VAL_02).
See [validation.md](../review/validation.md).

### Lamp or bulb invisible in the render
Cause: camera visibility depends on the light type and the Blender version.
Fix: check `visible_camera` and confirm the actual source in a small control. See [lighting-camera.md](../scene/lighting-camera.md).

### IES or point light much dimmer than the hand calculation
Cause: its sphere (radius) sits partly inside the ceiling or housing.
Fix: centre it radius + 2 mm clear (lighting-camera.md › IES). See [lighting-camera.md](../scene/lighting-camera.md).

### Colour cast from a pool or glass
Cause: a lens or emitter reaches surfaces through water or glass as *transmission* rays; visibility
follows the last bounce, so turning diffuse off alone still leaks.
Fix: `interior.lit_once()` (`visible_diffuse` and `visible_transmission` off). Ray visibility is an
emitter-path approximation; declare its bias (RULES REN_02). See [lighting-camera.md](../scene/lighting-camera.md).

### Unwanted scallops on a washed wall
Cause: spots used as wall washers.
Fix: a linear source along the wall. See [lighting-camera.md](../scene/lighting-camera.md).

### Image too cold after white balance
Cause: the white-balance temperature names the light rendered neutral; warming depends on the current
neutral point and tint.
Fix: use the current warming and tint procedure and compare the whole reference image before changing
the temperature. See [lighting-camera.md](../scene/lighting-camera.md).

### Glazing far darker than the reference
Cause: the room seen through it or the environment it reflects is too dark; Fresnel depends on angle and IOR.
Check: room lighting → HDRI reflection direction, against the reference.
Fix: correct the darker of the two; declare any added room light. See [lighting-camera.md](../scene/lighting-camera.md).

### An area renders black that is bright in the reference
Cause: the model may be roofed where the reference is open to the sky.
Fix: check sky access over that area against the reference. See [lighting-camera.md](../scene/lighting-camera.md).

### House edge crisp against a soft HDRI backplate
Cause: the rendered subject and the photographed backplate have different depth-of-field softness.
Fix: slight DOF in front of the subject (lighting-camera.md › Soft backplate). See [lighting-camera.md](../scene/lighting-camera.md).

## Materials, geometry and images

### Imported object has 0 faces
Cause: the .3dm has no cached render mesh for it.
Fix: force render meshes in an owned export; extract mesh data without modifying or saving the
user's document. See [pipeline.md](../scene/pipeline.md) › Rhino reference.

### Rhino boxes or slabs hang below their datum
Cause: `Extrusion.Create` follows the curve's plane normal, so a clockwise outline extrudes down.
Fix: `Surface.CreateExtrusion(curve, Vector3d(0, 0, h))` + `CapPlanarHoles`. See [pipeline.md](../scene/pipeline.md) › Rhino reference.

### GN geometry renders with its source's material
Cause: Object Info and Collection Info geometry keeps the source's materials.
Fix: a Set Material node on the instanced geometry. See [blender-api-traps.md](../scene/blender-api-traps.md).

### One long line runs down the camera axis on floor and ceiling
Cause: a tiled map's joint line at UV 0 = world 0, which is usually the camera axis.
Fix: offset the UVs by a fraction of a tile. See [texture-selection.md](../materials/texture-selection.md) › Tiled maps.

### Visible joint grid on walls or a curved wall
Cause: the map's tile edges, wherever it repeats in both directions.
Fix: rotate or flatten the map (texture-selection.md › Tiled maps). See [texture-selection.md](../materials/texture-selection.md).

### Relief vanishes on a bright wall
Cause: near display value ~0.8, AgX's highlight roll-off flattens relief shading: grain, steps and fins disappear.
Fix: match the reference's typical wall, not its brightest patch; lower the base or the exposure. See [physical-ranges.md](../materials/physical-ranges.md).

### Water, haze or fog volume murky and dark
Cause: `cycles.volume_bounces` defaults to 0, so Volume Scatter only removes light.
Fix: 2-4 for absorbing water and light haze; ~8 for dense fog (`atmosphere.volume_render_settings`).
See [blender-api-traps.md](../scene/blender-api-traps.md).

### Strength preview speckles on water or glass
Cause: behind a transparent layer the AOV holds only part of the surface; dividing by it explodes.
Fix: rescale only dry opaque pixels with plausible multipliers. See [validation.md](../review/validation.md).

### Multilayer EXR seems to hold only Combined
Cause: Blender 5.2 writes multi-part EXRs; the reader opened only the first part.
Fix: read every part (`seek_subimage`) with the bundled OpenImageIO. See [blender-api-traps.md](../scene/blender-api-traps.md).

## LuxCore

### LuxCore saved image noisy though OIDN ran
Cause: the denoised image is a separate `DENOISED` pass; a plain save writes the raw pipeline.
Fix: route `DENOISED` through the compositor. See [luxcore.md](../renderer/luxcore.md).

### Cloudy blotches on smooth walls or ceiling after OIDN
Cause: fireflies from caustic-bounce paths, which OIDN smears into clouds.
Fix: radiance clamping, not more time (`engine_setup` sets it; luxcore.md › Fireflies). Clamping is
biased; disclose it (RULES REN_02). See [luxcore.md](../renderer/luxcore.md).

## Final output

### Saved final is grainy after a stop or cancel
Cause: stopping or cancelling may skip the denoiser and the compositor.
Fix: Cycles: `finals.py -- denoise` from the passes EXR; LuxCore: `from_passes.py`. See [render-settings.md](../renderer/render-settings.md).

### No-limit final renders only one block ("0/4 tiles")
Cause: Cycles auto-tiling is still on.
Fix: auto-tile off and tile size above the frame (`finals.setup_unlimited`). See [render-settings.md](../renderer/render-settings.md).
