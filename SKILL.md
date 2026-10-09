---
name: blender-archviz
description: >-
  The default for any rendering / visualization work: photoreal archviz in Blender 5.2 + Cycles
  (LuxCore when detailed caustics through glass or water matter),
  driven through the Blender Lab MCP, with Rhino (.3dm) as geometry only — materials (Poly Haven
  PBR, procedural stone/wood/metal/glass/water), daylight (calibrated HDRI) and artificial light
  in real lumens, physical camera, displacement, caustics, edge wear and chips, recreating a
  reference image, control renders and measurement. Use whenever the user mentions Blender,
  Cycles, shader/geometry nodes, Poly Haven, render, rendering, lookdev, materials, lighting,
  HDRI, caustics, LuxCore, glass blocks, patterned glass, water, exposure, a Render Reference Library image, or wants a photoreal image of
  a Rhino model — even without naming Blender. Also use it when pulling, editing or pushing this
  skill itself, so its MIGRATE.md and maintenance rules apply.
---
<!-- blender-archviz-skill-loaded-marker -->

# Blender archviz

**If `MIGRATE.md` exists in this folder, run it before anything else.** It holds what this machine must do after an update; the machine that runs it deletes it (`references/maintaining.md`).

Verified on Blender 5.2.2 LTS, Blender Lab MCP 1.0.3, import_3dm 0.0.18, RTX 3060 Ti 8 GB (OptiX),
Windows 10/11.

## Skill and project
- **This skill** (`~/.claude/skills/blender-archviz`, synced through GitHub) holds method and
  code: `RULES.md`, `references/`, `scripts/`. It is generic: it names no project or study,
  because every machine and every project loads it.
- **A project folder** (whichever one the user is working in) holds the data: `studies/`. It
  stays on that machine and is never pushed.
