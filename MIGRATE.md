# MIGRATE: forward-only, self-contained skill; study closure rebuilt

## What changed
- RULES GOV_01: the skill serves new studies only; every existing study counts as finished. New files and folders
  are kebab-case (AST_05); new studies are `studies/<yymmdd>-<topic>/` with `study-notes.md`.
- RULES GOV_02: the skill is self-contained. It runs with an empty CLAUDE.md and memory; machine files may name the
  skill but never its files or sections.
- `study_close.py` rebuilt (RULES AST_02, `references/workflow/study-close.md`, renamed from `study-lifecycle.md`):
  deletes an allow-list only; the study stays in place and gets `closed.md`.
- New rules PIP_02, VAL_05, MAT_09 (they were stated only in references before).

## Steps
- In this machine's project CLAUDE.md and memory files, remove pointers into the skill's files or sections and any
  copy of a skill rule; keep "use the bc-archviz skill" and facts about this machine.
- Do not run `study_close.py` on a study created before this change.

## Check after pull
- `python scripts/workflow/structure_check.py` reports 0 problems.

Delete this file after applying it.
