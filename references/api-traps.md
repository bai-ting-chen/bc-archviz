# Blender 5.2 API traps

## Nodes
- GN modifier inputs: `mod["Socket_N"]` fails; values live at `mod.properties.inputs.<id>.value`
  (empty `.name`; resolve via `node_group.interface.items_tree`) → `wear.set_input`. Group defaults
  are copied only at modifier creation. New code re-hits this with `mod[ident] = v`.
- Edge Angle (signed): convex arrises read **positive** on outward-normal Rhino meshes.
- ShaderNodeMix: hidden per-type sockets share names `A/B/Result` → `archviz.sock`.
- Noise Texture output: "Factor" in GN; index 0 is safest.
- Capture Attribute: socket index 1 is Selection — link by name.
- Object/Collection Info geometry keeps source materials → Set Material.
- Bump invert is a property (`bump.invert`), not a socket.
- `ShaderNodeSeparateRGB` / `CombineRGB` no longer exist in 5.2 (`Node type … undefined`): use
  Separate/Combine Color — or Separate XYZ when the material must also convert to LuxCore.
- `Material.use_nodes` / `World.use_nodes` log a DeprecationWarning (removal planned for 6.0);
  still required in 5.2.
- Noise Texture values cluster at 0.5 (sd ≈ 0.1): threshold near 0.5.
- No per-axis Extend: keep once-spanning UVs inside 0..1 with REPEAT.

- Noise Texture `W` input exists only with `noise_dimensions = "4D"` (KeyError otherwise) - set
  the dimensions first.
- Random Value (GN) has one output named "Value" in 5.2 (`outputs[1]` is out of range).
- Volume Scatter `phase = "MIE"` adds the `Diameter` input (um); set the phase first.
- Node-group menu inputs (e.g. *Scatter on Surface* "Instance Type") take the item name as a
  string: `node.inputs["Instance Type"].default_value = "Collection"`.

## Mesh / scene
- Subdivision adaptive: `use_adaptive_subdivision`, `adaptive_space='PIXEL'`, `adaptive_pixel_size`.
- After changing modifier inputs in background scripts: `obj.update_tag()` +
  `view_layer.update()` before reading evaluated meshes.
- `matrix_world` is stale right after a script sets `location`/`rotation_euler`: call
  `view_layer.update()` before reading it (`straighten_verticals` read a camera as pointing straight
  down: yaw −90°, lens shift −2·10¹⁶, black frame).
- After `bmesh.ops.delete`: `bm.faces.ensure_lookup_table()` before indexing.
- MCP context has no `bpy.context.object` after add-primitive operators → bmesh + `objects.new`.
- Editor operators need `bpy.context.temp_override(window=, area=, region=)`;
  `render.render('INVOKE_DEFAULT')` from MCP needs `temp_override(window=…)`.

## Camera
- `shift_x/shift_y` with `sensor_fit = HORIZONTAL` are fractions of the frame width (also on
  portrait frames); +shift_x moves the frame right. Probe with `world_to_camera_view`.
- `archviz.physical_camera()` resets lens/sensor fit — re-apply the solved shifts after it.

## MCP
- `execute_blender_code`: `result` must be a dict, not a string.
- Shader Attribute node on a missing attribute returns 0 (not an error) — gate masks that
  treat 0 as meaningful.

## Render / images
- `cycles.volume_bounces` defaults to **0**: Volume Scatter then only removes light (murky,
  dark water/haze). 2-4 for absorbing water and light haze; ~8 for dense forward-peaked Mie fog,
  which needs multiple scattering (`atmosphere.volume_render_settings`).
- Ray visibility (`visible_diffuse / visible_transmission …`) follows the type of the LAST bounce.
- Changing `light.type` (POINT → SPOT) keeps the datablock but the Python handle keeps the old
  subclass (`'PointLight' object has no attribute 'spot_size'`): re-fetch `bpy.data.lights[name]`.
- Lights created from Python default to `visible_camera = False`: a "visible bulb" point light
  renders nothing until you set it.
