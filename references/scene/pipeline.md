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
  `mklink /J "%USERPROFILE%\.agents\skills\bc-archviz" "%USERPROFILE%\.claude\skills\bc-archviz"`.
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
- Skill code lives in `~/.claude/skills/bc-archviz`, project data in the current study, and MCP in `%LOCALAPPDATA%/BlenderMCP`.

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
  operation may still be running after a timeout. Inspect CPU and target state, wait for active work; never blindly retry writes or terminate Rhino without the user’s decision. Keep each call short and timed
  (`time.time()` log per step), prefer closed-form layouts, sample a curve once into a table if
  you must search, and split builds into steps run as separate calls. A background
  `rhino_execute` that times out is still running — check the Rhino process CPU before queuing
  more. The client gives up after ~2 min while Rhino carries on ("dispatcher busy"): run
  **open, build and explicitly authorized save as three calls**.
- **Open models with `Rhino.RhinoDoc.OpenFile(path)` inside `rhino_execute`** (the document
  tool's open fails in a fresh workbench). Opening while the current document counts as
  modified raises a modal "save changes?" that blocks every call until a person clicks it; after
  an authorized save, re-read the document state; never clear `doc.Modified` to bypass the prompt. A force-killed Rhino leaves `<file>.3dm.rhl` lock
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
- In an owned disposable study process, start from `read_homefile(use_empty=True)`; never reset a user’s live scene without authorization.
- Imported meshes are welded, manifold, outward normals; coarse — dice where detail is needed.

## Assets
- Poly Haven (CC0; credit "Powered by Poly Haven" if the live API is used in published work):
  `polyhaven_fetch.py search textures <cat>`, `tex <id> --res 2k`, `hdri <id> --res 4k`; maps diff,
  arm, nor_gl, disp; `meta.json` has `dimensions_mm`. `search` matches categories only. For
  names and tags, query `api.polyhaven.com/assets?t=textures|hdris` and choose from a thumbnail
  contact sheet ([index.md](../materials/index.md)). HTTP 520–525 is Cloudflare: retry the same call.
- Others in `library/local/<name>/` with a `meta.json` stating the source. Megascans via Fab:
  free items only; download needs the user's own sign-in (their Chrome) — never type passwords.
- **Where:** the study's own `library/` (RULES AST_03) — `ARCHVIZ_PROJECT=<study> polyhaven_fetch.py …`,
  `archviz.set_project(<study>)` in Blender. Run from inside a study, both find it without the
  setting (`projectpath`: the search stops at the study folder); a shared `library/` above is
  read only by studies listed in its `legacy_studies.txt`, and `polyhaven_fetch` prints a NOTE
  when it downloads anywhere but a study. Edited HDRIs, baked/generated maps and their
  generator script references go in `<study>/library/local/` with a `meta.json`. Never repoint a
  study at another study's or a shared copy. Choosing a texture: [materials/texture-selection.md](../materials/texture-selection.md)

## Look-dev headless
`blender -b scene.blend --python scripts/blender/render_variant.py -- out.png res=800x800
[disp=off|caustics=off|wear=off|stain=off|chips=off|dirt=off|noise_seed=7|mask_view=1|material_view=NAME|camera=NAME]`
(forward-slash paths from bash; the script's docstring lists every option, and an unknown option
stops it rather than rendering an unchanged "control"). It renders on the GPU (`archviz.use_gpu`).

## Final render in the open UI (RULES GAT_04)
`bpy.ops.render.render("INVOKE_DEFAULT")` inside `bpy.context.temp_override(window=…)` returns
immediately and the user watches it; register a `bpy.app.handlers.render_complete` function
that `save_render`s *Render Result* to the study folder (and removes itself), then wait for the
file from the shell. Save the .blend first when explicitly authorized; otherwise obtain save authorization before destructive scene operations.
- When Blender is not open yet: launch it **with UI** on the build script (`blender --python
  build.py -- …`, no `-b`); the script builds the owned scene, saves the .blend only with explicit authorization, then starts the render
  from `bpy.app.timers.register(start, first_interval=3)`. If no render window appears, put an
  Image Editor on `Render Result` (api-traps).
- Unlimited final: Cycles `samples` high with `time_limit = 0` and adaptive off, LuxCore
  `halt.enable = False`. Register the save handler on
  `render_complete` **and** `render_cancel` — Esc fires only the latter, and skips the
  compositor: save all passes as multilayer EXR and build the finals from the denoised layer
  (`scripts/blender/from_passes.py`; [luxcore.md](../renderer/luxcore.md) › Final in the open UI).
- The pre-final full-frame check (RULES GAT_04 (4)) runs the same build script headless at reduced
  resolution; it caught a broken save helper and a UI-only context error before a multi-hour run.
  Only one Blender may hold the MCP port: quit an idle finished-final window first.
- Before proposing the final, estimate how long the expected quality takes from a measured
  preview (noise ∝ 1/√(samples/px)), so the user knows when stopping is reasonable.
- Tests and previews headless (RULES GAT_04), one at a time; tell the user when a CPU-only
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
study uses, RULES AST_03), `_wip/` (controls, boards, test scripts, crops, measurements,
downloads — everything the study produces, RULES AST_01). Delete `*.blend1` / `*.3dmbak`.
Closing a study: `## Milestones` list in STUDY_NOTES, then `study_close.py` (RULES AST_02).


