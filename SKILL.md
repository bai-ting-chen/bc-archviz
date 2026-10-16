---
name: blender-archviz
description: >-
  Default for any rendering or visualization work: photoreal archviz in Blender 5.2 + Cycles
  (LuxCore for detailed caustics through glass or water), with Rhino
  (.3dm) as geometry only. Covers materials (Poly Haven PBR, procedural concrete, wood, stone,
  metal, glass, water; edge wear, chips, cracks, leak streaks, anti-tiling), HDRI
  daylight and lights in real lumens (IES/LDT), physical camera, caustics, fog and mist,
  terrain, grass and meadow scatter, wet surfaces, matching a reference image, controls
  and finals. Use whenever the user mentions Blender, Cycles, LuxCore, shader or geometry nodes,
  Poly Haven, rendering, lookdev, lighting, HDRI, lux, caustics, fireflies or
  denoising, a Render Reference Library image, or wants a photoreal image of a Rhino model, even
  without naming Blender. Also for bringing 3ds Max (.max) assets into Blender (Maxtree,
  Evermotion, Forest Pack vegetation; V-Ray or Corona props), and for pulling, editing or
  pushing this skill (MIGRATE.md and maintenance rules).
---
<!-- blender-archviz-skill-loaded-marker -->

# Blender archviz

**If `MIGRATE.md` exists in this folder, run it before anything else.** It holds what this machine must do after an update; the machine that runs it deletes it (`references/maintaining.md`).

Verified on Blender 5.2.2 LTS, Blender Lab MCP 1.0.3, import_3dm 0.0.18, BlendLuxCore 2.11.1, RTX 3060 Ti 8 GB (OptiX),
Windows 10/11.

## Skill and project
- **This skill** (`~/.claude/skills/blender-archviz`, synced through GitHub) holds method and
  code: `RULES.md`, `references/`, `scripts/` (scope: RULES 0, 0a).
- **A project folder** (whichever one the user is working in) holds the data: `studies/`. It
  stays on that machine and is never pushed.
- **Assets** (RULES 10c): `studies/<yymmdd>_<topic>/library/` (`polyhaven/`, `local/`). Point
  scripts at the study with `archviz.set_project(<study>)` / env `ARCHVIZ_PROJECT=<study>`.
  Without that, `projectpath.find_project` searches up from the .blend / working directory and
  stops at the study folder (a folder inside `studies/`), so a new study gets its own
  `library/`; a shared `library/` above is used only for studies listed in its
  `legacy_studies.txt`.
- **The Blender MCP server** is a per-machine install in `%LOCALAPPDATA%\BlenderMCP\` (`app\`,
  `venv\`), registered in Claude Code at user scope, like Rook in `%LOCALAPPDATA%\Rook\`.

`scripts\…` paths below are in the skill; `studies\` is in the project, `library\` in the study.
**Changing, pulling or pushing this skill?** Read `references/maintaining.md` first. It covers
what may go in, `git pull` before editing, the git identity, and the `MIGRATE.md` every push
must leave for the other machines.

## Preflight — copy into your first response and tick off
```
- [ ] Read RULES.md and the references/ file for the task — both live in THIS skill folder,
      not the project; skim api-traps.md before writing node/GN code
- [ ] `%LOCALAPPDATA%\BlenderMCP\AGENT_LOCK` absent or mine (RULES 16); create it before driving Blender
- [ ] Blender open, MCP on 9876 (get_blendfile_summary_datablocks)
- [ ] Rhino: which document is open, is it modified? A user's file stays untouched — write
      the study geometry with File3dm (pipeline.md)
- [ ] Local studies? read `studies/README.md` + the latest STUDY_NOTES.md (open items carry over)
- [ ] New technique? research the physics first, then compare workflows (RULES 3)
- [ ] Before every "done": native-resolution crop pass of each material vs the ref (RULES 8b)
- [ ] Look decision? profile the Render Reference Library slice
- [ ] Study folder set? `archviz.set_project(<study>)`; every asset downloaded/generated into
      the study's own `library/` (`ARCHVIZ_PROJECT=<study> polyhaven_fetch.py …`)