- **Each study owns its assets** (user rule): `studies/<yymmdd>_<topic>/library/` (`polyhaven/`,
  `local/` for edited HDRIs, generated maps, other sources) holds every HDRI, texture and
  generated bitmap that study renders with — downloaded again even if another study has the
  same file — so a study folder moves or archives on its own. Point everything at the study:
  `archviz.set_project(<study folder>)` in Blender, env `ARCHVIZ_PROJECT=<study folder>` for
  `polyhaven_fetch.py`. Without that, scripts take the nearest folder holding `library/` above
  the .blend / working directory — which may be an old shared project `library/`; never let a
  new study read from it.
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
| Helpers (run in Blender) | `scripts\blender\`: `archviz` (import, UVs, HDRI, camera, render), `study_materials`, `interior` (lights in lumens, stone, steel, water), `lookdev` (measured-albedo PBR, vertical boards, long pavers, sheers, glass shells, per-instance tone), `scatter` (GN leaf litter / foliage), `wear`, `wood_wear`, `glassware`, `gn_caustics`, `caustic_photons`, `render_variant` |
| Measure | `scripts\imgstats.py stats|patch|diff`; `scripts\refmatch.py grid|pair|patches` (render vs reference) — MCP venv python (`%LOCALAPPDATA%\BlenderMCP\venv\Scripts\python`) |
| Geometry check | `scripts\rhino\project_edges.py` (in Rhino via Rook, with the solved camera) → `scripts\edge_overlay.py edges.json ref.png out.png` |
| Reference recreation | `scripts\refsolve.py readings.json` (camera from a repeated element + image→plan); `scripts\study_run.py <study> vNN.png [--rebuild]` (syntax-check, render via MCP, pair + stack + patches) |
| Controls | `scripts\controls\light_units.py`, `mnee_water.py` — rerun after a Blender upgrade (`blender -b --factory-startup --python …`) |
| Caustics renderer | LuxCore via the BlendLuxCore extension (`references/luxcore.md`): PATH, CPU, *Add Light Tracing* |
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
   **Gate: stop and get the user's approval of the model before step 2** (RULES 10a).
2. **Import**: `bpy.ops.wm.read_homefile(use_empty=True)`, `archviz.import_rhino(path)` → layer
   collections, blocks → instances, named views → cameras, materials dropped, mm → m.
3. **UVs**: `archviz.box_uv(obj, size_m)`; wood `wood_wear.grain_uv(obj, tex_size_m, axis)`.
4. **Materials** by layer → `references/materials.md`.
5. **Light**: daylight = a **matching HDRI sky first** (RULES 8a), `archviz.world_hdri_lux` + matched sun; artificial `interior.downlight /
   led_strip / lens_luminance` → `references/lighting-camera.md`.
6. **Camera**: `archviz.physical_camera(cam, iso, f, shutter, focal)`, `straighten_verticals`,
   white balance if lights are warm. From a reference image: `refmatch.py grid` → solve the
   camera (`refsolve.py` when the image has a repeated element) → `archviz.framing_render()` +
   `refmatch.py pair --overlay`; then light region by region with `study_run.py`
   (lighting-camera.md › *Recreating a reference*).
7. **Render**: `archviz.render_setup(...)` → `references/render-settings.md`. Caustics through
   refractive glass in the shot → LuxCore instead (`references/luxcore.md`); Cycles otherwise.
8. **Look-dev**: headless `render_variant.py` or MCP renders into the study `_wip/`; measure
   with `imgstats`; prove each feature with a control (RULES 9). Reuse the helpers
   (`wear.set_input`, `study_materials.sock`, `archviz.pbr_material`, `lookdev`, `scatter`) instead of re-deriving
   node plumbing — the traps they wrap get hit again otherwise.
9. **Preview → approval → final** (RULES 10b): show a preview render and wait for the user's
   go before the final; state resolution, time and expected noise. The final runs in the open
   Blender UI so the user watches it live (pipeline.md › *Final render in the open UI*); never
   headless. Save the linear EXR + graded PNGs into the study folder.
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
| Scallops on walls | spots used as washers — grazing area strip |
| Image too cold after white balance | WB temperature = light shown neutral: raise it |
| Grain runs across planks | `grain_uv(axis=…)`, size = texture's real size |
| Out of memory on GPU | no adaptive subdivision on large diced areas; GN band detail; texture limits |
| GN geometry renders with source's material | Object Info keeps materials — Set Material |
| `bpy_struct[key] = val: id properties not supported` on a GN modifier | 5.2 inputs: `wear.set_input(mod, name, value)` |
| Region numbers identical after a geometry change | the patches miss the change — look at the image before concluding "no effect" |
| Lamp/bulb invisible in render | new lights default to `visible_camera = False` |
| Glazing far darker than the reference | glass reflects ~5 % at ~30°: brightness is the room behind (light it, declare it) or the HDRI direction the glass reflects (lighting-camera) |
| An area renders black that is bright in the ref | it is roofed in the model but open to the sky in the ref — check sky access |
| Visible joint grid on walls / a curved wall | texture tile edges — rotate/flatten the map (materials › Tiled maps) |
| Sun through patterned glass: fireflies, no caustic shape | specular–diffuse–specular paths from a sun-sized source: Cycles PT, path guiding and MNEE cannot resolve them — LuxCore CPU light tracing (caustics.md) |
| LuxCore render stops after a few seconds at "100 %" | halt-by-samples is on by default — `halt.use_samples = False` (luxcore.md) |
| LuxCore GPU light tracing changes nothing | it is a no-op on the GPU in 2.11 — light tracing runs on CPU (luxcore.md) |
| LuxCore sun casts but never glints through glass | `distant` lights are never hit by camera rays — use the `sun` type (luxcore.md) |
| LuxCore saved image noisy though OIDN ran | the denoised image is a separate DENOISED pass — route it through the compositor (luxcore.md) |
| Caustics a flat glow on far surfaces / one S-shaped bright line per pattern tile | relief too steep (focal length cm) / single-frequency pattern — size relief slope from receiver distance, randomise (caustics.md › Designing a refractive relief) |
| Rhino UI frozen by a Rook script | Python loop calling curve queries per element — kill Rhino (unsaved work lost); use closed-form layouts and time each step (pipeline.md) |
| Edited look script fails to run | a scripted edit put a `#` comment mid-call — syntax-check the scripts in the runner (pipeline) |
| Water/haze volume murky and dark | `cycles.volume_bounces` defaults to 0 — set 2-4 |
| Rhino boxes/slabs hang below their datum | `Extrusion.Create` follows the curve normal — `Surface.CreateExtrusion` (pipeline) |
| Ripples look fake or stretched | noise bump — Ocean geometry on a finer mesh, never stretch (materials › Water) |
| Numbers match, image doesn't | native-resolution crop pass beside the ref (RULES 8b) |
| Poly Haven download `HTTP Error 52x` | Cloudflare hiccup — retry the same call |

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
| `references/learning-from-video.md` | `yt_learn.py` use and rules |
| `references/capabilities.md` | What the pipeline can do and which technique does it |
