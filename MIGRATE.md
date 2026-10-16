# MIGRATE — run before anything else, then delete

## 261008 — LuxCore for caustics, per-study assets, final-render gate
A study of sun caustics through patterned glass showed Cycles (path tracing, path guiding, MNEE)
cannot converge them; LuxCore CPU light tracing can and is energy-correct. The user made three
standing rules: Cycles stays default but LuxCore is preferred for detailed caustics (RULES 2a);
every study owns its assets in its own `library/` (RULES 10c); a final render needs the user's
approval of a preview and runs in the open Blender UI (RULES 10b). New `references/luxcore.md`;
caustics, lighting-camera, materials, pipeline, api-traps, capabilities and SKILL.md updated.

### 1. Install BlendLuxCore (needs Blender 5.2)
Check: `%APPDATA%\Blender Foundation\Blender\5.2\extensions\user_default\blendluxcore\blender_manifest.toml` exists with `version = "2.11.1"` or newer.
Do: `gh release download v2.11.1 -R LuxCoreRender/BlendLuxCore -p "BlendLuxCore-2.11.1.zip" -D <empty temp folder>`;
compare its sha256 with `gh release view v2.11.1 -R LuxCoreRender/BlendLuxCore --json assets`;
`"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b -c extension install-file -r user_default --enable <zip>`
(the log must say `BlendLuxCore 2.11.1 registered (with pyluxcore …)`); delete the zip.

### 2. Pick up the new rules in local memory
Check: the project's memory index (`~/.claude/projects/<project>/memory/MEMORY.md`) has entries for per-study assets, the final-render gate and LuxCore for caustics.
Do: add one memory file each (feedback type) summarising RULES 10c, 10b and 2a, and the index lines.

### 3. Project layout
Check: new studies are created with their own `library/` (`polyhaven/`, `local/`); the project `CLAUDE.md` does not describe a shared `library/` as where studies read assets.
Do: update the project `CLAUDE.md` table: assets live in each study's `library/`; a top-level
`library/` remains only for studies that already use it (leave finished studies untouched).

### 4. Directional UVs moved into archviz
Check: `scripts/blender/archviz.py` defines `directional_uv` (it does after pulling).
Do: nothing to run. New code calls `archviz.directional_uv(obj, size_m, axis)` for any
directional texture (grain, boards, brushing, veining, long tiles); `wood_wear.grain_uv` still
works as an alias for older study scripts.

### 5. HDRI is the sole natural light
Check: the project's memory index has an entry saying an HDRI sky is never combined with a sun lamp.
Do: add that memory (feedback type) from RULES 8a; in any open study script, remove sun lamps
that sit alongside an HDRI and rotate the HDRI to place its own sun instead.

## 261009 — Review: general knowledge only, each rule once
Pull-only. RULES.md and every reference were reviewed: study anecdotes and one scene's tuned
numbers removed or generalised, provenance tags dropped, each rule stated once in RULES.md with
pointers elsewhere, the clean-arcs Rhino rule removed, `archviz.directional_uv` added. Re-read
RULES.md; drop any local memory that repeats the removed clean-arcs Rhino rule.

### 6. Local memory
Check: the project's memory has no entry telling Rhino models to use one arc per curved edge.
Do: delete such a memory file and its index line.

## 261010 — LuxCore fireflies, glass-block relief, dust, randomness, final-render safety
A long LuxCore study of sun caustics through a glass-block wall showed: OIDN turns caustic-bounce
fireflies into blotches that more time cannot fix — radiance clamping (camera paths only)
removes them without touching the caustics; a render cancelled from Blender skips the
compositor, so finals are now built from a multilayer passes EXR; long-wave reliefs at a higher
slope make units' caustics tangle into one net; corner dust and anti-tiling for LuxCore need a
Cycles bake and native node trees. New user rules: RULES 8d (repetition and imperfection, corner
dust), 10b step 4 (full-frame test of the exact final settings before any long run; raise known
fixes first) and 10d (everything a study makes stays in its folder). New scripts
`scripts/blender/lux_materials.py` and `scripts/blender/from_passes.py`. Updated: luxcore,
caustics, edge-wear, materials, pipeline, api-traps, render-settings, capabilities, SKILL.md.

### 7. Local memory for the new rules
Check: the project's memory index has entries for (a) randomness on repeated units + corner dust,
(b) saving everything inside the study folder, and (c) the full-frame pre-final test in the
final-render-gate memory.
Do: add/extend those memory files (feedback type) from RULES 8d, 10d and 10b (4), with index lines.

