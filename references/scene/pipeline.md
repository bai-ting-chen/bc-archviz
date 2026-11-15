# Pipeline

Use when: running a study from Rhino geometry to a Blender final.

One phase per tool. Each phase names what it hands to the next and the check that must pass first.
A failed check stops the phase (RULES PIP_02; see *When a phase fails*). Machine setup, MCP tools and
where each tool lives: [machine-setup.md](../workflow/machine-setup.md).

## Phase 0. Preflight (apply only the checks the task needs)
Read-only documentation work needs no Blender or Rhino connection.
```
- [ ] RULES.md and the reference for the task (both in THIS skill folder, not the project);
      blender-api-traps.md before writing node/GN code
- [ ] Blender open, MCP answering on 9876 (get_blendfile_summary_datablocks)
- [ ] Rhino: which document is open and is it modified? A user's file stays untouched (Rhino below)
- [ ] Local studies: studies/README.md + the latest study-notes.md (open items carry over)
- [ ] Study folder set: archviz.set_project(<study>); assets into the study's library/ (RULES AST_01)
- [ ] New technique: research gate first (RULES RES_01, GAT_01)
- [ ] Caustics through glass or water central to the shot → LuxCore (RULES REN_02), else Cycles
```

## Phase 1. Geometry in Rhino (Rook)
1. Model on named layers: layer, block and object names are Blender's hooks (RULES PIP_01).
2. Give every object a render mesh and write only the owned study `.3dm` (*Rhino* below).
3. **Hands over:** the study `.3dm` path; named layers, blocks and named views.
4. **Check:** `IsSolid` on every generated solid; every object has a render mesh (one without
   imports with 0 faces); the user's document unchanged.
5. **Gate:** viewport captures + modelled/omitted list (RULES GAT_02); Blender only after approval.

## Phase 2. Import into Blender (Blender MCP)
1. In an owned study process: `bpy.ops.wm.read_homefile(use_empty=True)`, then
   `archviz.import_rhino(path)`: layers → collections, blocks → instances, named views → cameras,
   materials dropped, hidden objects skipped, mm → m. Delete a leftover `V-Ray Infinite Plane`.
2. **Hands over:** collections and object names for materials; cameras from the named views.
3. **Check:** every mesh, including those inside blocks, has faces; a named-view camera matches
   Rhino's direction, up, location and FOV (Rhino's lens = `sensor_width = 24` on a square render).

## Phase 3. Look build (Blender)
1. **UVs** at the texture's real size: `archviz.box_uv(obj, size_m)` for non-directional textures,
   `archviz.directional_uv(obj, size_m, axis)` for grain, boards, brushed metal, long tiles
   ([texture-selection.md](../materials/texture-selection.md)).
2. **Materials** by layer → [materials/index.md](../materials/index.md); `archviz.apply_material_map`.
3. **Light:** HDRI world `archviz.world_hdri_lux`, rotated by `hdri_analyse` (RULES LGT_02);
   fixtures `ies_light` when an IES file is specified, else `downlight` / `led_strip` /
   `panel_light` → [lighting/index.md](lighting/index.md).
4. **Render settings, then camera:** `archviz.render_setup(...)` (it resets view exposure), then
   `archviz.physical_camera`, `straighten_verticals`, white balance → [camera.md](camera/camera.md),
   [render-settings.md](../renderer/render-settings.md).
5. **From a reference image:** [reference-match.md](reference-match.md).
6. **Hands over:** a full first build rendered from the final camera.
7. **Gate:** the material gate (RULES GAT_03) before any look round.

## Phase 4. Look rounds (Blender, host tools)
1. Run the rounds as [validation.md](../review/validation.md) › *The look round*: the match list, one
   change per round, keep or revert, the stop rule.
2. Prove each feature with a control (RULES VAL_01).
3. Reuse the helpers in [blender-python-helpers.md](blender-python-helpers.md) instead of
   re-deriving node plumbing: the traps they wrap get hit again otherwise.
4. **Hands over:** the look the user approved.

## Phase 5. Final (Blender UI)
1. **Gate:** preview, resolution, time budget and expected noise; wait for approval (RULES GAT_04).
2. **Check before launch:** a short full-frame test with exactly the final's settings.
3. Launch in the open UI with no limit: [render-settings.md](../renderer/render-settings.md) ›
   *Final in the open UI*. Linear EXR + graded PNGs go into the study folder.
4. **Check:** look at the saved result, every surface, before calling it done.

## Phase 6. Record
`study-notes.md` in the study: what, proof numbers, traps, open items.

## When a phase fails
- **Stop the phase** (RULES PIP_02): report what failed and what was tried.
- **A user file or live scene is involved:** MCP code runs unguarded in the user's Blender. Stop
  before destructive operations unless saving was explicitly authorized; never delete user
  datablocks without asking; rebuild only owned study files from their scripts (RULES SAF_01).
- **A generated brep is not solid:** re-show the original rather than leaving a hole.
- Blender MCP not answering, Rook hanging and other symptoms: troubleshooting.md.

## Rhino
Rhino gives geometry only (RULES PIP_01): materials, lights, camera look and render settings live in
Blender, where the look has one place to edit; Rhino materials don't translate.
- **Never open, create or save over a user's open file** (check `sc.doc.Name` / `Modified`):
  single-document Rhino would close it. Build the study geometry in a `Rhino.FileIO.File3dm`
  instead: set `Settings.ModelUnitSystem`, add layers, add meshes from
  `Mesh.CreateFromBrep(brep, MeshingParameters.QualityRenderMesh)`, `f.Write(path, 7)`. With no
  Rhino open, `rhino_launch` starts an owned empty workbench that is safe to build in.
- **Render meshes:** `import_3dm` reads cached render meshes only; in an owned document run
  `obj.CreateMeshes(MeshType.Render, MeshingParameters.QualityRenderMesh, False)` before writing.
- **Rook scripts run on Rhino's UI thread and cannot be interrupted.** Keep each call short; run
  open, build and authorized save as three calls. A call that times out is still running: check
  Rhino's CPU before sending more.
- **Repeated elements as block definitions** import as instances; their mesh lives in the
  definition's collection, so assign their materials by object name.

## Study layout
`studies/<yymmdd>-<topic>/`: Rhino build script, `*.3dm`, `scene_geometry.py` + `scene_look.py`
(the names `study_run.py` expects), `.blend`, finals, `study-notes.md`, `library/` (RULES AST_01)
and `_wip/`. Everything a study makes (crops, comparisons, test renders, measurements, downloads,
throwaway scripts) goes in its `_wip/`, never the session scratchpad or %TEMP%, so one place holds
it all; tell subagents the path too (RULES AST_01). Delete `*.blend1` / `*.3dmbak`. Names: RULES
AST_03. Closing: [study-close.md](../workflow/study-close.md).