- [ ] Caustics through glass/water central to the shot? → LuxCore (RULES 2a, `references/luxcore.md`);
      otherwise Cycles
- [ ] Final render: preview approved by the user first, then render in the open UI (RULES 10b)
```

## Stack
| Piece | Where |
|---|---|
| Blender | `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe` |
| MCP | server `%LOCALAPPDATA%\BlenderMCP\venv\Scripts\blender-mcp.exe` (user scope, `claude mcp get blender`); add-on `mcp` autostarts on 127.0.0.1:9876 (needs Prefs → *Allow Online Access*) |
| Helpers (run in Blender) | `scripts\blender\`: `archviz` (import, UVs, HDRI, camera, render), `study_materials`, `interior` (lights in lumens, stone, steel, water), `lookdev` (measured-albedo PBR, vertical boards, long pavers, sheers, glass shells, per-instance tone), `scatter` (GN leaf litter / foliage), `wear`, `wood_wear`, `glassware`, `gn_caustics`, `caustic_photons`, `render_variant`, `lux_materials` (LuxCore: baked corner dust, native Randomized Tiling, per-instance glass tint), `from_passes` (finals from a multilayer passes EXR) |
| Outdoor | `scripts\blender\`: `terrain` (landform hill around a pad, ground with bare soil), `scatter.meadow_layer_group` (grass on terrain), `vegetation` (grass blades, wet film, dew), `atmosphere` (Mie fog from visibility) |
| Finals (Cycles) | `scripts\blender\finals.py`: untiled no-limit final in the UI, savers, OIDN from passes, graded PNG |
| 3ds Max assets | `scripts\blender\max_import.py`: `load` (io_scene_max extension + repairs), `tidy`, `rebuild_materials`, `open_loops` — `references/max-import.md` |
| Photometry | `scripts\ldt2ies.py in.ldt out.ies` (Eulumdat → IES for Cycles, lumens checked); IES files → `interior.ies_light` |
| Measure | `scripts\imgstats.py stats|patch|diff`; `scripts\refmatch.py grid|pair|patches` (render vs reference) — MCP venv python (`%LOCALAPPDATA%\BlenderMCP\venv\Scripts\python`) |
| Geometry check | `scripts\rhino\project_edges.py` (in Rhino via Rook, with the solved camera) → `scripts\edge_overlay.py edges.json ref.png out.png` |
| Reference recreation | `scripts\refsolve.py readings.json` (camera from a repeated element + image→plan); `scripts\study_run.py <study> vNN.png [--rebuild]` (syntax-check, render via MCP, pair + stack + patches) |
| Maintenance | `scripts\helper_index.py` (writes references/helpers.md), `scripts\regress_helpers.py` (old vs new helper output), `scripts\codex_review.py` (Codex reviews a change before push, RULES 14) |
| Tiles | `scripts\blender\`: `tile_mapping` (metre UVs: planar, cylinder, annulus), `tile_layout` (tile id/UV/edge/joint node group), `tile_surface` (tile material, `use_damage_displacement`), `tile_damage` (Voronoi crack network; chips WIP) — materials.md › Tiles |
| Controls | `scripts\controls\light_units.py`, `ies_units.py`, `mnee_water.py` — rerun after a Blender upgrade (`blender -b --factory-startup --python …`); `tile_layout_check`, `tile_mapping_check`, `tile_surface_check`, `tile_damage_check` (`--only <section>`, `--full`) |
| Caustics renderer | LuxCore via the BlendLuxCore extension (`references/luxcore.md`): PATH, GPU + *Use CPUs*, *Add Light Tracing* |
| Assets | `scripts\polyhaven_fetch.py` → `<study>\library\polyhaven\` (env `ARCHVIZ_PROJECT=<study>`); others `<study>\library\local\` with a `meta.json` |
| Video research | `scripts\yt_learn.py` |

In Blender code: `sys.path.insert(0, os.path.expanduser(r"~\.claude\skills\blender-archviz\scripts\blender"))`.
Without the MCP tools loaded (session started elsewhere), drive Blender with
`scripts/mcp_call.py execute_blender_code --file script.py`; the script must assign a **dict** to `result`.
Anything in a Blender panel is RNA → scriptable via MCP `execute_blender_code`. Not scriptable:
hand tools (sculpt, knife, gizmos). The MCP bundles the 5.x manual + API offline
(`search_manual_docs`, `get_python_api_docs`) — the authority for generic Blender facts.

## Workflow
1. **Rhino** (Rook): geometry on named layers; force render meshes; save `.3dm` — or, when the
   user has their own file open, build meshes into a `File3dm` and write it (pipeline.md).
   Then the model gate (RULES 10a).
2. **Import**: `bpy.ops.wm.read_homefile(use_empty=True)`, `archviz.import_rhino(path)` → layer
   collections, blocks → instances, named views → cameras, materials dropped, mm → m.
3. **UVs** at the texture's real size: non-directional textures (plain concrete, plaster,
   terrazzo, mortar, gravel) `archviz.box_uv(obj, size_m)`; directional ones (wood grain, boards,
   brushed metal, vein-cut stone, ribbed sheet, weave, long tiles) `archviz.directional_uv(obj,
   size_m, axis)` so the direction follows the element on every face (materials.md › Choosing).
4. **Materials** by layer → `references/materials.md`.
5. **Light**: daylight (RULES 8a) `archviz.world_hdri_lux`, rotated by its `hdri_analyse` sun
   direction; artificial: the fixture's IES file `interior.ies_light` when it is specified, else `interior.downlight /
   led_strip / lens_luminance` → `references/lighting-camera.md`.
6. **Camera**: `archviz.render_setup(...)` first (it resets view exposure; step 7), then
   `archviz.physical_camera(cam, iso, f, shutter, focal)`, `straighten_verticals`,
   white balance if lights are warm. From a reference image: `refmatch.py grid` → solve the
   camera (`refsolve.py` when the image has a repeated element) → `archviz.framing_render(root, path)` +
   `refmatch.py pair --overlay`; then light region by region with `study_run.py`
   (lighting-camera.md › *Recreating a reference*).
7. **Render**: settings → `references/render-settings.md`; LuxCore case
   (RULES 2a) → `references/luxcore.md`.
8. **Look-dev**: headless `render_variant.py` or MCP renders into the study `_wip/`; measure
   with `imgstats`; prove each feature with a control (RULES 9). Reuse the helpers
   (`references/helpers.md` lists them all: `wear.set_input`, `archviz.sock`, `archviz.pbr_material`,
   `study_materials.G`, `lookdev`, `scatter`) instead of re-deriving
   node plumbing — the traps they wrap get hit again otherwise.
9. **Final** (RULES 10b) → pipeline.md › *Final render in the open UI* (Cycles: `finals.py`); linear EXR + graded
   PNGs into the study folder.
10. `studies/<yymmdd>_<topic>/STUDY_NOTES.md`: what, proof numbers, traps, open items.

## Troubleshooting
| Symptom | Fix |
|---|---|
| MCP port 9876 not listening | Prefs → System → *Allow Online Access*; or Blender was closed — no `blender.crash.txt` in %TEMP% = closed, relaunch |
| Camera framing far off after setting lens shift | shift units/sign trap — probe with `world_to_camera_view` (lighting-camera) |
| Whole floor/slab gets edge grime | object without the GN modifier reads `edge_dist` = 0 = "on an arris" — gate it (edge-wear) |
| One long line runs down the camera axis on floor and ceiling | a texture's panel joint at UV 0 = world 0 — offset the UVs (materials) |
| `refmatch.py` / `imgstats.py`: No module named numpy | `pip install numpy pillow` into the MCP venv |
| Imported object has 0 faces | no cached render mesh in the .3dm — force render meshes in Rhino |
| Material/light change has no visible effect | look at the control; suspiciously identical numbers = feature not removed / stale mesh (`update_tag()` + `view_layer.update()`) |
| Colour cast from a pool or glass | a lens seen through water by transmission rays — `interior.lit_once()` (lighting-camera) |
| Submerged surfaces black under lamps | shadow rays can't pass refraction — MNEE with a diced top plane (caustics.md) |
| Unwanted scallops on a washed wall | spots used as washers — a linear source along the wall (lighting-camera) |
| Image too cold after white balance | WB temperature = light shown neutral: raise it |
| Grain / boards / brushing turns 90° between faces or runs across planks | `archviz.directional_uv(axis=…)`, size = texture's real size |
| Out of memory on GPU | no adaptive subdivision on large diced areas; GN band detail; texture limits |
| GN geometry renders with source's material | Object Info keeps materials — Set Material |
| `bpy_struct[key] = val: id properties not supported` on a GN modifier | 5.2 inputs: `wear.set_input(mod, name, value)` |
| Region numbers identical after a geometry change | the patches miss the change — look at the image before concluding "no effect" |
| IES / point light much dimmer than the hand calc | its sphere (radius) is partly inside the ceiling or housing — centre it radius + 2 mm clear (lighting-camera › IES) |
| Scripted camera faces the wrong way / huge lens shift | `matrix_world` stale after setting rotation — `view_layer.update()` (fixed in `straighten_verticals`) |
| Lamp/bulb invisible in render | new lights default to `visible_camera = False` |
| Glazing far darker than the reference | glass reflects ~5 % at ~30°: brightness is the room behind (light it, declare it) or the HDRI direction the glass reflects (lighting-camera) |
| An area renders black that is bright in the ref | it is roofed in the model but open to the sky in the ref — check sky access |
| Visible joint grid on walls / a curved wall | texture tile edges — rotate/flatten the map (materials › Tiled maps) |
| Sun through patterned glass: fireflies, no caustic shape | specular–diffuse–specular paths from a sun-sized source: Cycles PT, path guiding and MNEE cannot resolve them — LuxCore light tracing (caustics.md) |
| LuxCore render stops after a few seconds at "100 %" | halt-by-samples is on by default — `halt.use_samples = False` (luxcore.md) |
| LuxCore GPU light tracing changes nothing | light tracing runs on CPU threads: Devices › *Use CPUs* on, GPU light-ray field (`_opencl`) 100 % (luxcore.md) |
| LuxCore caustic final takes many hours | CPU-only: switch to GPU + *Use CPUs* (2–6× at equal noise); geometry is not the cost — no displacement/normal-map shortcut (luxcore.md › Speed) |
| LuxCore test sun casts but never glints through glass | `distant` lights are never hit by camera rays — use the `sun` type (luxcore.md) |
| LuxCore saved image noisy though OIDN ran | the denoised image is a separate DENOISED pass — route it through the compositor (luxcore.md) |
| Caustics a flat glow on far surfaces / one S-shaped bright line per pattern tile | relief too steep (focal length cm) / single-frequency pattern — size relief slope from receiver distance, randomise (caustics.md › Designing a refractive relief) |
| Rhino UI frozen by a Rook script | Python loop calling curve queries per element — kill Rhino (unsaved work lost); use closed-form layouts and time each step (pipeline.md) |
| Edited look script fails to run | a scripted edit put a `#` comment mid-call — syntax-check the scripts in the runner (pipeline) |
| Water/haze/fog volume murky and dark | `cycles.volume_bounces` defaults to 0 (api-traps › Render) |
| Rhino boxes/slabs hang below their datum | `Extrusion.Create` follows the curve normal — `Surface.CreateExtrusion` (pipeline) |
| Ripples look fake or stretched | noise bump — Ocean geometry on a finer mesh, never stretch (materials › Water) |
| Numbers match, image doesn't | native-resolution crop pass beside the ref (RULES 8b) |
| Poly Haven download `HTTP Error 52x` | Cloudflare hiccup — retry the same call |
| Cloudy blotches on smooth walls/ceiling after OIDN (LuxCore) | fireflies from caustic-bounce paths — radiance clamping, not more time (luxcore.md › Fireflies) |
| Saved final is grainy after a stop or cancel | the denoiser/compositor was skipped — Cycles: `finals.py -- denoise` from the passes EXR; LuxCore: `from_passes.py` |
| LuxCore crashes at export, `EXCEPTION_ACCESS_VIOLATION` in pyluxcore | a native mapping's `uvindex` points at a missing UV layer (luxcore.md › Native) |
| Script works headless, fails in the UI ("Context missing active object") | operators need `temp_override` in a UI startup script (api-traps) |
| Rook call hangs / "dispatcher busy" / file won't open | long script still running, or a modal dialog (save-changes, crash report) — split calls; pipeline › Rhino |
| Imported .max: trunk/twigs missing, leaves rendered as bark, bark squashed | stock io_scene_max import — use `max_import.load` and its checks (max-import.md) |
| Back-lit leaves glint white | the importer's stored glossiness scalar used instead of the wired glossiness map (max-import.md › Materials) |
| Render white / exposure ignored | `archviz.render_setup` sets view exposure — call it before `physical_camera` |
| No-limit final renders only one block ("0/4 tiles") | auto-tiling: tile off + tile size > frame (`finals.setup_unlimited`) |
| Light triangles hanging below an arris | leak/raycast field computed after the chips - leak field first (edge-wear.md) |
| Grass sinks dark / lawn reads grey when wet | canopy albedo is ~0.05-0.1 (softer AgX look); wet sheen at grazing - darker base (materials.md) |
| House edge crisp against a soft HDRI backplate | slight DOF in front of the subject (lighting-camera.md > Soft backplate) |
| Caustics on a wall look like vertical streaks | seen at a grazing angle; judge on a face-on surface (caustics.md) |
| Foam reads as snow cones with black holes | spiky short boils + a hard foam switch over a dark trench — rounded chop, milky subsurface whitewater, soft foam mask (water-features.md) |
| Black band at a waterline seen through glass | open water sheet over a void: sight lines end on the dark floor — opaque milky body under the troughs (water-features.md) |
| Splash drops read as a dark band | clear drops in soft light refract the dark surroundings — fewer, higher, spread (water-features.md) |
| Camera from a Rhino named view frames wider/narrower | Rhino's lens length refers to the frame's short side on a square view — match the frustum (pipeline.md) |

