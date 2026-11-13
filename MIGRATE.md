# MIGRATE: forward-only, self-contained skill; study closure rebuilt
From: LAPTOP-25

## What changed
- RULES GOV_01: the skill serves new studies only; every existing study counts as finished. New files and folders
  are kebab-case (AST_05); new studies are `studies/<yymmdd>-<topic>/` with `study-notes.md`.
- RULES GOV_02: the skill is self-contained. It runs with an empty CLAUDE.md and memory; machine files may name the
  skill but never its files or sections.
- `study_close.py` rebuilt (RULES AST_02, `references/workflow/study-close.md`, renamed from `study-lifecycle.md`):
  deletes an allow-list only; the study stays in place and gets `closed.md`.
- New rules PIP_02, VAL_05, MAT_09 (they were stated only in references before).
- Renamed study documents in the references: `loop-log.md`, `brief-/report-/review-<stage>.md`,
  `<topic>-sources.md`, `materials-schedule.md`, `pair-vNN.png`.

## Steps
- Add the kebab-case naming rule to your global `~/.claude/CLAUDE.md` (it does not sync through git).
- In this machine's project CLAUDE.md, AGENTS.md and memory files, remove pointers into the skill's files or sections and any
  copy of a skill rule; keep "use the bc-archviz skill" and facts about this machine.
- Do not run `study_close.py` on a study created before this change.

## Check after pull
- `python scripts/workflow/structure_check.py` reports 0 problems.

# MIGRATE: skill restructure (5ea2e80, 2026-10-26), if this machine has not applied it
From: LAPTOP-25

## What changed
- Scripts and Blender modules moved into topic folders (`scripts/workflow/`, `research/`, `review/`, `scene/`,
  `controls/<topic>/`; modules `core.*`, `scene.io.*`, `scene.lighting.*`, `materials.<family>.*`, `effects.*`,
  `renderer.*`). The full old → new list: `git show c54d5bf:MIGRATE.md`.
- V-Ray is retired; the skill has no V-Ray files.

## Steps
- Delete stale `__pycache__` folders in the skill folder.
- Delete `~/.claude/skills/vray` if it exists.
- Outside the skill (Blender MCP setup, `~/.codex/config.toml`, the `~/.agents/skills/bc-archviz` junction, any
  local script), replace old skill paths and module names using that list. Finished studies need no changes.
- Restart Claude Code so it reloads the skill.

# MIGRATE: forward-only shared rounded edges and crooked crack masks
From: LAPTOP-25

## What changed
- Removed `materials.wood.wood_arrises` / `round_arrises`. All geometry rounding uses `effects.round_edges.round_edges(obj, method='geometry')`.
- The shared scene radius is configured with `effects.round_edges.set_round_radius` before building. Defaults remain 2.5 mm, two segments and a 30-degree edge threshold.
- `effects.cracks.ribbon_masks` is replaced by `effects.crack_ribbon.crooked_ribbon_masks`.
- Also removed: `materials.wood.wood_wear` (import from `wood_damage` / `wood_shading`), `materials.wood.wood_uv.grain_uv`
  (use `archviz.directional_uv`), and the private `_GN`/`_input`/`_math`/`_range`/`_noise`/`_attr` re-exports of `effects.edge_wear`.
- The LuxCore dust bake now stores edge line (R) and dust (G); rebake cached dust PNGs.

## Steps
- Update external imports/callers of the removed names; use the shared layer directly. Do not recreate forwarding shims.

## Check after pull
- `rg "round_arrises|wood_arrises" scripts references` finds no callers or references.
- `python scripts/workflow/structure_check.py` reports 0 problems.

# MIGRATE: explicit edge-wear builders and lean controls
From: LAPTOP-25

## What changed
- `weathered_concrete`: `dirt_band` -> `line_width`, `dirt_amount` -> `line_amount`, `dust_band` -> `dust_width`.
- `edge_dirt_masks` now returns `(line, dust, vertex_join)`; `corner=False/True` becomes `kind='outside'/'corner'`.
  All shared dirt builders use `line_width` / `dust_width` instead of `line_w` / `dust_w`.
- Removed the overloaded `round_edges`: use `round_shader(g, normal, ...)`, `round_geometry(obj, ...)`,
  or `switch_rounding(material, ...)`; the boolean keyword is `rounded_edges` everywhere.
- Removed `effects.crack_path` and `crack_profile`; use `effects.crack_ribbon.crack_polylines(seed)` directly.
- The dirt lab removes `--reference-soffit`, `--cap-control`, `--vertex-before` and their one-off outputs.
  Scene and native board code now live in `controls/effects/edge_lab_common.py`.
- No forwarding shims. The protected edge-wear reference still names the old API; follow this section and
  the regenerated helper index until its owner revises that reference.

## Steps
- Update external callers to the names and return values above; do not replay controls for finished studies.

## Check after pull
- `python scripts/workflow/structure_check.py` reports 0 problems.
- Run `edge_wear_graph_check`, `wood_wear_graph_check`, and the affected helper regressions with local fixtures.

# MIGRATE: variation split into tiling, per-unit and surface marks
From: LAPTOP-25

## What changed
- Removed `effects.variation` and `references/effects/variation.md`. Use `effects.variation_tiling` (`anti_tile`),
  `effects.variation_per_unit_shading` (`unit_key`, `set_unit_keys`, `unit_values`, `random_tone_material`) and
  `effects.variation_surface_marks` (`macro_tone`, `grunge`, `patchy_extent`).
- References: `variation-tiling.md`, `variation-per-unit-shading.md`, `variation-per-unit-geometry.md`,
  `variation-surface-marks.md`. RULES MAT_05 and MAT_06 point to them.

## Steps
- Update external imports and links to the names above; no forwarding shims.

## Check after pull
- `rg "effects\.variation\b|variation\.md" scripts references` finds nothing.
- `python scripts/workflow/structure_check.py` reports 0 problems.

# MIGRATE: bitmap leak stain removed from concrete
From: LAPTOP-25

## What changed
- `concrete_study()` lost `stain`, `stain_mult` and `stain_map`; `weathered_concrete()` lost `stain`. The Megascans
  leak map (`library/local/leakage_tdlbbd1c`) is no longer loaded. Leak streaks come only from `add_leak_field` +
  `add_runoff` (edge-wear.md › Run-off).
- `render_variant.py stain=off` now cuts the run-off `leak streak mask`.

## Steps
- Drop `stain=`, `stain_mult=` and `stain_map=` from external calls to these two builders.

