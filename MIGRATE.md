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

Remove each section after applying it; delete this file when none is left.