- Area lights emit along local −Z; with rotation (θ, 0, 0) the beam goes along (0, sin θ, −cos θ).
- Solidify on a sphere (thin glass shell): `offset` −1 keeps the outer surface where it was,
  so the shell grows inward and the silhouette does not change.
- `view_settings.white_balance_temperature`: lower = cooler.
- `Image.save()` on float images applies view transform + exposure → for data EXRs use
  `img.save_render(path)` with OPEN_EXR 32-bit.
- Pixel analysis: `img.pixels.foreach_get(np_array)` is linear for **float** images only; 8-bit
  sRGB textures come back sRGB-encoded — decode (`((v+0.055)/1.055)**2.4`) before measuring an
  albedo (encoded means read about twice the linear value on mid-grey maps).
- Compositor in 5.x is a node group: `bpy.data.node_groups.new(name, "CompositorNodeTree")`,
  an output socket via `tree.interface.new_socket("Image", in_out="OUTPUT",
  socket_type="NodeSocketColor")`, a `NodeGroupOutput` node, then `scene.compositing_node_group
  = tree` and `scene.render.use_compositing = True` (`scene.node_tree` is gone).
- `render.render("INVOKE_DEFAULT")` from a startup-script timer renders but may open no render
  window: switch the largest area to `IMAGE_EDITOR` showing `Render Result` to watch it.
- Headless runs load user prefs unless `--factory-startup` (which disables add-ons, CPU device —
  `archviz.render_setup` turns OptiX on when no compute device is set; a control that builds its
  own scene must call `archviz.use_gpu()` (`controls/_scene.black_scene` does), or it silently
  renders on the CPU at ~10x the time —
  and gives new worlds a grey 0.05 background (+π·0.05 W/m² on every surface) — set the
  Background Strength to 0 for a black test world).

- A multilayer EXR loaded as an image reports `size == (0, 0)` until its pixels load: read the
  size with OpenImageIO (a compositor render sized from it came out 4x4).
- Cycles only: `Render Result` cannot be saved while a render runs ("could not be saved") - no
  mid-render snapshots from Python. LuxCore allows them (luxcore.md › Final in the open UI).
- `bpy.ops.render.view_cancel()` (viewer stop) fires render_complete - yet the denoiser had not
  run; see render-settings.md > Finals with no sample limit.

## Windows shell
- Pass Blender output paths with forward slashes from bash.
- Edit skill/script files as UTF-8; several skill files use CRLF (use the Edit tool, or
  `newline=''` when scripting).

## Output and UI scripts (5.2)
- **Multilayer EXR is a media type now:** `image_settings.media_type = "MULTI_LAYER_IMAGE"`
  first, then `file_format = "OPEN_EXR_MULTILAYER"` (setting the format alone raises "enum not
  found"); set `media_type = "IMAGE"` back before saving PNGs. `Render Result.save_render()`
  then writes every pass (e.g. Combined + DENOISED) into one file. Read layers back with the
  bundled `OpenImageIO` (`seek_subimage` per layer); `scripts/blender/from_passes.py`.
- **Blender's render cancel skips the compositor** (Esc, status-bar ✕): `render_cancel` fires,
  `render_complete` does not, and the composited Render Result is the uncomposited image.
- **Operators in a `--python` startup script with UI** see no active object in their context
  (`mode_set.poll()` fails: "Context missing active object"), unlike `-b`. Wrap them:
  `bpy.context.temp_override(window=w, screen=w.screen, object=ob, active_object=ob,
  selected_objects=[ob], edit_object=ob)` (`lux_materials._ctx`). Test UI-run code in the UI
  once — a headless pass proves nothing about it.
- An object with **no material slots bakes nothing** ("No active image found"): give it a
  temporary slot for the bake material.

- `archviz.render_setup` sets `view_settings.exposure` (default 0) — call it before `archviz.physical_camera`, which writes the camera's exposure there; the other order renders white.
