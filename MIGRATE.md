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

Delete this file after applying it.