## Check after pull
- `rg "stain_map|stain_mult|stain=(True|False)" scripts` finds nothing.
- `python scripts/workflow/structure_check.py` reports 0 problems.

# MIGRATE: caustic_photons drops two private re-exports
From: LAPTOP-25

## What changed
- `effects.caustics.caustic_photons` no longer re-exports `_stem` and `_load_grid`; import them from
  `effects.caustics.photon_grid`. Headings in `caustics.md` renamed (§1 › Choosing the method, §4 steps 1–4).

## Steps
- Update external imports of the two names; no forwarding shims.

## Check after pull
- `rg "caustic_photons\b.*_(stem|load_grid)|photons\._(stem|load_grid)" scripts` finds nothing.
- `python scripts/workflow/structure_check.py` reports 0 problems.

# MIGRATE: caustics down to two methods; photon bake deleted
From: LAPTOP-25

## What changed
- Caustics use GN wavefront (sun through a water body) or LuxCore (all glass, lamps); MNEE and the photon
  bake are no longer caustics methods. Deleted: `effects.caustics.caustic_photons` and `photon_bake`,
  `photon_geometry`, `photon_grid`, `photon_shading`, `photon_trace` (supersedes the section above).
  MNEE code outside caustics (`glass_of_water_mnee`, `render_variant.py mnee=off`) is unchanged.

## Steps
- Delete stale `__pycache__` in `scripts/blender/effects/caustics/`. External photon-bake callers: render
  the glass in LuxCore instead; no shims.

## Check after pull
- `rg "caustic_photons|photon_(bake|geometry|grid|shading|trace)" scripts references` finds nothing.
- `python scripts/workflow/structure_check.py` reports 0 problems.

# MIGRATE: fab_sheet.py renamed asset_sheet.py
From: LAPTOP-25

## What changed
- `scripts/scene/assets/fab_sheet.py` is now `asset_sheet.py`; it tiles Fab and Maxtree rows.

## Steps
- Point any local note or script that calls `fab_sheet.py` at `asset_sheet.py`; no shim.

## Check after pull
- `rg "fab_sheet" scripts references` finds nothing.
- `python scripts/workflow/structure_check.py` reports 0 problems.

# MIGRATE: work modes moved to the ai-work-modes skill
From: LAPTOP-25

## What changed
- Work modes, briefs and reports, Codex runs, reviews and the machine lock now live in a separate skill,
  `ai-work-modes` (`github.com/bai-ting-chen/ai-work-modes`). bc-archviz keeps the study stages, the study
  documents (`agent-exchange.md`) and the new `references/workflow/review-checklist.md`.
- Removed: `references/workflow/work-modes.md`, `references/workflow/agent-lock.md`, `scripts/workflow/codex_review.py`
  (now `ai-work-modes/scripts/codex_run.py review --checklist references/workflow/review-checklist.md`).
- RULES AGT_01, AGT_02 and AGT_04 are removed: modes, review and the machine lock live only in ai-work-modes.
  bc-archviz installed alone works as Claude only.
- The machine lock moved from `%LOCALAPPDATA%\BlenderMCP\AGENT_LOCK` to `%LOCALAPPDATA%\ai-work-modes\agent-lock.txt`.

## Steps
- Clone the skill: `git clone https://github.com/bai-ting-chen/ai-work-modes "%USERPROFILE%\.claude\skills\ai-work-modes"`,
  then set the per-clone identity (skill-maintaining.md › Before editing).
- Link it for Codex: `mklink /J "%USERPROFILE%\.agents\skills\ai-work-modes" "%USERPROFILE%\.claude\skills\ai-work-modes"`.
- In `~/.codex/AGENTS.md`, add a "Work modes" section that names the ai-work-modes skill (it does not sync through git).
- If `%LOCALAPPDATA%\BlenderMCP\AGENT_LOCK` exists and no agent is working, delete it.
- Delete stale `scripts/workflow/__pycache__/codex_review.*`.

## Check after pull
- `python scripts/workflow/structure_check.py` reports 0 problems.
- `python %USERPROFILE%\.claude\skills\ai-work-modes\scripts\agent_lock.py check` runs.

# MIGRATE: Blender 5.3.0 runtime
From: LAPTOP-25

## What changed
- Blender 5.3.0 is now the skill's version. Setup commands and the default executable in
  `scripts/workflow/study_close.py` target its install directory.
- Another clone can fail to launch Blender from that path or lack the MCP add-on and renderer/import
  extensions in the new version's user directory. Extensions need their own compatibility check.

## Steps
- Install Blender 5.3.0; follow `references/scene/pipeline.md` for the executable path and install command.
- Reinstall the MCP add-on and required extensions there. Check LuxCore separately with
  `references/renderer/luxcore.md` before choosing that engine.
- Update local launcher/MCP executable paths to the installed executable and restart the MCP connection.

## Check after pull
- The executable reports Blender 5.3.0; MCP connects to that instance after the add-on is enabled.
- `python -m compileall -q scripts` passes; `python scripts/workflow/structure_check.py` reports 0 problems.
- `python scripts/workflow/helper_index.py` regenerates the helper index.
- Run every `*_graph_check.py` except `edge_wear` (needs an asset) and `luxcore` (needs its extension),
  and the four cases of `anisotropy_lab.py` (needs `nvidia-smi`), with `-b --factory-startup` and each
  script's own arguments after `--`;
  for LuxCore use its installed extension and verify a small render.

# MIGRATE: dew removed from vegetation
From: LAPTOP-25

## What changed
- `blade_material()` lost its `dew` argument; `DEW_GRASS`, `DEW_BROAD` and `materials.vegetation.blade_dew` are deleted.
- `wet-surfaces.md` now has two sections: §4.1 Wet look, §4.2 Wet extent (the former wet surround and wet wall).

## Steps
- Drop `dew=` from external calls to `blade_material`; no shim. Delete stale `__pycache__` in
  `scripts/blender/materials/vegetation/`.

## Check after pull
- `rg -i "\bdew" scripts references` finds nothing.
- `python scripts/workflow/structure_check.py` reports 0 problems.

# MIGRATE: one clear-glass builder; glass references split
From: LAPTOP-25

## What changed
- `glass_material` is deleted (from `materials.shared.dielectric` and `materials.shared.pbr`). The one builder is
  `materials.glass.glass.clear_glass(name="GLASS", tint=(1, 1, 1), roughness=0.0, ior=1.52)`.
