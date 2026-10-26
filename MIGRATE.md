# MIGRATE: skill restructure (commit 5ea2e80)

Changes made on the other machine after its last pull. Apply the steps, then delete this file in your next push
(or the next push from the first machine once you confirm).

## Update safely
1. `git pull --ff-only` in the skill folder (`~/.claude/skills/bc-archviz`). Never force-push or reset to
   replace local work; if the pull refuses, check `git status` first.
2. Delete stale `__pycache__` folders in the skill (`find . -name __pycache__ -type d -prune -exec rm -rf {} +`).
3. Delete `~/.claude/skills/vray` if it exists. V-Ray is retired; the skill no longer has it.
4. Search your local CLAUDE.md files, AGENTS.md, memory and any scripts outside the skill for the old names
   below, and update them. Studies are closed, so none should need changes.
5. Run `python scripts/workflow/structure_check.py` in the skill folder. It must report 0 problems.
6. Restart Claude Code so it reloads the skill.
7. Once steps 1-6 pass, delete this file: `git rm MIGRATE.md`, commit "Apply MIGRATE: skill restructure".
   Push with your next push. Do not push this deletion on its own.

## Moved scripts (paths)
- `scripts/{study_close,study_files,study_milestones,study_prune,study_refs,study_run,codex_review,helper_index,mcp_call}.py` -> `scripts/workflow/`
- `scripts/{refmatch*,refsolve,imgstats,edge_overlay,yt_learn}.py` -> `scripts/research/`
- `scripts/{regress_helpers,regress_compare}.py` -> `scripts/review/`
- `scripts/polyhaven_*.py` -> `scripts/scene/assets/`; `scripts/{ldt*,ies_write,photometry_integral}.py` -> `scripts/scene/lighting/`
- `scripts/controls/*` -> `scripts/controls/{archviz,tile,material,effects,water,lighting,environment,regression}/`;
  shared helpers stay at `scripts/controls/` (`_scene.py`, `graph_dump.py`, `material_graph_cases.py`)

## Moved Blender modules (names to import)
- `archviz` -> `core.archviz` (keep the alias: `import core.archviz as archviz`)
- `assets`, `projectpath`, `uv`, `material_map` -> `core.*`
- `rhino_import`, `max_import`, `blend_refs`, `reference_paths`, `reference_localise` -> `scene.io.*`
  (the last three run with `scripts/blender/scene/io` on the path, as before)
- `lighting`, `photometry`, `camera`, `interior`, `atmosphere`, `ies_*`, `light_fixtures`, `light_objects`, `emitter_shading` -> `scene.lighting.*`
- `terrain*`, `scatter*`, `meadow_*`, `leaf_geometry` -> `scene.environment.*`
- `glassware`, `glass_assembly`, `lathe_geometry`, `tumbler_profiles` -> `materials.glass.*`
- `render`, `render_variant` -> `renderer.*`; `finals`, `final_*`, `from_passes` -> `renderer.finals.*`
- `caustic_*`, `gn_caustics`, `photon_*` -> `effects.caustics.*`
- Materials: `materials.X` -> `materials.<family>.X` (families: tile, wood, concrete, glass, stone, ground,
  vegetation, metal, fabric, displacement, shared, water). Examples: `materials.tile_surface` -> `materials.tile.tile_surface`,
  `materials.pbr` -> `materials.shared.pbr`, `materials.luxcore` -> `renderer.luxcore.luxcore`
- Effects: `materials.edge_wear`, `materials.runoff`, `materials.cracks`, `materials.leak_field`, `materials.variation`, `materials.wear_nodes` -> `effects.*`
- The old `water` package -> `materials.water` (for example `water.film` -> `materials.water.film`)

## V-Ray removed
- `max_import.rebuild_materials` and `max_import.slot_maps` are gone (they rebuilt V-Ray materials).
  The 3ds Max repair (`load`, `tidy`, `open_loops`, `origin_to_root`) stays.

## Reference folders
- `references/materials/`: `tiles.md` -> `tile/tiles.md`; `wood.md` -> `wood/wood.md`; `concrete.md` and
  `board-formed-concrete.md` -> `concrete/`; `glass.md` -> `glass/glass.md`; `stone.md`, `ground.md`, `metal.md`,
  `fabric.md`, `vegetation.md`, `displacement.md` -> their family folders.
  `index.md`, `physical-ranges.md`, `scale.md`, `texture-selection.md` and `water/` stay.
- Links between the files were updated. SKILL.md has the repository map.
