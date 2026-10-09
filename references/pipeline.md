# Pipeline

## Install (2026-10-06)
- Blender: `winget install --id BlenderFoundation.Blender --version 5.2.2 --exact` — winget
  upgrades in place (removed 5.0.1); use the portable zip for side-by-side versions.
- MCP (Blender Lab, projects.blender.org/lab/blender_mcp, Blender ≥ 5.1): `mcp-<v>.zip` = add-on,
  `blender-<v>.mcpb` = server. Installers are downloaded when needed, not kept. The site is behind Cloudflare;
  Gitea API `/api/v1/repos/lab/blender_mcp/...` works with curl.
- Add-on from file: `blender -c extension install-file -r user_default --enable <zip>`.
- Prefs: MCP `use_autostart`, port 9876; Cycles `compute_device_type = OPTIX`;
  `system.use_online_access = True` (required even for localhost).
- Server install (per machine, like Rook in `%LOCALAPPDATA%\Rook`): unzip the `.mcpb` into
  `%LOCALAPPDATA%\BlenderMCP\app`, `python -m venv %LOCALAPPDATA%\BlenderMCP\venv`, then
  `venv\Scripts\pip install app numpy pillow`. A venv can't be moved (absolute paths) — rebuild it.
- Claude Code, user scope (every project): `claude mcp add-json blender
  '{"type":"stdio","command":"<LOCALAPPDATA>/BlenderMCP/venv/Scripts/blender-mcp.exe","env":{...}}'
  --scope user`; check with `claude mcp get blender`. A project `.mcp.json` named `blender`
  overrides it — don't keep one. Tools load at session start. Server env: `BLENDER_MCP_HOST/PORT`, `BLENDER_PATH`.
- download.blender.org can answer winget with **403**. Fetch the same MSI from an official
  mirror (`mirrors.ocf.berkeley.edu/blender/release/…`, `mirror.clarkson.edu/blender/…`) and
  check its SHA256 against `winget show --id BlenderFoundation.Blender --version <v> --exact`
  before installing (`msiexec /i … /qn`, elevated — the user must accept the UAC prompt).
- The MCP server needs Python ≥ 3.10 (3.14 works). `numpy pillow` in its venv serve
  `refmatch.py` / `imgstats.py`.
- Set prefs headless: `blender -b --python set_prefs.py` with `bpy.ops.wm.save_userpref()`
  (online access, MCP autostart/port, Cycles OPTIX + `refresh_devices()`).
- Where things live (skill, project, MCP server): `SKILL.md` › *Skill and project*.

## MCP tools
`execute_blender_code` (assign a dict to `result`), `get_objects_summary`,
`get_screenshot_of_window_as_image`, `render_viewport_to_path` (writes to
`<tempdir>/blender_mcp/` — copy out), `search_manual_docs`, `get_python_api_docs`. Timeout 300 s.
Fallback CLI client: `scripts/mcp_call.py <tool> [json | --file script.py]`.

## Rhino → Blender
- `import_3dm` reads cached **render meshes**; in Rhino run
  `obj.CreateMeshes(MeshType.Render, MeshingParameters.QualityRenderMesh, False)` for breps,
  extrusions, SubD and block definitions. Via Rook, `sc.doc.WriteFile(path, FileWriteOptions())`.
- **User file open in Rhino** (check `sc.doc.Name` / `Modified` first): never open, new or save
  over it — single-document Rhino would close it. Build the study geometry in memory instead:
  `f = Rhino.FileIO.File3dm()`, set `f.Settings.ModelUnitSystem`, add layers to
  `f.AllLayers`, then add meshes with `f.Objects.AddMesh(mesh, attrs)`, where the mesh is
  `Mesh.CreateFromBrep(brep, MeshingParameters.QualityRenderMesh)` joined. Finish with
  `f.Write(path, 7)`. Meshes need no cached render mesh, and `objectsCreated` stays 0 in the
  user's document. Keep the builder as a parameter script in the study, run with
  `exec(open(path).read())` through Rook.
