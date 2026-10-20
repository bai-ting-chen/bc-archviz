# Pipeline

## Install
- Blender: `winget install --id BlenderFoundation.Blender --version 5.2.2 --exact` — winget
  upgrades in place; use the portable zip for side-by-side versions.
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
- Codex (OpenAI) on the same machine: its user skills folder is `~/.agents/skills`. Link the
  skill there as a directory junction, not a copy, so a `git pull` updates both agents:
  `mklink /J "%USERPROFILE%\.agents\skills\blender-archviz" "%USERPROFILE%\.claude\skills\blender-archviz"`.
  A Codex skill import can leave a stale copy there; replace it. Register the MCP in
  `~/.codex/config.toml` as `[mcp_servers.blender]` with the same command and an
  `[mcp_servers.blender.env]` table; check with `codex mcp list`. Codex reads `AGENTS.md`, not
  `CLAUDE.md` or Claude Code's memory, so a project used from Codex gets an `AGENTS.md` that points
  at those sources and translates Claude-only terms (tool names, "save a memory"). Git operations
  on the skill go through the `~/.claude` path.
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
- **Materials from another renderer on the user's layers** (Enscape, V-Ray; data only, no
  V-Ray tooling): read them read-only
  with `File3dm`. Enscape keeps its data in the RDK RenderMaterials XML (`parameters-v8`, mirrored
  `parameters`) plus plug-in UserData: texture paths, size, rotation, tint, roughness, normal
  strength. Paths often point at another user's machine (`C:\Users\<other>\Enscape\ImportedTextures\`):
  look for legacy or `_embedded_files` copies on the project drives, copy the found maps into the
  study's `library/local/<material>/` with a `meta.json`, and report what is missing. Rhino's
  `rdk$….tiff` cache is a ~512 px preview, not a usable map. Reuse maps and real size; translate
  gloss/roughness against the reference, never 1:1.
- **No Rhino open**: `rhino_launch` starts an owned workbench (empty document) — safe to build in.
- **RhinoCommon traps**: `Extrusion.Create(curve, h, cap)` follows the curve's plane normal, so a
  clockwise outline extrudes *down* (jambs and a canopy hung below their datum). Use
  `Surface.CreateExtrusion(curve, Vector3d(0, 0, h))` + `CapPlanarHoles`. `Curve.Offset(…, 0)`
  returns None. `RhinoViewport.SetFrustum` does not exist: build a `ViewportInfo`, `SetFrustum`
  on it, then `SetViewProjection`.
- Arc through three points: `ArcCurve(Arc(p0, p1, p2))`; extending an arc with
  `CurveExtensionStyle.Arc` keeps its radius.
- **Rook scripts run on Rhino's UI thread and cannot be interrupted.** A long Python loop (a
  numeric solver calling curve queries millions of times) freezes Rhino until it finishes; the
  only way out is killing Rhino, losing unsaved changes. Keep each call short and timed
  (`time.time()` log per step), prefer closed-form layouts, sample a curve once into a table if
  you must search, and split builds into steps run as separate calls. A background
  `rhino_execute` that times out is still running — check the Rhino process CPU before queuing
  more. The client gives up after ~2 min while Rhino carries on ("dispatcher busy"): run
  **open, build and save as three calls**.