### 8. Study scripts that saved finals from the composite
Check: no open (unfinished) study script saves its final from the composited Render Result
without also writing a multilayer passes EXR.
Do: in such scripts, save all passes (`media_type = "MULTI_LAYER_IMAGE"`) and build finals with
`scripts/blender/from_passes.py`. Leave finished studies alone.


## 261011 — LuxCore: GPU + CPU light tracing; geometry is not the cost
A speed study of a glass-block caustic scene showed the old "light tracing is a no-op on the GPU"
came from a test with *Use CPUs* off. In PATHOCL, light tracing runs on the native CPU threads
while the GPU does camera paths: same image, 2–6× faster at equal noise than CPU-only. Flat
blocks instead of a modelled relief were only 1.1–1.3× faster, so displacement / normal maps are
no speedup. Updated: luxcore.md (engine settings, Speed bullets, PhotonGI), caustics.md, RULES 2a,
SKILL.md, capabilities.md.

### 9. Local memory: LuxCore device
Check: the project's LuxCore-for-caustics memory does not say "CPU light tracing" as the setup (or says GPU + Use CPUs).
Do: edit it to "LuxCore PATH + light tracing, GPU camera paths + Use CPUs (CPU light paths)".

### 10. Open study scripts that force CPU-only or disable native threads
Check: no open (unfinished) study script sets `cfg.device = "CPU"` for a final or `devices.use_native_cpu = False` with light tracing.
Do: switch them to `cfg.device = "OCL"`, `use_native_cpu = True`, `hybridbackforward_lightpartition_opencl = 100`. Leave finished studies alone.

## 261011 — Light types and IES photometry
Cycles' IES Texture converts candela with 177.83 lm/W (D65), not the skill's 683, so an IES on a
1 W light is 3.84x too bright; on a point light, power 177.83/683 W reproduces the file's candela
exactly (control `scripts/controls/ies_units.py`, real files 1.000). New `interior.ies_read`
(lumens, beam/field angles from the file) and `interior.ies_light` (point light, embedded file,
optional lumen rescale). lighting-camera.md has a light-type table and an IES section (scale,
orientation, absolute vs relative photometry, where to get files); SKILL.md and capabilities.md
updated.

Also: `scripts/ldt2ies.py` (Eulumdat → IES); linear fixtures as N point lights; a light's
sphere must sit clear of the ceiling/housing; `archviz.straighten_verticals` now updates the
view layer first (it misread scripted cameras); `archviz.render_setup` enables OptiX when the
preferences have no compute device (`--factory-startup` rendered on CPU before).

### 11. IES files per study
Check: `scripts/blender/interior.py` defines `ies_light` (it does after pulling).
Do: nothing to install. Fixture IES files go in the study's `library/local/ies/` with a
`meta.json`; never set an IES light's power by eye.

## 261011b — Full review of docs and scripts
Pull-only. Docs: README describes per-study assets; RULES 5 now requires a specified fixture's
photometric file; lighting-camera gains the incident-meter exposure (EV100 = log2(E/2.5)) and
correct helper signatures; caustics and edge-wear lose one scene's numbers; video outputs go to
the study `_wip/`; SKILL description triggers on IES/LDT/lux. Scripts: `mcp_call.py` image
output crash fixed; `concrete_study(stain_map=…)` stops with a clear message when the leak map
is missing; `caustic_photons` stores its receiver grid with the geometry and takes
`albedo_label`; `render_variant` options `key_target`, `coll`; cleanup on failure in
`study_run`, `polyhaven_fetch`, `lux_materials.bake_dust`; `refsolve` reports parallel lines.

### 12. Callers of changed signatures
Check: no open (unfinished) study script calls `render_variant … key_area=` expecting the aim
point at z 0.73, or `caustic_photons.add_caustic_light` on a receiver whose BSDF is not labelled
"Pine + satin varnish coat" without passing `albedo_label`.
Do: add `key_target=0,0,0.73` / `albedo_label=…` there. Leave finished studies alone.

## 261011c — One builder per job; helper index; regression tool
Duplicated helpers merged, old names kept as aliases (no study script has to change):
`archviz.dielectric` is the one clear-glass/water builder (`glass_material`,
`study_materials.clear_glass`, `glassware.dielectric` call it); `study_materials.G` is the one
node-graph builder for shader and GN trees (`wear._GN` and `wear._math/_range/_noise/_attr` are
aliases; `G(node_tree)` adds to an existing tree); `archviz.read_meta/write_meta`,
`archviz.use_gpu`, `archviz.sock` (still importable from study_materials). The concrete and wood
GN wear groups share `wear._edge_field/_chip_field/_rejoin` and both gain a **Seed** input
(`add_edge_wear(obj, g, Seed=(x, y, z))` = per-object chips). Proof: every material and group
built by old and new code fingerprints identical except the Seed input; evaluated wear meshes
identical vertex for vertex; all three controls print the same numbers. New:
`references/helpers.md` (generated by `scripts/helper_index.py`), `scripts/regress_helpers.py`,
`scripts/controls/_scene.py`; maintaining.md › Helpers changed.

