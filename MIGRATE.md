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

### Last. Delete this file
Only after the steps above changed something here: delete MIGRATE.md, commit, pull --rebase, push.
