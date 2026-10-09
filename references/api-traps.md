# Blender 5.2 API traps

## Nodes
- GN modifier inputs: `mod["Socket_N"]` fails; values live at `mod.properties.inputs.<id>.value`
  (empty `.name`; resolve via `node_group.interface.items_tree`) → `wear.set_input`. Group defaults
  are copied only at modifier creation. New code re-hits this with `mod[ident] = v`.
- Edge Angle (signed): convex arrises read **positive** on outward-normal Rhino meshes.
- ShaderNodeMix: hidden per-type sockets share names `A/B/Result` → `study_materials.sock`.
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

## Mesh / scene
- Subdivision adaptive: `use_adaptive_subdivision`, `adaptive_space='PIXEL'`, `adaptive_pixel_size`.
- After changing modifier inputs in background scripts: `obj.update_tag()` +
  `view_layer.update()` before reading evaluated meshes.
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
  dark water/haze). Set 2-4 whenever a volume scatters.
- Ray visibility (`visible_diffuse / visible_transmission …`) follows the type of the LAST bounce.
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
- Headless runs load user prefs unless `--factory-startup` (which disables add-ons, CPU device,
  and gives new worlds a grey 0.05 background (+π·0.05 W/m² on every surface) — set the
  Background Strength to 0 for a black test world).

## Windows shell
- Pass Blender output paths with forward slashes from bash.
- Edit skill/script files as UTF-8; several skill files use CRLF (use the Edit tool, or
  `newline=''` when scripting).