More traps: `references/api-traps.md`.

## References
| File | Contents |
|---|---|
| `RULES.md` | House rules (what belongs here, priorities, split, look, process, safety) |
| `references/maintaining.md` | Changing the skill: scope, pull, git identity, MIGRATE.md, push |
| `references/pipeline.md` | Install, MCP server, Rhino import, assets, iteration loop, study layout |
| `references/lighting-camera.md` | HDRI lux, sun, artificial lights in lumens, ray visibility, EV100, white balance, recreating a reference (camera solve incl. from repeated elements + image→plan, geometry readings, hidden lights, glazing/HDRI reflection, region balancing) |
| `references/materials.md` | Physical ranges, albedo from measured map means, texture choice, concrete (one-material rooms, patch grunge, tiled joints, vertical boards), aggregate, pavers, GN litter/foliage, gravel, wood, stone, steel, glass, sheers, water |
| `references/caustics.md` | Decision order (measured renderer ranking), comparing renderers with controls, designing a refractive relief (focal length, fold lines, per-instance variants), MNEE, GN wavefront, photon bake |
| `references/luxcore.md` | LuxCore for caustics: install, engine settings, sun/HDRI calibration against Cycles, LuxCore-safe materials, denoised output, UI final, traps |
| `references/edge-wear.md` | Dirty edges vs chips (GN), whole-room gating, corner grime, wood wear |
| `references/render-settings.md` | Sampling, denoise, bias list, memory, colour management |
| `references/api-traps.md` | Blender 5.2 API gotchas |
| `references/max-import.md` | 3ds Max assets: io_scene_max install, the four importer faults and their repair, per-model checks, rebuilding V-Ray materials (leaf cards) |
| `references/helpers.md` | Every public helper in `scripts/blender/` with signature and purpose (generated) |
| `references/learning-from-video.md` | `yt_learn.py` use and rules |
| `references/capabilities.md` | What the pipeline can do and which technique does it |
| `references/water-features.md` | Water down walls and glass, overflow edges, whitewater, choppy pools; procedural vs simulation (Mantaflow, FLIP Fluids); brushed metal and cast glass beside water |