- `clear_glass`: the second positional argument is now `tint`, not `ior`. The default is white (the old
  `glass_material` default was green, (0.92, 0.96, 0.97)) and the default material name is `GLASS`, not `Glass_Clear`.
- The `"glass"` material spec builds through `clear_glass`, so it is white by default.
- References: cast relief and glass block left `glass.md` for `glass-relief.md` and `glass-block.md`; liquid in glass
  moved to `water-attached-film.md` §4.2; caustics.md step 2 is now "Size the relief".

## Steps
- In external calls replace `glass_material(...)` with `clear_glass(...)`; pass `ior=` by keyword; pass `tint=` for
  green glass. No shim. Delete stale `__pycache__` in `scripts/blender/materials/`.

## Check after pull
- `rg "glass_material" scripts references` finds nothing.
- `python scripts/workflow/structure_check.py` reports 0 problems.

# MIGRATE: macro tone reference and helper renamed
From: LAPTOP-25

## What changed
- `references/effects/variation-surface-marks.md` -> `references/effects/variation-macro-tone.md`.
- `scripts/blender/effects/variation_surface_marks.py` -> `scripts/blender/effects/variation_macro_tone.py`.
- Mark extent/strength instructions now belong to `references/effects/surface-wear.md`.
- `patchy_extent` is removed; `surface_wear_extent.patch_extent` owns slow zero-reaching wear patches.
- The old Python module is a thin `macro_tone` / `grunge` re-export marked for removal after callers migrate.

## Steps
- Update external links to the new reference. Import `macro_tone` from `effects.variation_macro_tone`
  and `grunge` from `effects.surface_wear`; stop using the deprecated module.
- Replace external `patchy_extent` calls with `surface_wear_extent.patch_extent` and tune its
  black/white thresholds in the shot; its signature is different and has no coverage parameter.
- Delete stale `__pycache__` under `scripts/blender/effects/` after pulling.

## Check after pull
- Old path/name searches hit only the deprecated re-export and this migration note.
- `variation_lab.py --only marks --check-only` and `surface_wear_graph_check.py` pass headless.
- `python scripts/workflow/structure_check.py` reports 0 problems.

# MIGRATE: wear family organised by mechanism
From: LAPTOP-25

## What changed
- `references/effects/edge-wear.md` and `surface-wear.md` are deprecated pointer files.
  Start at `references/effects/wear/wear.md`. Locations no longer separate edge from face wear.
- Canonical layer name `worn-through` → `chipping`, including `var_surface-chipping` AOV names,
  frame labels and control manifests. The old layer spelling remains an input alias.
- Defaults, scalar settings, switches and graph behaviour are unchanged. Scratch hybrid remains held;
  grunge's 0.20 edge width is unchanged pending a render test.

| Old reference section | New reference under `references/effects/wear/` |
|---|---|
| Edge §4.1–4.2, surface location settings, leak origin | `wear-locations.md` |
| Edge §4.3 | `edge-line.md` |
| Edge §4.4, surface §4.1 | `dirt.md` |
| Edge §4.6, surface §4.3 | `water-marks.md` |
| Edge §4.5, surface §4.4 | `chipping.md` |
| Surface §4.2 | `scratches.md` |
| Edge §4.7 | `cracks.md` |
| Shared assembly, source choice, tiling, loading and strength matching | `wear.md` |

Canonical Python modules moved from `scripts/blender/effects/` into its `wear/` package.
Old modules are thin re-exports marked for removal; update imports in other clones now.

| Old `effects.*` module | New `effects.wear.*` owner |
|---|---|
| `edge_wear` | package assembly API `effects.wear` |
| `surface_wear` | `wear` (`grunge` implementation in `dirt`) |
| `edge_chips`, `surface_wear_chips` | `chipping` (clean `edge_field` in `wear_locations`) |
| `edge_dirt` | `dirt`; line profile in `edge_line`, shared support in `edge_profile` |
| `round_edges`, `surface_wear_extent` | `wear_locations` |
| `runoff`, `surface_wear_deposits` | `water_marks` |
| `cracks`, `edge_cracks`, `crack_ribbon` | same basename inside `wear` |
| `leak_field` | `leak_field` |
| `edge_masks`, `edge_shading` | `mask_views`, `concrete_shading` |
| `wear_nodes` | `nodes` |
| `surface_wear_fields` | `patterns` dispatcher; patterns live in mechanism modules |
| `surface_wear_masks`, `surface_wear_defaults`, `surface_wear_hybrid` | `masks`, `defaults`, `hybrid` (held `scratch_hybrid` in `scratches`) |
| `surface_wear_tiling`, `surface_wear_stamps`, `surface_wear_atlas` | `tiling`, `stamps`, `atlas` |

## Steps
- Change external imports/doc bookmarks to the owners above; change layer keys and requested AOVs
  to `chipping`. Existing finished studies need no changes. Do not edit downloaded assets.
- Delete stale skill `__pycache__` folders. Keep the compatibility re-exports until their removal is announced.

## Check after pull
- `python scripts/workflow/structure_check.py` reports 0 problems.
- `python scripts/workflow/helper_index.py` regenerates the helper index.
- Headless Blender 5.3: `--python-exit-code 1 --python scripts/controls/effects/edge_wear_graph_check.py -- <out.json>`
  with `ARCHVIZ_PROJECT` set to a library containing `concrete_wall_009`.
- Headless Blender 5.3: `--python-exit-code 1 --python scripts/controls/effects/surface_wear_graph_check.py -- --project <project> --out <dir>`.
- Snapshot source graphs with `--python scripts/controls/effects/wear_graph_check.py -- --project <project> --out <json>`;
  add `--baseline <old-json>` to compare every source/switch path. Only the declared layer-label rename is normalised.

# MIGRATE: wood wear merged into the shared chip group
From: LAPTOP-25

## What changed
- Deleted `materials.wood.wood_damage` and `materials.wood.wood_shading`. Everything wood is in `materials.wood.wood`.
- `wood_wear_group(...)` -> `effects.wear.edge_wear_group(**WOOD_CHIPS)`; grain breaks are `GrainBreaks(share, depth_m,
  grain_stretch)` (was `break_share`, `break_depth`, `grain_stretch`). The group socket `Subdivisions` is now `Band Subdivisions`.
- `weathered_wood(inner_tint=, inner_mix=, inner_gain=)` -> `weathered_wood(tint=, mix=, gain=)`; the raw-wood under-layer
  is its own builder, `raw_wood_under(g, color, normal)`.

## Steps
- Update external imports and calls to the names above; no shim. Delete stale `__pycache__` in `scripts/blender/materials/wood/`.