- **No Rhino open**: `rhino_launch` starts an owned workbench (empty document) — safe to build in.
- **RhinoCommon traps**: `Extrusion.Create(curve, h, cap)` follows the curve's plane normal, so a
  clockwise outline extrudes *down* (jambs and a canopy hung below their datum). Use
  `Surface.CreateExtrusion(curve, Vector3d(0, 0, h))` + `CapPlanarHoles`. `Curve.Offset(…, 0)`
  returns None. `RhinoViewport.SetFrustum` does not exist: build a `ViewportInfo`, `SetFrustum`
  on it, then `SetViewProjection`.
- **Clean curves**: `ArcCurve(Arc(p0, p1, p2))` through three readings; extend with
  `CurveExtensionStyle.Arc` so the extension keeps the radius (RULES 4a).
- **Rook scripts run on Rhino's UI thread and cannot be interrupted.** A per-element bisection
  solver calling `LengthParameter` ~40 M times froze Rhino for 20+ min; the only way out was
  killing Rhino (unsaved changes lost). Keep each call short and timed (`time.time()` log per
  step), prefer closed forms (on a constant radius, equal centre spacing gives equal joints),
  sample a curve once into a table if you must search, and split builds into steps
  (`STEPS = "block" | "wall"` globals). A background `rhino_execute` that times out is still
  running — check the Rhino process CPU before queuing more.
- **Displaced surfaces need explicit grids.** `Mesh.CreateFromBrep` ignores `MaxEdgeLength` on
  planar faces (46 mm triangles inside a "1.5 mm" mesh), so a relief displaced on it vanishes.
  Build regular quad grids instead; a rounded box = grid on the box pulled onto
  `core + r·unit(p − core)`.
- **Booleans on shared planes come out open.** Slab ∪ footprint band with the same top/bottom
  planes returned an open brep (and `MergeCoplanarFaces` then dropped its big faces); a 2D
  curve union failed where the curves touch tangentially. Edit the outline instead (swap one edge,
  matched by end points) and extrude. Check `IsSolid` on every generated brep; on failure re-show
  the original rather than leaving the scene with a hole.
- `ObjectTable.FindByLayer` skips hidden objects: re-runnable builders must enumerate with
  `ObjectEnumeratorSettings(HiddenObjects=True)` and `Delete(obj, True, True)`, or duplicates pile up.
- Copy the open model for Blender without touching it: `FileWriteOptions(UpdateDocumentPath=False)`
  + `sc.doc.WriteFile(path, opt)`.
- **Repeated elements as block definitions.** `import_3dm` turns them into collection instances;
  the definition's mesh lives in the definition's collection, not its layer's — assign materials
  by object name. For variety, a handful of definitions placed at random (+ random turns/flips)
  stays instanced; one unique mesh per element does not.
- `archviz.import_rhino` options: layers as collections, instances, named views → cameras, hidden
  objects/layers skipped, merge by distance; materials removed; mm → m. Delete any leftover `V-Ray Infinite Plane` object (older .3dm files carry one).
- Always start from `read_homefile(use_empty=True)` (importing into an edited factory scene failed once).
- Imported meshes are welded, manifold, outward normals; coarse — dice where detail is needed.

## Assets
- Poly Haven (CC0; credit "Powered by Poly Haven" if the live API is used in published work):
  `polyhaven_fetch.py search textures <cat>`, `tex <id> --res 2k`, `hdri <id> --res 4k`; maps diff,
  arm, nor_gl, disp; `meta.json` has `dimensions_mm`. `search` matches categories only. For
  names and tags, query `api.polyhaven.com/assets?t=textures|hdris` and choose from a thumbnail
  contact sheet (materials.md). HTTP 520–525 is Cloudflare: retry the same call.