- **Open models with `Rhino.RhinoDoc.OpenFile(path)` inside `rhino_execute`** (the document
  tool's open fails in a fresh workbench). Opening while the current document counts as
  modified raises a modal "save changes?" that blocks every call until a person clicks it; after
  writing a copy, set `doc.Modified = False`. A force-killed Rhino leaves `<file>.3dm.rhl` lock
  files (delete once no Rhino owns them) and a crash-report dialog on the next start that only
  the user can dismiss. A relaunched workbench needs `rhino_set_active_instance(port=…)`.
- **Displaced surfaces need explicit grids.** `Mesh.CreateFromBrep` ignores `MaxEdgeLength` on
  planar faces (large triangles inside a fine mesh), so a relief displaced on it vanishes.
  Build regular quad grids instead; a rounded box = grid on the box pulled onto
  `core + r·unit(p − core)`.
- **Booleans on shared planes come out open.** A union of solids sharing their top and bottom
  planes returns an open brep (and `MergeCoplanarFaces` can then drop its big faces); a 2D curve
  union fails where the curves touch tangentially. Edit the outline instead (swap one edge,
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
- **Matching a Rhino named view exactly:** read its frustum (`ViewInfo.Viewport.GetFrustum()` →
  FOV = 2·atan(right/near)) and aspect. Rhino's `Camera35mmLensLength` on a square view equals
  the FOV of a 24 mm frame side, so Blender takes the same lens with `sensor_width = 24` and a
  square render; check dir/up/location/FOV against Rhino after import.
- `archviz.import_rhino` options: layers as collections, instances, named views → cameras, hidden
  objects/layers skipped, merge by distance; materials removed; mm → m. Delete any leftover `V-Ray Infinite Plane` object (older .3dm files carry one).
- Always start from `read_homefile(use_empty=True)`; importing into an edited factory scene is unreliable.
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
  `archviz.set_project(<study>)` in Blender. Run from inside a study, both find it without the
  setting (`projectpath`: the search stops at the study folder); a shared `library/` above is
  read only by studies listed in its `legacy_studies.txt`, and `polyhaven_fetch` prints a NOTE
  when it downloads anywhere but a study. Edited HDRIs, baked/generated maps and their
  generator script references go in `<study>/library/local/` with a `meta.json`. Never repoint a
  study at another study's or a shared copy. Choosing a texture: materials.md › Choosing.

## Look-dev headless
`blender -b scene.blend --python scripts/blender/render_variant.py -- out.png res=800x800
[disp=off|caustics=off|wear=off|stain=off|chips=off|dirt=off|noise_seed=7|mask_view=1|material_view=NAME|camera=NAME]`
(forward-slash paths from bash; the script's docstring lists every option, and an unknown option
stops it rather than rendering an unchanged "control"). It renders on the GPU (`archviz.use_gpu`).

## Final render in the open UI (RULES 10b)
`bpy.ops.render.render("INVOKE_DEFAULT")` inside `bpy.context.temp_override(window=…)` returns
immediately and the user watches it; register a `bpy.app.handlers.render_complete` function
that `save_render`s *Render Result* to the study folder (and removes itself), then wait for the
file from the shell. Save the .blend first.
- When Blender is not open yet: launch it **with UI** on the build script (`blender --python
  build.py -- …`, no `-b`); the script builds the scene, saves the .blend, then starts the render
  from `bpy.app.timers.register(start, first_interval=3)`. If no render window appears, put an
  Image Editor on `Render Result` (api-traps).
- Unlimited final: Cycles `samples` high with `time_limit = 0` and adaptive off, LuxCore
  `halt.enable = False`. Register the save handler on
  `render_complete` **and** `render_cancel` — Esc fires only the latter, and skips the
  compositor: save all passes as multilayer EXR and build the finals from the denoised layer
  (`scripts/blender/from_passes.py`; luxcore.md › Final in the open UI).
- The pre-final full-frame check (RULES 10b (4)) runs the same build script headless at reduced
  resolution; it caught a broken save helper and a UI-only context error before a multi-hour run.
  Only one Blender may hold the MCP port: quit an idle finished-final window first.
- Before proposing the final, estimate how long the expected quality takes from a measured
  preview (noise ∝ 1/√(samples/px)), so the user knows when stopping is reasonable.
- Tests and previews headless (RULES 10b), one at a time; tell the user when a CPU-only
  engine leaves the GPU idle — it looks like wasted capacity otherwise.

- Cycles: `scripts/blender/finals.py` does all of this - `start_in_ui(out_dir, res)` (untiled,
  no limit, savers on complete + cancel, view fitted), `stop_in_ui()`, then `-- denoise` and
  `-- png` from the saved passes (render-settings.md > Finals with no sample limit).

## Iteration loop
`scripts/study_run.py <study> vNN.png [--rebuild] [--pct 50 --spp 128]` does all of this for a
study holding `scene_geometry.py` + `scene_look.py` (+ `_wip/ref.jpg`, `regions.json`).
Keep two rebuild scripts in the study (`scene_geometry.py`: import + camera; `scene_look.py`:
materials, lights, exposure) and a small runner that rebuilds, renders `_wip/vNN.png`, prints
`refmatch.py patches` and writes `pair_vNN.png`. Every change is then one edit + one run, and
each version's reason lives as a comment next to the value it changed.
- The runner must `ast.parse` both scripts before sending them to Blender. A scripted
  replacement (sed or str.replace) appending `# reason` to a line that continues a call comments
  out the rest of the call — put the comment on its own line above the value, or use the Edit tool.
- Long Python patches don't belong in a bash heredoc (nested quotes break the shell). Write the
  patch as a file with `assert old in s` per replacement, so a stale anchor fails loudly. A sed
  replacement of a whole line silently drops any second statement on it — use the Edit tool for
  multi-statement lines.
- Render the wip frames at 50 % / 128 spp. Look at the stacked render-over-reference every
  iteration, not only the patch table: region numbers miss joint grids, missing objects and
  wrongly roofed areas.
- When patch scripts pile up, fold them back into the scene scripts before the study is reused.

## Study layout
`studies/<yymmdd>_<topic>/`: Rhino build script, `*.3dm`, `scene_geometry.py` + `scene_look.py`
(rebuild from the .3dm via MCP; the names `study_run.py` expects), `.blend`, finals, `STUDY_NOTES.md`, `library/` (`polyhaven/`, `local/` — every asset the
study uses, RULES 10c), `_wip/` (controls, boards, test scripts, crops, measurements,
downloads — everything the study produces, RULES 10d). Delete `*.blend1` / `*.3dmbak`.
Closing a study: `## Milestones` list in STUDY_NOTES, then `study_close.py` (RULES 10e).