### 13. Saved .blend files with the old wear groups
Check: nothing to do unless an open study rebuilds a wear group and then sets inputs by socket
identifier (`Socket_N`) instead of by name.
Do: set inputs by name (`wear.set_input` / `add_edge_wear`) — the new Seed input shifts the
output socket's identifier.

## 261011d — Code review fixes (each reproduced in Blender/Rhino, then fixed)
`lux_materials.bake_dust` bakes every object under Cycles (only the first did); 
`caustic_photons.add_caustic_light` can be re-run, and the receiver grid travels as
`<file>.grid.json`; `study_materials.solve_levels` measures linear values (it read sRGB-encoded
bytes), so **`coated_wood` / `weathered_wood` now reach their target albedo** — before, the pine
came out at about (0.31, 0.14, 0.05) against a target of (0.52, 0.33, 0.17); `interior` lights
refuse a name held by a non-light object and switch light kind on re-run; `render_variant`
refuses unknown options, implements `stain=off` and renders on the GPU; `gn_caustics` takes
`floor_albedo`; `archviz.glass_material` edits an existing material in place again and
`simple_material` repairs a missing Principled; `scripts/rhino/project_edges.py` reads the model
units and includes block instances and meshes.

### 14. Open studies that use coated_wood / weathered_wood
Check: no open (unfinished) study rebuilds its look with `study_materials.coated_wood` or
`wood_wear.weathered_wood` and relies on the old (darker) pine.
Do: re-render a preview of that study and re-tune its wood target if the brighter, correct pine
is not wanted. Leave finished studies alone.

## 261011e — 3ds Max (.max) assets into Blender
Vendor vegetation libraries ship as `.max` with V-Ray materials. Blender reads them through the
`io_scene_max` extension, but version 1.9.2 drops tube bands (trunks, twigs: 13-28 % of faces),
shifts material IDs after them, maps Multi/Sub slots wrongly and can take vertex colours as UVs.
New `scripts/blender/max_import.py` (`load` repairs all four; `tidy`, `rebuild_materials`,
`open_loops`) and `references/max-import.md` (install, faults, per-model checks, leaf-card
material; a wired V-Ray map beats its stored scalar). Proved on four models, 25-320 MB.
RULES 10d: software (extensions, add-ons) installs into Blender's own folder, never a study.
SKILL.md (description, stack, troubleshooting, references), capabilities.md, api-traps.md
(`render_setup` before `physical_camera`) and helpers.md updated.

### 15. Install the .max importer (needs Blender 4.2+)
Check: `%APPDATA%\Blender Foundation\Blender\5.2\extensions\user_default\io_scene_max\blender_manifest.toml` exists with `version = "1.9.2"` or newer.
Do: read `archive_url` and `archive_hash` for id `io_scene_max` from
`https://extensions.blender.org/api/v1/extensions/?type=add-on`; download into an empty temp
folder; compare the sha256; `"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b -c extension install-file -r user_default --enable <zip>`; delete the zip and folder.
A newer version may fix some faults: rerun the checks in max-import.md on one model either way.

### 16. Local memory: software is not study output
Check: the project's memory index has an entry saying Blender extensions / add-ons install into Blender's extension folder, never a study folder.
Do: add that memory (feedback type) from RULES 10d, with its index line.

### 17. Studies with their own copy of a .max repair script
Check: no open (unfinished) study folder contains its own `max_import.py`.
Do: import it from the skill (`scripts/blender` on `sys.path`) and delete the local copy.

## 261011f — Asset lookup stops at the study folder
`archviz.library()` and `polyhaven_fetch.py` used the nearest `library/` above the working
folder, so a new study without its own `library/` silently read and downloaded into a shared
one (against RULES 10c). New `scripts/blender/projectpath.py` (one resolver for both): inside a
study (a folder in `studies/`) the search stops at the study; a shared `library/` above is used
only for studies listed in its `legacy_studies.txt`; `polyhaven_fetch` prints a NOTE when it
downloads outside a study. Tested: resolver cases, fetch destinations, legacy studies loading
their assets in Blender, helper fingerprints old = new, the three controls.