- Others in `library/local/<name>/` with a `meta.json` stating the source. Megascans via Fab:
  free items only; download needs the user's own sign-in (their Chrome) — never type passwords.
- **Where:** the study's own `library/` (RULES 10c) — `ARCHVIZ_PROJECT=<study> polyhaven_fetch.py …`,
  `archviz.set_project(<study>)` in Blender. Edited HDRIs, baked/generated maps and their
  generator script references go in `<study>/library/local/` with a `meta.json`. Never repoint a
  study at another study's or a shared copy.
- Judge a texture on its colour map at full size, not by its tags: "white / clean" plaster and
  concrete scans turned out to be painted formwork boards with peeling paint, or weathered and
  stained (materials.md › Choosing).

## Look-dev headless
`blender -b scene.blend --python scripts/blender/render_variant.py -- out.png res=800x800
[disp=off|caustics=off|wear=off|chips=off|dirt=off|noise_seed=7|mask_view=1|material_view=NAME|camera=NAME]`
(forward-slash paths from bash).

## Final render in the open UI (RULES 10b: only after the user approved the preview)
`bpy.ops.render.render("INVOKE_DEFAULT")` inside `bpy.context.temp_override(window=…)` returns
immediately and the user watches it; register a `bpy.app.handlers.render_complete` function
that `save_render`s *Render Result* to the study folder (and removes itself), then wait for the
file from the shell. Save the .blend first.
- When Blender is not open yet: launch it **with UI** on the build script (`blender --python
  build.py -- …`, no `-b`); the script builds the scene, saves the .blend, then starts the render
  from `bpy.app.timers.register(start, first_interval=3)`. If no render window appears, put an
  Image Editor on `Render Result` (api-traps).
- Before proposing the final, state resolution, time and expected noise from a measured preview
  (noise ∝ 1/√(samples/px)); leave a buffer for denoise and saving.
- Tests and previews run headless (`blender -b`), one at a time; tell the user when a CPU-only
  engine leaves the GPU idle — it looks like wasted capacity otherwise.

## Iteration loop
`scripts/study_run.py <study> vNN.png [--rebuild] [--pct 50 --spp 128]` does all of this for a
study holding `scene_geometry.py` + `scene_look.py` (+ `_wip/ref.jpg`, `regions.json`).
Keep two rebuild scripts in the study (`scene_geometry.py`: import + camera; `scene_look.py`:
materials, lights, exposure) and a small runner that rebuilds, renders `_wip/vNN.png`, prints
`refmatch.py patches` and writes `pair_vNN.png`. Every change is then one edit + one run, and
each version's reason lives as a comment next to the value it changed.
- The runner must `ast.parse` both scripts before sending them to Blender. Scripted
  replacements (sed or str.replace) appending `# reason` to a line that continues the call
  commented out the arguments three times in one study, and each cost a render round-trip.
  Put the comment on its own line above the value, or use the Edit tool.
- Long Python patches don't belong in a bash heredoc (quotes broke the shell). Write the patch
  as a file with `assert old in s` per replacement, so a stale anchor fails loudly. This was
  hit again with a patch holding nested quotes; sed replacements of whole lines also silently
  dropped a second statement on the same line. Use the Edit tool for multi-statement lines.
- Render the wip frames at 50 % / 128 spp (about a minute). Look at the stacked render-over-
  reference every iteration, not only the patch table: the table missed a joint grid, missing
  globes and the black courtyard.
- When patch scripts pile up, fold them back into the scene scripts before the study is reused.

## Study layout
`studies/<yymmdd>_<topic>/`: Rhino build script, `*.3dm`, scene script (rebuilds from the .3dm via
MCP), `.blend`, finals, `STUDY_NOTES.md`, `library/` (`polyhaven/`, `local/` — every asset the
study uses, RULES 10c), `_wip/` (controls, boards, test scripts). Delete `*.blend1` / `*.3dmbak`.
