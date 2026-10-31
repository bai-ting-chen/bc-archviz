# Closing a study
Use when: the user calls a study finished (RULES AST_02). Never close a study on your own judgement.

Closing frees space and marks the study with `closed.md`; the study keeps its name and place.
`scripts/workflow/study_close.py` (MCP venv python) deletes only these; everything else stays:

| Deleted | Why it is safe |
|---|---|
| `_wip/`, after the milestone images move out | process output only (RULES AST_01) |
| root `.blend` files that are not the final scene; every `*.blend1`, `*.3dmbak` | old versions and backups |
| `__pycache__/` | rebuilt on the next run |
| `library/` images the final scene does not use | unused downloads |

## Steps
**Step 1. Final scene.** List the final `.blend` files (study root) under `## Final scene` in `study-notes.md`,
as list items in backticks.

**Step 2. Milestones.** Show the user the `_wip/` boards and previews and ask which are milestones. List their
choice, in order, under `## Milestones` (`_wip/pair-v16.png`); they become `milestones/milestone-1`, `-2`, …
None chosen: leave the heading out.

**Step 3. Plan.** `python scripts/workflow/study_close.py <study>`. It stops if the final scene uses a file that is
missing, outside the study or in `_wip/`: fix that in Blender, rerun. Otherwise it prints the deletions, their
size and unknown folders over 100 MB (kept; delete one only if the user asks).
Check: the deletion list holds only the four kinds in the table, and no `.blend` you mean to keep (one missing
from `## Final scene` is deleted as an old version).

**Step 4. Apply.** Hold AGENT_LOCK (RULES AGT_04), close the final scene in every Blender, then add `--apply`.
If it says the plan changed, rerun step 3. If a delete fails (a locked file), close the program holding it and
rerun `--apply`.
Check: `closed.md` reports 0 broken references.

**Step 5. Records.** The script writes `closed.md` and a pointer line in the notes. Set the study's status in
`studies/README.md` to `closed <yymmdd>`.
