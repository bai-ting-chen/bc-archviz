# MIGRATE: kebab-case study names

## What changed
- RULES AST_05: new files and folders are lowercase kebab-case, Python files snake_case.
  New studies are `studies/<yymmdd>-<topic>/` with `study-notes.md`. Older studies keep
  `<yymmdd>_<topic>` and `STUDY_NOTES.md`; `_wip/` keeps its name.
- `study_close.py` and `study_milestones.py` read either notes name and stop if a study has both.
- Renamed in the references: `loop-log.md`, `brief-/report-/review-<stage>.md`,
  `<topic>-sources.md`, `materials-schedule.md`, `pair-vNN.png`.

## Check after pull
- Your project's own CLAUDE.md: if it names `studies/<yymmdd>_<topic>/` or `STUDY_NOTES.md` for
  new studies, change them to `<yymmdd>-<topic>` and `study-notes.md` (older studies keep theirs).
- Your global `~/.claude/CLAUDE.md` does not sync through git: add the same naming rule there.
- `python scripts/workflow/structure_check.py` reports 0 problems.

# MIGRATE: study closure deletes known-safe items only; skill is forward-only

## What changed
- RULES GOV_01: the skill is written for new studies only; every existing study counts as finished.
- RULES AST_02 and `study_close.py`: notes list the kept `.blend` under `## Final scene`; `## Milestones` lists
  `_wip/` images (moved to `milestones/milestone-N`). The plan stops if the final scene uses a file that is missing,
  outside the study or in `_wip/`. Deleted: `_wip/`, non-final root `.blend`, `*.blend1`, `*.3dmbak`, `__pycache__/`,
  unused library images. The study stays in place and gets `closed.md`. Older studies (`STUDY_NOTES.md`) are not supported.
- `references/workflow/study-lifecycle.md` is renamed `study-close.md` (RULES GOV_04: a reference shares its script's name).

## Check after pull
- Links to `study-lifecycle.md` in your project CLAUDE.md or memory files point to `study-close.md`.
- Do not run `study_close.py` on a study created before this change; close such a study by hand if the user asks.

Delete this file after applying it.
