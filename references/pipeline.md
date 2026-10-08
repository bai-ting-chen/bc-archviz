# Pipeline

## Install (2026-10-06)
- Blender: `winget install --id BlenderFoundation.Blender --version 5.2.2 --exact` — winget
  upgrades in place (removed 5.0.1); use the portable zip for side-by-side versions.
- MCP (Blender Lab, projects.blender.org/lab/blender_mcp, Blender ≥ 5.1): `mcp-<v>.zip` = add-on,
  `blender-<v>.mcpb` = server (unzip, `pip install .` into a venv). The site is behind Cloudflare;
  Gitea API `/api/v1/repos/lab/blender_mcp/...` works with curl.
- Add-on from file: `blender -c extension install-file -r user_default --enable <zip>`.
- Prefs: MCP `use_autostart`, port 9876; Cycles `compute_device_type = OPTIX`;
  `system.use_online_access = True` (required even for localhost).
- Claude Code: `.mcp.json` + `.claude/settings.local.json` `enabledMcpjsonServers`; tools load at
  session start. Server env: `BLENDER_MCP_HOST/PORT`, `BLENDER_PATH`.
- download.blender.org can answer winget with **403**. Fetch the same MSI from an official
  mirror (`mirrors.ocf.berkeley.edu/blender/release/…`, `mirror.clarkson.edu/blender/…`) and
  check its SHA256 against `winget show --id BlenderFoundation.Blender --version <v> --exact`
  before installing (`msiexec /i … /qn`, elevated — the user must accept the UAC prompt).
- The MCP server needs Python ≥ 3.10 (3.14 works). Add `numpy pillow` to its venv for
  `refmatch.py` / `imgstats.py`.
- Set prefs headless: `blender -b --python set_prefs.py` with `bpy.ops.wm.save_userpref()`
  (online access, MCP autostart/port, Cycles OPTIX + `refresh_devices()`).
- On a new machine the hard-coded project paths in `.mcp.json`, `CLAUDE.md` and a few tool
  scripts may name another user — fix them in that repo; the skill itself uses `~`.

## MCP tools
`execute_blender_code` (assign a dict to `result`), `get_objects_summary`,
`get_screenshot_of_window_as_image`, `render_viewport_to_path` (writes to
`<tempdir>/blender_mcp/` — copy out), `search_manual_docs`, `get_python_api_docs`. Timeout 300 s.
Fallback CLI client: `tools/mcp_call.py <tool> [json | --file script.py]`.

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

## Look-dev headless
`blender -b scene.blend --python tools/blender/render_variant.py -- out.png res=800x800
[disp=off|caustics=off|wear=off|chips=off|dirt=off|noise_seed=7|mask_view=1|material_view=NAME|camera=NAME]`
(forward-slash paths from bash).

## Final render in the open UI
`bpy.ops.render.render("INVOKE_DEFAULT")` inside `bpy.context.temp_override(window=…)` returns
immediately and the user watches it; register a `bpy.app.handlers.render_complete` function
that `save_render`s *Render Result* to the study folder (and removes itself), then wait for the
file from the shell. Save the .blend first.

## Iteration loop
`tools/study_run.py <study> vNN.png [--rebuild] [--pct 50 --spp 128]` does all of this for a
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
  as a file with `assert old in s` per replacement, so a stale anchor fails loudly.
- Render the wip frames at 50 % / 128 spp (about a minute). Look at the stacked render-over-
  reference every iteration, not only the patch table: the table missed a joint grid, missing
  globes and the black courtyard.
- When patch scripts pile up, fold them back into the scene scripts before the study is reused.

## Study layout
`studies/<yymmdd>_<topic>/`: Rhino build script, `*.3dm`, scene script (rebuilds from the .3dm via
MCP), `.blend`, finals, `STUDY_NOTES.md`, `_wip/` (controls, boards, test scripts). Delete
`*.blend1` / `*.3dmbak`.