## Check after pull
- `rg "wood_damage|wood_shading|wood_wear_group" scripts references` finds nothing.
- `python scripts/workflow/structure_check.py` reports 0 problems.

# MIGRATE: deprecated wear re-exports removed; one graph-check runner; shared controls path
From: LAPTOP-25

## What changed
- Removal announced and done: the 23 `effects.*` wear re-export modules (`effects.edge_wear`, `effects.surface_wear*`,
  `effects.edge_*`, `effects.runoff`, `effects.round_edges`, `effects.cracks`, `effects.crack_ribbon`, `effects.leak_field`,
  `effects.wear_nodes`) and `effects.variation_surface_marks`. Import from the `effects.wear.*` owners and
  `effects.variation_macro_tone` (tables in the wear section above); `grunge` is `effects.wear.dirt.grunge`.
- `effects.wear.nodes` is deleted: use the `G` methods `g.attr`, `g.noise`, `g.math`, `g.range` (its `frame` is a keyword,
  after `tmin`/`tmax`); `frame_for` moved to `materials.shared.nodes`.
- The 13 one-line `*_graph_check.py` wrappers in `scripts/controls/material/`, `tile/` and `water/` are deleted, and
  `controls/material_graph_cases.py` is now `controls/material_graph_check.py`:
  `--python scripts/controls/material_graph_check.py -- <topic> <out.json>`.
- Controls put their topic folders on `sys.path` through `scripts/controls/_paths.py`.

## Steps
- Update external imports and command lines to the names above; no shims. Delete stale `__pycache__` under
  `scripts/blender/effects/` and `scripts/controls/`, and the empty `scripts/controls/material/` folder.

## Check after pull
- `rg "effects\.(edge_wear|surface_wear|runoff|round_edges|wear_nodes|variation_surface_marks)|effects\.wear\.nodes|material_graph_cases" scripts references` finds nothing.
- `python scripts/workflow/structure_check.py` reports 0 problems.

# MIGRATE: shared map, pixel and node helpers
From: LAPTOP-25

## What changed
- `materials.stone.stone_ramp` is deleted, and `materials.stone.stone` no longer re-exports `_ramp`: use `G.ramp(loc, frame,
  stops, label, interp)`. `G` also gained `mix(...)` and `vmath(...)`; the private `_mix_color`, `_vector` and `_mix`
  helpers in the wear and variation modules are gone.
- New shared helpers: `materials.shared.pbr_maps.box_maps` (BoxUV map block), `materials.shared.map_measure.image_rgb`
  and `srgb_to_linear`, and `surface_wear_lab.surface_region` for the labs.

## Steps
- Update external imports of `_ramp` and the deleted helpers; no shims. Delete stale `__pycache__` in
  `scripts/blender/materials/stone/`.

## Check after pull
- `rg "stone_ramp|_mix_color|import _ramp" scripts references` finds nothing.
- `python scripts/workflow/structure_check.py` reports 0 problems.

# MIGRATE: node builder renamed NodeGraph; descriptive method names
From: LAPTOP-25

## What changed
Supersedes the builder names in the sections above. `materials.shared.nodes` is now `materials.shared.node_graph`.

| Old | New |
|---|---|
| `G` | `NodeGraph` |
| `sock` | `active_socket` |
| `.nt` | `.tree` |
| `.L(a, b)` | `.link(a, b)` (now returns the link) |
| `.n(kind, loc, **props)` | `.node_with_props(...)` |
| `._in(socket, value)` | `.link_or_set(socket, value)` |
| `.img`, `.uv` | `.image_texture`, `.uv_map` |
| `.range`, `.noise`, `.vmath`, `.ramp`, `.combine` | `.map_range`, `.noise_texture`, `.vector_math`, `.color_ramp`, `.combine_xyz` |
| `.attr`, `.store`, `.named` | `.attribute`, `.store_attribute`, `.named_attribute` |

`scripts/controls/_paths.py` is now `scripts/controls/controls_import_paths.py`. Node graphs are unchanged.

## Steps
- Update external imports and calls with the table; no shim. Delete stale `__pycache__` in `scripts/blender/materials/shared/`.

## Check after pull
- `rg "materials\.shared\.nodes|import _paths" scripts references` finds nothing.
- `python scripts/workflow/structure_check.py` reports 0 problems.

# MIGRATE: descriptive file and API names, round A
From: LAPTOP-25

## What changed
Public imports, helper names, constants and CLI spellings now use descriptive names. No compatibility shims remain.
Graph construction, numeric results, parameter names and settings fields are unchanged. The video reference remains
`references/research/learning-from-video.md`, paired with `scripts/research/learning_from_video.py`.

Paths in the table are relative to the skill root. Symbol and flag rows identify their original owner;
apply the file row first to locate its new owner. Re-exported symbols use the same new spelling.