### 18. List the studies that still read a shared library
Check: in every project here with a top-level `library/`, each study folder in `studies/` that
has no `library/` of its own but whose scripts load assets (`archviz.library`, `pbr_material`,
`world_hdri*`, `study_materials`, `lookdev`) is listed in `<project>/library/legacy_studies.txt`.
Do: write that file, one study folder name per line (`#` comments allowed). Without it those
studies resolve to their own empty folder and fail on missing textures. Never list new studies.

## 261012 — Outdoor: terrain, meadow, wet lawn, fog; facade runoff, cracks, glass; no-limit finals
New modules from a house-on-a-hill study (sunny and foggy wet morning): `terrain.py` (landform hill
around a pad, ground with bare soil), `scatter.meadow_layer_group` (Blender's own Scatter on
Surface + patch / bare-soil / pad / frustum masks), `vegetation.py` (modelled grass blades, wet
film, near-camera dew), `atmosphere.py` (Mie fog, density from visibility; control
`scripts/controls/fog_koschmieder.py` = 1.000), `finals.py` (untiled no-limit Cycles finals,
savers, OIDN from passes). Added to `wear.py` (raycast leak field - must be the first modifier -,
runoff/grunge/splash, cracks; `weathered_concrete(tex_id=...)`), `study_materials.retone`,
`lookdev.glass_distortion`, `max_import.slot_maps` / `origin_to_root`. Smoke test
`scripts/controls/outdoor_smoke.py` runs all of it on a new scene; regress_helpers: the 35
existing helpers build identically. RULES 8 gains one sentence (sub-pixel effects = their
aggregate). Docs: materials (Terrain, Grass and meadow, Wet surfaces and dew, glass distortion),
edge-wear (Runoff streaks, cracks), lighting-camera (Fog and mist, Soft backplate), render-settings
(Finals with no sample limit), api-traps, max-import (vendor scene files), pipeline, capabilities,
SKILL.md.

### 19. Local memory: sub-pixel effects
Check: the project's memory index has an entry saying a named effect (dew, frost, rain) means how it reads at the shot's distance - model the aggregate, ask before micro-geometry.
Do: add that memory (feedback type) from RULES 8, with its index line.

### 20. No-limit Cycles finals
Check: no open (unfinished) study script starts a no-limit Cycles final with auto-tiling on.
Do: use `finals.start_in_ui(out_dir, res)` (or set `use_auto_tile = False` and `tile_size` above the frame), and after a stop check whether Combined == Noisy Image; if so `finals.py -- denoise` from the passes EXR.

## 261012b — Code review fixes to the outdoor helpers
Pull-only. Fixed: `wear.leak_field_group` / `scatter.meadow_layer_group` no longer delete a group
other objects use (a 2nd wall lost its leak streaks); `study_materials.retone(mat, target, tex_id,
saturation)` desaturates by a luminance mix (Hue/Saturation came out ~25 % too bright) and
needs tex_id; `lookdev.glass_distortion` uses the pane's own coordinates (rotated or shared panes);
`max_import.slot_maps` matches the longest existing tail and ignores `.001`; `wear.add_runoff`
measures along any wall orientation and takes `ground_z`; one `terrain.BARE` constant; dew beads
offset per instance; essentials path via `bpy.utils.system_resource`; `finals` guards an
unsaved .blend and takes the view-layer name. Smoke test extended to cover each.

### 21. Callers of retone
Check: no open (unfinished) study script calls `study_materials.retone` with the old argument order (target, saturation, tex_id=...).
Do: call `retone(mat, target_rgb, tex_id, saturation=0.25)`.

## 261012c — Skill review: description, consistency, rule pointers
Pull-only. SKILL.md description cut to 999 characters (spec limit 1024) with every trigger kept;
Workflow: `render_setup` before `physical_camera` (it resets exposure - the old order rendered
white); glassware caustics follow RULES 2a (LuxCore; `caustic_photons` = Cycles-only fallback);
finals denoise with OIDN on the GPU (`finals.setup_unlimited`); one volume-bounce statement
(api-traps: 2-4 water/haze, ~8 Mie fog); one grainy-after-stop troubleshooting row per engine;
EV table sunny-16 fixed (f/16 1/125); RULES 9 control criterion = > 2 % and several x the noise
floor; rule restatements in render-settings, lighting-camera, pipeline, edge-wear replaced by
pointers; materials.md has a contents line; study layout names `scene_geometry.py` +
`scene_look.py`; one-scene numbers removed from render-settings and lighting-camera.
Re-read RULES 9 and SKILL.md › Workflow.

