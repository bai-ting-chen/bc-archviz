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

Remove each section after applying it; delete this file when none is left.