| Kind / original owner | Old | New |
|---|---|---|
| File | `scripts/research/imgstats.py` | `scripts/research/image_statistics.py` |
| File | `scripts/research/refsolve.py` | `scripts/research/reference_camera.py` |
| File | `scripts/research/refmatch.py` | `scripts/research/reference_match.py` |
| File | `scripts/research/refmatch_grid.py` | `scripts/research/reference_grid.py` |
| File | `scripts/research/refmatch_image.py` | `scripts/research/reference_image.py` |
| File | `scripts/research/refmatch_pair.py` | `scripts/research/reference_pair.py` |
| File | `scripts/research/refmatch_patches.py` | `scripts/research/reference_patches.py` |
| File | `scripts/research/yt_learn.py` | `scripts/research/learning_from_video.py` |
| File | `scripts/blender/core/projectpath.py` | `scripts/blender/core/project_paths.py` |
| File | `scripts/blender/scene/io/blend_refs.py` | `scripts/blender/scene/io/blend_references.py` |
| File | `scripts/scene/lighting/ldt2ies.py` | `scripts/scene/lighting/ldt_to_ies.py` |
| File | `scripts/scene/assets/polyhaven_meta.py` | `scripts/scene/assets/polyhaven_metadata.py` |
| File | `scripts/review/regress_helpers.py` | `scripts/review/helper_regression.py` |
| File | `scripts/review/regress_compare.py` | `scripts/review/regression_compare.py` |
| File | `scripts/controls/regression/regress_cases.py` | `scripts/controls/regression/regression_cases.py` |
| File | `scripts/controls/regression/regress_dump.py` | `scripts/controls/regression/regression_dump.py` |
| File | `scripts/controls/regression/regress_graph.py` | `scripts/controls/regression/regression_graph.py` |
| File | `scripts/controls/regression/regress_rig.py` | `scripts/controls/regression/regression_rig.py` |
| File | `scripts/controls/regression/stage_b_files_check.py` | `scripts/controls/regression/render_reference_files_check.py` |
| File | `scripts/controls/regression/stage_b_graph_check.py` | `scripts/controls/regression/scene_renderer_graph_check.py` |
| File | `scripts/controls/regression/stage_b_import_check.py` | `scripts/controls/regression/scene_renderer_import_check.py` |
| File | `scripts/controls/_scene.py` | `scripts/controls/photometric_scene.py` |
| File | `scripts/blender/renderer/render.py` | `scripts/blender/renderer/cycles_render.py` |
| File | `scripts/blender/renderer/luxcore/engine.py` | `scripts/blender/renderer/luxcore/engine_settings.py` |
| File | `scripts/blender/renderer/luxcore/lux_textured.py` | `scripts/blender/renderer/luxcore/textured_material.py` |
| File | `scripts/blender/materials/shared/simple.py` | `scripts/blender/materials/shared/flat_color_materials.py` |
| File | `scripts/blender/materials/shared/map_measure.py` | `scripts/blender/materials/shared/map_measurements.py` |
| File | `scripts/blender/materials/shared/material_spec.py` | `scripts/blender/materials/shared/material_specification.py` |
| File | `scripts/blender/materials/water/build.py` | `scripts/blender/materials/water/falling_film_assembly.py` |
| File | `scripts/blender/materials/water/curtain.py` | `scripts/blender/materials/water/ballistic_sheet.py` |
| File | `scripts/blender/materials/water/film.py` | `scripts/blender/materials/water/falling_film.py` |
| File | `scripts/blender/materials/water/film_build.py` | `scripts/blender/materials/water/film_surfaces.py` |
| File | `scripts/blender/materials/water/foot.py` | `scripts/blender/materials/water/pool_impacts.py` |
| File | `scripts/blender/materials/water/foot_config.py` | `scripts/blender/materials/water/impact_config.py` |
| File | `scripts/blender/materials/water/foot_impacts.py` | `scripts/blender/materials/water/impact_locations.py` |
| File | `scripts/blender/materials/water/foot_crowns.py` | `scripts/blender/materials/water/impact_crowns.py` |
| File | `scripts/blender/materials/water/foot_foam.py` | `scripts/blender/materials/water/impact_foam.py` |
| File | `scripts/blender/materials/water/foot_bubbles.py` | `scripts/blender/materials/water/impact_bubbles.py` |
| File | `scripts/blender/materials/water/foot_splash.py` | `scripts/blender/materials/water/impact_splash.py` |
| File | `scripts/blender/materials/water/foot_drift.py` | `scripts/blender/materials/water/impact_drift.py` |
| File | `scripts/blender/materials/water/mesh.py` | `scripts/blender/materials/water/mesh_builders.py` |
| File | `scripts/blender/materials/water/noise.py` | `scripts/blender/materials/water/seeded_noise.py` |
| File | `scripts/blender/materials/water/shading.py` | `scripts/blender/materials/water/surface_shading.py` |
| File | `scripts/blender/materials/water/motion.py` | `scripts/blender/materials/water/motion_blur.py` |
| File | `scripts/blender/materials/water/wet.py` | `scripts/blender/materials/water/wet_wall_proxy.py` |
| File | `scripts/blender/materials/water/fragments.py` | `scripts/blender/materials/water/film_fragments.py` |
| File | `scripts/blender/materials/water/thin_wall.py` | `scripts/blender/materials/water/thin_wall_material.py` |
| File | `scripts/blender/materials/water/height_image.py` | `scripts/blender/materials/water/ripple_height_image.py` |
| File | `scripts/blender/materials/tile/tile_bsdf.py` | `scripts/blender/materials/tile/tile_shading.py` |
| File | `scripts/blender/effects/caustics/gn_caustics.py` | `scripts/blender/effects/caustics/geometry_node_caustics.py` |
| File | `scripts/blender/scene/environment/scatter_asset.py` | `scripts/blender/scene/environment/scatter_node_asset.py` |
| File | `scripts/blender/effects/wear/atlas.py` | `scripts/blender/effects/wear/decal_atlas.py` |
| File | `scripts/blender/effects/wear/defaults.py` | `scripts/blender/effects/wear/default_sources.py` |
| File | `scripts/blender/effects/wear/hybrid.py` | `scripts/blender/effects/wear/hybrid_sources.py` |
| File | `scripts/blender/effects/wear/masks.py` | `scripts/blender/effects/wear/image_masks.py` |
| File | `scripts/blender/effects/wear/patterns.py` | `scripts/blender/effects/wear/procedural_patterns.py` |
| File | `scripts/blender/effects/wear/stamps.py` | `scripts/blender/effects/wear/decal_stamps.py` |
| File | `scripts/blender/effects/wear/tiling.py` | `scripts/blender/effects/wear/scan_sampling.py` |
| File | `scripts/blender/effects/wear/layers.py` | `scripts/blender/effects/wear/layer_names.py` |
| File | `scripts/blender/materials/water/ripple.py` | `scripts/blender/materials/water/pool_ripples.py` |
| Class: `scripts/blender/materials/water/build.py` | `Setup` | `FallingFilmSetup` |
| Class: `scripts/blender/materials/water/curtain.py` | `Lip` | `LaunchLip` |
| Class: `scripts/blender/materials/water/curtain.py` | `Flow` | `SheetFlow` |
| Class: `scripts/blender/materials/water/foot_config.py` | `FootParams` | `ImpactParams` |
| Class: `scripts/research/refsolve.py` | `Solve` | `ReferenceCameraSolve` |
| Class: `scripts/controls/regression/regress_rig.py` | `Modules` | `LazyModules` |
| Class: `scripts/blender/materials/tile/tile_graph.py` | `_Graph` | `_TileGraph` |
| Public function/method: `scripts/blender/materials/tile/tile_graph.py` | `_Graph.m` | `math` |
| Public function/method: `scripts/blender/materials/tile/damage_graph.py` | `_DamageGraph.m` | `math` |
| Public function/method: `scripts/blender/materials/tile/tile_graph.py` | `_Graph.v` | `vector_math` |
| Public function/method: `scripts/blender/materials/tile/damage_graph.py` | `_DamageGraph.v` | `vector_math` |
| Public function/method: `scripts/blender/materials/tile/tile_graph.py` | `_Graph.xyz` | `combine_xyz` |
| Public function/method: `scripts/blender/materials/tile/damage_graph.py` | `_DamageGraph.xyz` | `combine_xyz` |
| Public function/method: `scripts/blender/materials/tile/tile_graph.py` | `_Graph.rand` | `hash_noise` |
| Public function/method: `scripts/blender/materials/tile/tile_graph.py` | `_Graph.put` | `link_or_set` |
| Public function/method: `scripts/blender/materials/tile/tile_graph.py` | `_Graph.split` | `separate_xyz` |
| Public function/method: `scripts/blender/materials/tile/tile_graph.py` | `_Graph.loc` | `next_location` |
| Public function/method: `scripts/blender/materials/tile/tile_graph.py` | `_Graph.noise` | `noise_texture` |
| Public function/method: `scripts/blender/materials/tile/damage_graph.py` | `_DamageGraph.mad` | `multiply_add` |
| Public function/method: `scripts/blender/materials/tile/damage_graph.py` | `_DamageGraph.knot` | `knot_noise` |
| Public function/method: `scripts/blender/materials/tile/damage_graph.py` | `_DamageGraph.interval` | `interpolate_interval` |
| Public function/method: `scripts/research/refsolve.py` | `Solve.to_f` | `camera_to_facade` |
| Public function/method: `scripts/research/refsolve.py` | `Solve.floor_pt` | `pixel_to_floor` |
| Public function/method: `scripts/research/refsolve.py` | `Solve.pt_at_z` | `pixel_to_height` |
| Public function/method: `scripts/research/refsolve.py` | `Solve.plane_pt` | `pixel_to_facade_plane` |
| Public function/method: `scripts/research/refsolve.py` | `Solve.blender` | `blender_camera_settings` |
| Public function/method: `scripts/research/yt_learn.py` | `learn` | `extract_tutorial` |
| Public function/method: `scripts/research/yt_learn.py` | `clean_vtt` | `clean_caption_cues` |
| Public function/method: `scripts/scene/assets/asset_sheet.py` | `fetch_thumb` | `fetch_thumbnail` |
| Public function/method: `scripts/scene/assets/polyhaven_texture.py` | `fetch_tex` | `fetch_texture` |
| Public function/method: `scripts/controls/regression/regress_graph.py` | `val` | `stable_value` |
| Public function/method: `scripts/controls/regression/regress_graph.py` | `sig` | `node_signature` |
| Public function/method: `scripts/controls/regression/regress_rig.py` | `mods` | `lazy_modules` |
| Public function/method: `scripts/controls/regression/regress_rig.py` | `eval_positions` | `evaluated_positions` |
| Public function/method: `scripts/workflow/helper_index.py` | `sig` | `function_signature` |
| Public function/method: `scripts/blender/scene/environment/leaf_geometry.py` | `leaf_proto` | `leaf_prototype` |
| Public function/method: `scripts/blender/materials/water/noise.py` | `smooth` | `smoothstep` |
| Public function/method: `scripts/blender/materials/water/noise.py` | `clustered` | `clustered_noise` |
| Public function/method: `scripts/blender/materials/water/noise.py` | `unit` | `unit_noise` |
| Public function/method: `scripts/blender/materials/water/motion.py` | `enable` | `enable_motion_blur` |
| Public function/method: `scripts/blender/materials/water/wet.py` | `proxy` | `build_proxy` |
| Public function/method: `scripts/blender/materials/water/height_image.py` | `readback_mm` | `height_range_mm` |
| Public function/method: `scripts/blender/materials/water/curtain.py` | `mean_launch` | `mean_launch_speed_m_s` |
| Public function/method: `scripts/blender/materials/water/curtain.py` | `flux` | `flow_per_width_m2_s` |
| Public function/method: `scripts/blender/materials/water/curtain.py` | `launch` | `launch_speed_m_s` |
| Public function/method: `scripts/blender/materials/water/curtain.py` | `speed` | `fall_speed_m_s` |
| Public function/method: `scripts/blender/materials/water/curtain.py` | `thickness` | `sheet_thickness_m` |
| Public function/method: `scripts/blender/materials/tile/tile_bsdf.py` | `bsdfs` | `surface_shader` |
| Public function/method: `scripts/blender/materials/tile/damage_shading.py` | `damage_bsdfs` | `damage_shaders` |
| Public function/method: `scripts/blender/materials/shared/simple.py` | `simple_material` | `flat_color_material` |
| Public function/method: `scripts/blender/materials/shared/map_measure.py` | `map_mean` | `map_mean_linear_rgb` |
| Public function/method: `scripts/blender/renderer/luxcore/lux_textured.py` | `lux_textured` | `textured_material` |
| Module constant: `scripts/blender/materials/water/curtain.py` | `G` | `GRAVITY_M_S2` |
| Module constant: `scripts/blender/materials/water/motion.py` | `G` | `GRAVITY_M_S2` |
| Module constant: `scripts/blender/effects/variation_macro_tone.py` | `SD1` | `SINGLE_OCTAVE_NOISE_SD` |
| Module constant: `scripts/blender/effects/wear/wear_locations.py` | `ROUND_RADIUS` | `ROUND_RADIUS_M` |
| Module constant: `scripts/blender/materials/shared/pbr_config.py` | `BUMP_DISTANCE` | `BUMP_DISTANCE_M` |
| Module constant: `scripts/research/refmatch_image.py` | `W` | `COMPARISON_WIDTH_PX` |
| Module constant: `scripts/rhino/project_edges.py` | `CREASE` | `CREASE_ANGLE_RAD` |
| Module constant: `scripts/scene/assets/asset_sheet.py` | `TILE_W` | `TILE_WIDTH_PX` |
| Module constant: `scripts/scene/assets/asset_sheet.py` | `TILE_H` | `TILE_HEIGHT_PX` |
| Module constant: `scripts/scene/assets/asset_sheet.py` | `LABEL_H` | `LABEL_HEIGHT_PX` |
| Module constant: `scripts/scene/assets/asset_sheet.py` | `UA` | `REQUEST_HEADERS` |
| Module constant: `scripts/scene/assets/maxtree_search.py` | `UA` | `REQUEST_HEADERS` |
| Module constant: `scripts/scene/assets/polyhaven_config.py` | `UA` | `REQUEST_HEADERS` |
| Module constant: `scripts/scene/assets/maxtree_search.py` | `API` | `CATALOG_API_URL` |
| Module constant: `scripts/scene/assets/polyhaven_config.py` | `API` | `API_BASE_URL` |
| Module constant: `scripts/scene/assets/maxtree_search.py` | `PAGE` | `PAGE_SIZE` |
| Module constant: `scripts/scene/assets/maxtree_search.py` | `SCHEMA` | `CATALOG_SCHEMA_VERSION` |
| Module constant: `scripts/scene/assets/maxtree_search.py` | `VARIANT` | `VARIANT_PATTERN` |
| Module constant: `scripts/scene/assets/maxtree_search.py` | `COMMON` | `COMMON_NAME_PATTERN` |
| Module constant: `scripts/scene/assets/maxtree_search.py` | `SPECIES` | `SPECIES_PATTERN` |
| Module constant: `scripts/scene/assets/maxtree_search.py` | `VOLUME` | `VOLUME_PATTERN` |
| Module constant: `scripts/scene/assets/polyhaven_config.py` | `LIB` | `LIBRARY_DIR` |
| Module constant: `scripts/scene/assets/polyhaven_config.py` | `PROJECT` | `PROJECT_ROOT` |
| Module constant: `scripts/scene/assets/polyhaven_config.py` | `TEX_MAPS` | `TEXTURE_MAP_FORMATS` |
| Module constant: `scripts/scene/assets/fab_fetch.py` | `LOCAL` | `LOCAL_LIBRARY_DIR` |
| Module constant: `scripts/research/yt_learn.py` | `LINKS` | `WINGET_LINKS_DIR` |
| Module constant: `scripts/research/yt_learn.py` | `YTDLP` | `YT_DLP_EXE` |
| Module constant: `scripts/research/yt_learn.py` | `FFMPEG` | `FFMPEG_EXE` |
| Module constant: `scripts/workflow/structure_check.py` | `BS` | `BACKSLASH` |
| Module constant: `scripts/workflow/structure_check.py` | `SKILL` | `SKILL_ROOT` |
| Module constant: `scripts/workflow/helper_index.py` | `HERE` | `WORKFLOW_DIR` |
| Module constant: `scripts/workflow/helper_index.py` | `SRC` | `BLENDER_SCRIPTS_DIR` |
| Module constant: `scripts/workflow/helper_index.py` | `OUT` | `HELPER_REFERENCE_PATH` |
| Module constant: `scripts/controls/lighting/ies_units.py` | `D` | `LIGHT_HEIGHT_M` |
| Module constant: `scripts/controls/lighting/ies_units.py` | `I0` | `TEST_INTENSITY_CD` |
| Module constant: `scripts/controls/lighting/ies_units.py` | `V` | `VERTICAL_ANGLES_DEG` |
| Module constant: `scripts/controls/lighting/ies_units.py` | `H` | `HORIZONTAL_ANGLES_DEG` |
| Module constant: `scripts/controls/lighting/ies_units.py` | `ISO` | `ISOTROPIC_PROFILE_PATH` |
| Module constant: `scripts/controls/lighting/ies_units.py` | `DOWN` | `DOWNWARD_PROFILE_PATH` |
| Module constant: `scripts/controls/lighting/ies_units.py` | `C0` | `C0_PROFILE_PATH` |
| Module constant: `scripts/controls/lighting/ies_units.py` | `C90` | `C90_PROFILE_PATH` |
| Module constant: `scripts/controls/lighting/ies_units.py` | `TMP` | `TEMP_DIR` |
| Module constant: `scripts/controls/lighting/light_units.py` | `D` | `LIGHT_HEIGHT_M` |
| Module constant: `scripts/controls/lighting/light_units.py` | `P` | `LIGHT_POWER_W` |
| Module constant: `scripts/blender/scene/environment/terrain_graph.py` | `BARE_W` | `BARE_SOIL_NOISE_W` |
| Module constant: `scripts/blender/scene/environment/terrain_graph.py` | `BARE` | `BARE_SOIL_NOISE_SETTINGS` |
| Module constant: `scripts/blender/scene/lighting/ies_fixture.py` | `IES_POWER` | `IES_REFERENCE_POWER_W` |
| Module constant: `scripts/blender/renderer/luxcore/engine.py` | `ADDON` | `ADDON_MODULE` |
| Module constant: `scripts/blender/renderer/luxcore/engine.py` | `DEPTH_TOTAL` | `MAX_PATH_BOUNCES` |
| Module constant: `scripts/blender/renderer/luxcore/engine.py` | `DEPTH_DIFFUSE` | `MAX_DIFFUSE_BOUNCES` |
| Module constant: `scripts/blender/renderer/luxcore/engine.py` | `DEPTH_GLOSSY` | `MAX_GLOSSY_BOUNCES` |
| Module constant: `scripts/blender/renderer/luxcore/engine.py` | `DEPTH_SPECULAR` | `MAX_SPECULAR_BOUNCES` |
| Module constant: `scripts/blender/renderer/luxcore/engine.py` | `CLAMP` | `CAMERA_RADIANCE_CLAMP` |
| Module constant: `scripts/blender/scene/io/max_import.py` | `MOD` | `IMPORTER_MODULE` |
| Module constant: `scripts/controls/tile/tile_layout_rig.py` | `OUTS` | `OUTPUT_SOCKET_NAMES` |
| Module constant: `scripts/controls/regression/regress_graph.py` | `SKIP` | `IGNORED_NODE_PROPERTIES` |
| Module constant: `scripts/blender/effects/wear/cracks.py` | `CRACK` | `CRACK_DEFAULTS` |
| Module constant: `scripts/blender/effects/wear/edge_cracks.py` | `EDGE_CRACK` | `EDGE_CRACK_DEFAULTS` |
| Module constant: `scripts/blender/effects/wear/water_marks.py` | `LEAK` | `RUNOFF_DEFAULTS` |
| Module constant: `scripts/blender/materials/vegetation/blade_config.py` | `BLADE` | `BLADE_DEFAULTS` |
| Module constant: `scripts/blender/materials/vegetation/blade_config.py` | `WET` | `WET_BLADE_DEFAULTS` |
| Module constant: `scripts/blender/materials/tile/damage_contract.py` | `PARAMS` | `DAMAGE_INPUT_SOCKETS` |
| Module constant: `scripts/blender/materials/tile/damage_contract.py` | `DEFAULTS` | `DAMAGE_DEFAULT_VALUES` |
| Module constant: `scripts/blender/renderer/render_variant.py` | `KNOWN` | `SUPPORTED_OVERRIDES` |
| Module constant: `scripts/blender/effects/wear/edge_profile.py` | `LINE_WIDTH` | `LINE_WIDTH_M` |
| Module constant: `scripts/blender/effects/wear/edge_profile.py` | `DUST_WIDTH` | `DUST_WIDTH_M` |
| Module constant: `scripts/blender/effects/wear/edge_profile.py` | `AO_REACH` | `AO_REACH_M` |
| Module constant: `scripts/blender/materials/glass/glass_assembly.py` | `N_GLASS` | `GLASS_IOR` |
| Module constant: `scripts/blender/materials/glass/glass_assembly.py` | `N_WATER` | `WATER_IOR` |
| Module constant: `scripts/blender/materials/water/noise.py` | `_X0` | `_DOMAIN_MIN_M` |
| Module constant: `scripts/blender/materials/water/noise.py` | `_X1` | `_DOMAIN_MAX_M` |
| Module constant: `scripts/controls/environment/outdoor_smoke.py` | `C` | `PAD_CENTER_M` |
| Module constant: `scripts/controls/environment/outdoor_smoke.py` | `HALF` | `PAD_HALF_SIZE_M` |
| Module constant: `scripts/controls/lighting/fog_koschmieder.py` | `V` | `VISIBILITY_M` |
| Module constant: `scripts/controls/lighting/fog_koschmieder.py` | `D` | `EMITTER_DISTANCE_M` |
| Module constant: `scripts/controls/tile/tile_damage_rig.py` | `W` | `TILE_WIDTH_M` |
| Module constant: `scripts/controls/tile/tile_damage_rig.py` | `H` | `TILE_HEIGHT_M` |
| Module constant: `scripts/controls/tile/tile_damage_rig.py` | `J` | `JOINT_WIDTH_M` |
| Module constant: `scripts/controls/tile/tile_damage_rig.py` | `PX` | `METRES_PER_PIXEL` |
| Module constant: `scripts/controls/tile/tile_damage_rig.py` | `NT` | `TILE_COUNT` |
| Module constant: `scripts/controls/tile/tile_damage_rig.py` | `GLAZE` | `GLAZE_THICKNESS_M` |
| Module constant: `scripts/controls/tile/tile_damage_rig.py` | `ENGOBE` | `ENGOBE_THICKNESS_M` |
| Module constant: `scripts/controls/tile/tile_layout_rig.py` | `RES` | `RESOLUTION_PX` |
| Module constant: `scripts/controls/tile/tile_layout_rig.py` | `SIZE` | `FRAME_SIZE_M` |
| Module constant: `scripts/scene/assets/fab-search.js` | `FAB_PAGE` | `FAB_PAGE_SIZE` |
| Cli flag: `scripts/workflow/study_run.py` | `--pct` | `--resolution-percent` |
| Cli flag: `scripts/workflow/study_run.py` | `--spp` | `--samples` |
| Cli flag: `scripts/workflow/study_run.py` | `--ref` | `--reference` |
| Cli flag: `scripts/research/edge_overlay.py` | `--w` | `--width-px` |
| Cli flag: `scripts/scene/assets/asset_sheet.py` | `--cols` | `--columns` |
| Cli flag: `scripts/scene/assets/polyhaven_fetch.py` | `--res` | `--resolution` |
| Cli flag: `scripts/research/yt_learn.py` | `--n` | `--max-results` |
| Cli flag: `scripts/research/yt_learn.py` | `--scene` | `--scene-change-threshold` |
| Cli flag: `scripts/research/yt_learn.py` | `--every` | `--frame-interval-s` |
| Cli flag: `scripts/research/yt_learn.py` | `--max-height` | `--max-height-px` |
| Cli flag: `scripts/scene/assets/maxtree_search.py` | `--min-height` | `--min-height-cm` |
| Cli flag: `scripts/scene/assets/maxtree_search.py` | `--max-height` | `--max-height-cm` |
| Cli flag: `scripts/blender/renderer/render_variant.py` | `res=` | `resolution=` |
| Cli flag: `scripts/blender/renderer/render_variant.py` | `disp=` | `displacement=` |
| Cli flag: `scripts/blender/renderer/render_variant.py` | `coll=` | `collection=` |
| Cli flag: `scripts/blender/renderer/render_variant.py` | `woodwear=` | `wood_wear=` |
| Override: `scripts/blender/materials/tile/damage_graph.py` | `_DamageGraph.split` | `_DamageGraph.separate_xyz` |