## 261013 — Using the skill from Codex
Codex reads the same SKILL.md format from `~/.agents/skills`. A Codex skill import had left a
stale partial copy there (no scripts, old rules). Setup is in `references/pipeline.md` › Install.
Do steps 22–23 only on a machine where Codex is installed (`%USERPROFILE%\.codex` exists).

### 22. Codex sees the live skill
Check: `%USERPROFILE%\.agents\skills\blender-archviz` is a junction to `%USERPROFILE%\.claude\skills\blender-archviz` (`dir %USERPROFILE%\.agents\skills` shows `<JUNCTION>`), or Codex is not installed.
Do: delete the copy that is there, then
`mklink /J "%USERPROFILE%\.agents\skills\blender-archviz" "%USERPROFILE%\.claude\skills\blender-archviz"`.

### 23. Blender MCP in Codex, AGENTS.md per project
Check: `codex mcp list` shows `blender`, and each project used from Codex has an `AGENTS.md` that points at its `CLAUDE.md`, the user `CLAUDE.md` and the project's memory folder; or Codex is not installed.
Do: add `[mcp_servers.blender]` (same command and env as `claude mcp get blender`) to
`~/.codex/config.toml`; write the project's `AGENTS.md` as a map to those sources plus a
Claude→Codex term table (pipeline.md › Install), never a copy of their rules.

## 261013b — Codex reviews, Claude develops, one agent at a time
New RULES 14-16: the writer of skill code runs it but Codex reviews it before a push
(`scripts/codex_review.py`, maintaining.md › Review); Codex only executes workflows done before
and never edits the skill; a machine-wide `%LOCALAPPDATA%\BlenderMCP\AGENT_LOCK` file keeps Blender and study
files to one agent at a time. Re-read RULES.md › Agents.

### 24. Projects carry the lock rule
Check: each project used by both agents has `CLAUDE.md`/`AGENTS.md` lines naming `%LOCALAPPDATA%\BlenderMCP\AGENT_LOCK` (RULES 16) and none naming a project-root `AGENT_LOCK`; or Codex is not installed.
Do: add those lines; replace any project-root lock instruction.

## 261014 — Cross-check, roles as a guide, modular code
Pull-only. RULES 14 now cross-checks all code with the other model (Codex's code reviewed by a
fresh Claude subagent); RULES 15 is a guide (Claude steers, Codex does detail work, either can
take over alone); new RULES 17: modular code and docs, no god scripts. maintaining.md › Review and
› Handing work to Codex. Re-read RULES.md › Agents and RULES 17.

## 261016 — Tile system, Voronoi cracks, final-view rule, Codex handoff
New modules `tile_mapping`, `tile_layout`, `tile_surface`, `tile_damage` (+ controls in `scripts/controls/`):
real-unit tile layout, glazed tile material, and cracks as a noise-warped Voronoi network per tile with
rigid pieces, spalls and a patchy dirt band; damage-only displacement (`tile_surface.use_damage_displacement`).
Chips/edge flakes are work in progress (controls report them as WIP). Controls render on the GPU
(`controls/_scene.black_scene` calls `archviz.use_gpu`). Rules: RULES 8 (keep the final view in sight), RULES 3
(read a source's pictures at full resolution), RULES 15 (reference analysis and Rhino stay with Claude; stop
Codex at a clean point). Docs: materials.md › Tiles, edge-wear.md, api-traps.md, maintaining.md (Codex runs
Blender tests, run budget, same-model review), SKILL.md, helpers.md.

### 25. Local memory for the new rules
Check: the project's memory index has entries for (a) sizing detail features in the final view first, and
(b) lean headless controls (small packed probes, `--only`/`--full`, a run cap in every Codex brief).
Do: add those memory files (feedback type) from RULES 8 and maintaining.md › Handing work to Codex.

### 26. Codex can run Blender tests
Check: Codex is not installed, or the project's memory/AGENTS.md says Codex jobs that run headless Blender
start with `--sandbox danger-full-access` and own a listed set of files while they run.
Do: add that line to the project's `AGENTS.md` term table or memory.

### 27. Tile controls pass here
Check: `blender -b --factory-startup --python scripts/controls/tile_damage_check.py -- --output <study>/_wip/tile_damage_check`
ends with `TILE_DAMAGE_PASS` (chip sections may print `TILE_DAMAGE_SECTION_WIP`), and the layout,
mapping and surface checks print PASS.
Do: if a check fails on this machine, report it to the user before using the tile modules.

### Last. Delete this file
Only after the steps above changed something here: delete MIGRATE.md, commit, pull --rebase, push.
