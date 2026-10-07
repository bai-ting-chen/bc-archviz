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
- `archviz.import_rhino` options: layers as collections, instances, named views → cameras, hidden
  objects/layers skipped, merge by distance; materials removed; mm → m. Delete `V-Ray Infinite Plane`.
- Always start from `read_homefile(use_empty=True)` (importing into an edited factory scene failed once).
- Imported meshes are welded, manifold, outward normals; coarse — dice where detail is needed.

## Assets
- Poly Haven (CC0; credit "Powered by Poly Haven" if the live API is used in published work):
  `polyhaven_fetch.py search textures <cat>`, `tex <id> --res 2k`, `hdri <id> --res 4k`; maps diff,
  arm, nor_gl, disp; `meta.json` has `dimensions_mm`.
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
Keep two rebuild scripts in the study (`scene_geometry.py`: import + camera; `scene_look.py`:
materials, lights, exposure) and a small runner that rebuilds, renders `_wip/vNN.png`, prints
`refmatch.py patches` and writes `pair_vNN.png`. Every change is then one edit + one run, and
each version's reason lives as a comment next to the value it changed.

## Study layout
`studies/<yymmdd>_<topic>/`: Rhino build script, `*.3dm`, scene script (rebuilds from the .3dm via
MCP), `.blend`, finals, `STUDY_NOTES.md`, `_wip/` (controls, boards, test scripts). Delete
`*.blend1` / `*.3dmbak`.
