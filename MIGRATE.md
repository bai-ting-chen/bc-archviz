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

Remove each section after applying it; delete this file when none is left.