## PIP_01 procedure

**Rhino = geometry only.** Materials, lights, camera look and render settings live in Blender
   (one place to edit the look; Rhino materials don't translate). Layer/block/object names are the
   hooks; discard .3dm materials. Rhino files are read-only; re-meshing imported meshes is fine.


## GAT_02 procedure

**Rhino → Blender gate**. After the Rhino model is finished, stop and
    show the user (viewport captures + a list of what was modelled and left out); pipe to
    Blender only after the user approves the geometry. Rework in Rhino is cheap, a look-dev
    round on wrong geometry is not.


## GAT_04 procedure

**Final render gate**. (1) Render a preview, show it, state the final's
    resolution, time budget and expected noise, and **wait for approval** — the user reviews the
    preview first; a material or light change after approval means a new preview. (2) Run the
    final **in the open Blender UI** so the user watches it live; headless renders are for tests,
    controls and previews. (3) Set **no time or sample limit** on the final: it renders until the
    user stops it, and saving/denoising run on stop. A halt time is fixed when the session starts
    and a finished render cannot be resumed, so a limit can only cut the user's choice short.
    (4) Before any long or unattended final, render a short **full-frame** test with exactly the
    final's settings (raw and denoised) and look at every surface, not only the one under
    discussion. Bring known risks and their tested fixes to the user *before* launch; a fix is
    not withheld because it is not yet approved. Look at the saved result before calling it done
    or sending it anywhere.


## AST_03 procedure

**Each study owns its assets**. HDRIs, textures, edited HDRIs, generated
    maps and their `meta.json` live in the study's own `library/`, downloaded again even when
    another study has the same file, so a study moves, archives or hands over self-contained.


## AST_01/AST_04 procedure

**Everything a study makes stays in its folder**: crops, comparisons, test renders,
    measurements, downloads and throwaway scripts go in the study's `_wip/`, never the session
    scratchpad or %TEMP% — tell subagents the path too. One place holds all a study produced.
    Software is not study output: Blender extensions and add-ons install into Blender's own
    extension folder through the installer, and the downloaded zip is deleted afterwards.


## SAF_01 procedure

MCP code runs unguarded in the user’s Blender. Save user files first when explicitly authorized; otherwise stop before destructive scene operations. Never delete user datablocks without asking. Rebuild only owned study files from their scripts.


## Runtime task checks

Apply only checks needed by the current task. Read-only documentation work needs no Blender/Rhino connection.

## Runtime preflight (task-conditional)
```
- [ ] Read [RULES.md](../../RULES.md) and the references/ file for the task — both live in THIS skill folder,
      not the project; skim [api-traps.md](api-traps.md) before writing node/GN code
- [ ] `%LOCALAPPDATA%\BlenderMCP\AGENT_LOCK` absent or mine (RULES AGT_04); create it before working in Blender, Rhino, scripts or files
- [ ] Blender open, MCP on 9876 (get_blendfile_summary_datablocks)
- [ ] Rhino: which document is open, is it modified? A user's file stays untouched — write
      the study geometry with File3dm (pipeline.md)
- [ ] Local studies? read `studies/README.md` + the latest STUDY_NOTES.md (open items carry over)
- [ ] New technique? gather sources (physics first), stop at the research gate for the user's
      links, then analyse and compare workflows (RULES RES_01, GAT_01)
- [ ] First build done? material gate: schedule + first pass + crops, wait (RULES GAT_03)
- [ ] Before every "done": native-resolution crop pass of each material vs the ref (RULES VAL_01)
- [ ] Look decision? profile the Render Reference Library slice
- [ ] Study folder set? `archviz.set_project(<study>)`; every asset downloaded/generated into
      the study's own `library/` (`ARCHVIZ_PROJECT=<study> polyhaven_fetch.py …`)
- [ ] Caustics through glass/water central to the shot? → LuxCore ([RULES REN_03](../renderer/renderer-choice.md), [LuxCore setup](../renderer/luxcore.md));
      otherwise Cycles
- [ ] Final render: preview approved by the user first, then render in the open UI (RULES GAT_04)
```


## Tools and execution

## Stack
| Piece | Where |
|---|---|
| Blender | `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe` |
| MCP | server `%LOCALAPPDATA%\BlenderMCP\venv\Scripts\blender-mcp.exe` (user scope, `claude mcp get blender`); add-on `mcp` autostarts on 127.0.0.1:9876 (needs Prefs → *Allow Online Access*) |
| Helpers (run in Blender) | `scripts/blender/`: `archviz` (assets, import, UVs, camera and rendering), `interior` (photometric lighting), `scatter`, `terrain`, `atmosphere`, `glassware`, caustic solvers, `render_variant`, `finals`, `from_passes`. Materials use the canonical `materials` package; see [family map](../materials/index.md). |
| Outdoor | `terrain`, `scatter`, `atmosphere`; `materials.ground` and `materials.vegetation` for shading. |
| Finals (Cycles) | `scripts\blender\finals.py`: untiled no-limit final in the UI, savers, OIDN from passes, graded PNG |
| 3ds Max assets | `scripts\blender\max_import.py`: `load` (io_scene_max extension + repairs), `tidy`, `rebuild_materials`, `open_loops` — [max-import.md](max-import.md) |
| Photometry | `scripts\ldt2ies.py in.ldt out.ies` (Eulumdat → IES for Cycles, lumens checked); IES files → `interior.ies_light` |
| Measure | `scripts\imgstats.py stats|patch|diff`; `scripts\refmatch.py grid|pair|patches` (render vs reference) — MCP venv python (`%LOCALAPPDATA%\BlenderMCP\venv\Scripts\python`) |
| Geometry check | `scripts\rhino\project_edges.py` (in Rhino via Rook, with the solved camera) → `scripts\edge_overlay.py edges.json ref.png out.png` |
| Reference recreation | `scripts\refsolve.py readings.json` (camera from a repeated element + image→plan); `scripts\study_run.py <study> vNN.png [--rebuild]` (syntax-check, render via MCP, pair + stack + patches) |
| Maintenance | `scripts\helper_index.py` (writes [helpers.md](helpers.md)), `scripts\regress_helpers.py` (old vs new helper output), `scripts\codex_review.py` (Codex reviews a change before push, RULES AGT_01), `scripts\study_close.py` (close a study: keep milestones, delete the rest, RULES AST_02) |
| Tiles | `scripts/blender/materials/`: `tile_mapping`, `tile_layout`, `tile_surface`, `tile_damage` — [Tiles](../materials/tiles.md). |
| Controls | `scripts\controls\light_units.py`, `ies_units.py`, `mnee_water.py` — rerun after a Blender upgrade (`blender -b --factory-startup --python …`); `tile_layout_check`, `tile_mapping_check`, `tile_surface_check`, `tile_damage_check` (`--only <section>`, `--full`) |
| Caustics renderer | LuxCore via the BlendLuxCore extension ([luxcore.md](../renderer/luxcore.md)): PATH, GPU + *Use CPUs*, *Add Light Tracing* |
| Assets | `scripts\polyhaven_fetch.py` → `<study>\library\polyhaven\` (env `ARCHVIZ_PROJECT=<study>`); others `<study>\library\local\` with a `meta.json` |
| Video research | `scripts\yt_learn.py` |

In Blender code: `sys.path.insert(0, os.path.expanduser(r"~\.claude\skills\bc-archviz\scripts\blender"))`.
Without the MCP tools loaded (session started elsewhere), drive Blender with
`scripts/mcp_call.py execute_blender_code --file script.py`; the script must assign a **dict** to `result`.
Anything in a Blender panel is RNA → scriptable via MCP `execute_blender_code`. Not scriptable:
hand tools (sculpt, knife, gizmos). The MCP bundles the 5.x manual + API offline
(`search_manual_docs`, `get_python_api_docs`) — the authority for generic Blender facts.


## Build sequence

## Workflow
1. **Rhino** (Rook): geometry on named layers; force render meshes; write only the owned study `.3dm` with explicit save authorization — or, when the
   user has their own file open, build meshes into a `File3dm` and write it (pipeline.md).
   Then the model gate (RULES GAT_02).
2. **Import**: `bpy.ops.wm.read_homefile(use_empty=True)` in an owned disposable study process, `archviz.import_rhino(path)` → layer
   collections, blocks → instances, named views → cameras, materials dropped, mm → m.
3. **UVs** at the texture's real size: non-directional textures (plain concrete, plaster,
   terrazzo, mortar, gravel) `archviz.box_uv(obj, size_m)`; directional ones (wood grain, boards,
   brushed metal, vein-cut stone, ribbed sheet, weave, long tiles) `archviz.directional_uv(obj,
   size_m, axis)` so the direction follows the element on every face ([texture-selection.md](../materials/texture-selection.md)).
4. **Materials** by layer → [materials/index.md](../materials/index.md); after the first full build (step 6), the
   material gate (RULES GAT_03) before any look round.
5. **Light**: daylight (RULES LGT_02) `archviz.world_hdri_lux`, rotated by its `hdri_analyse` sun
   direction; artificial: the fixture's IES file `interior.ies_light` when it is specified, else `interior.downlight /
   led_strip / lens_luminance` → [lighting-camera.md](lighting-camera.md).
6. **Camera**: `archviz.render_setup(...)` first (it resets view exposure; step 7), then
   `archviz.physical_camera(cam, iso, f, shutter, focal)`, `straighten_verticals`,
   white balance if lights are warm. From a reference image: `refmatch.py grid` → solve the
   camera (`refsolve.py` when the image has a repeated element) → `archviz.framing_render(root, path)` +
   `refmatch.py pair --overlay`; then light region by region with `study_run.py`
   (lighting-camera.md › *Recreating a reference*).
7. **Render**: settings → [render-settings.md](../renderer/render-settings.md); LuxCore case
   ([RULES REN_03](../renderer/renderer-choice.md)) → [LuxCore setup](../renderer/luxcore.md).
8. **Look-dev**: headless `render_variant.py` or MCP renders into the study `_wip/`; measure
   with `imgstats`; prove each feature with a control (RULES VAL_02). Reuse the helpers
   ([helpers.md](helpers.md) lists them all: `materials.edge_wear.set_input`, `materials.nodes.sock`, `materials.pbr.pbr_material`,
   `materials.nodes.G`, `materials.pbr`, `scatter`) instead of re-deriving
   node plumbing — the traps they wrap get hit again otherwise.
9. **Final** (RULES GAT_04) → [pipeline.md](pipeline.md) › *Final render in the open UI* (Cycles: `finals.py`); linear EXR + graded
   PNGs into the study folder.
10. `studies/<yymmdd>_<topic>/STUDY_NOTES.md`: what, proof numbers, traps, open items.


## Tested stack baseline

The pre-restructure skill was verified on Blender 5.2.2 LTS, Blender Lab MCP 1.0.3,
import_3dm 0.0.18, BlendLuxCore 2.11.1, RTX 3060 Ti 8 GB (OptiX), Windows 10/11.
These are the recorded baseline versions, not a requirement to reinstall or upgrade on receiving machines.