The vector-separation override follows its renamed base method so its expression cache remains active.
Gravity has one authority: `materials.water.ballistic_sheet.GRAVITY_M_S2`; `motion_blur` imports it.
Short argparse destinations remain internal until the parameter/field round; callers use the new flags above.

## Steps
1. Update external imports, attribute accesses, file paths and command invocations using the table. Do not retain old shims.
2. Clear stale `__pycache__` directories under `scripts/`, especially the renamed module families.
3. Regenerate the helper reference with `python scripts/workflow/helper_index.py`.

## Check after pull
- `python scripts/workflow/structure_check.py` reports 0 problems; `python -m compileall -q scripts` passes.
- In factory-startup headless Blender, run `scripts/controls/material_graph_check.py -- <topic> <output.json>`
  for concrete, glass, ground, luxcore, pbr, stone, vegetation, wood_wear, tile_damage, tile_layout, tile_mapping, tile_nodes and water.
- Run `scripts/controls/effects/edge_wear_graph_check.py -- <output.json>` with `ARCHVIZ_PROJECT=<project>`.
- Run `scripts/controls/effects/surface_wear_graph_check.py` and `wear_graph_check.py` with `-- --project <project> --out <output>`;
  the first output is a directory, the second a JSON file. Run `variation_lab.py -- --only marks --check-only --out <directory>`.
- Dump helpers with `scripts/review/helper_regression.py -- dump <skill>/scripts/blender <project> <output.json>` in Blender;
  compare saved baselines using `python scripts/review/helper_regression.py compare <before.json> <after.json>`.
- Import `scripts/controls/water/water_numeric_check.py` in Blender with `scripts/blender` on `sys.path`,
  then compare the JSON result of `check(Path(<output-directory>))` with the saved numeric baseline.
- Compare graph and numeric outputs exactly. Missing source assets must produce the same errors as the saved baseline.
- Import library and host modules in their Blender/MCP Python environments. Load command/control declarations without running renders.
- Search for the old paths and qualified APIs outside this migration history; no obsolete import or invocation should remain.
  Common words, unrelated local bindings, unchanged fields and third-party interfaces retain their established spellings.

Remove each section after applying it; delete this file when none is left.
