# Study stages — who does what

Who does each stage when Claude and Codex work together. When one model works alone, it does both columns.

## Stage by stage

| Stage | Normal: Claude | Normal: Codex | CPM: Claude | CPM: Codex |
|---|---|---|---|---|
| **1. Brief intake** | reads the request and refs, writes the study goal and open questions in study-notes.md | — | same | — |
| **2. Reference analysis** | picks the refs (Render Reference Library shortlist), reads them at full resolution, names the character to match (RULES MAT_03) | `refmatch.py grid/patches`, measured numbers on request | names what to match from a contact sheet; picks among Codex's shortlist | greps `library.jsonl` to a shortlist, makes the contact sheet, crops and `imgstats` numbers |
| **3. Gather sources** (RULES RES_01) | finds papers, manual, forums, videos; writes the source list | gathers sources into a file on request | — | finds the sources; writes the source list ([format](agent-exchange.md)) |
| **4. Research gate** (GAT_01) | shows the question, source list and gaps; waits; adds the user's links | — | same, from Codex's list; passes the user's links on | adds the user's links to the list |
| **5. Analysis + method** | reads the sources at full resolution, compares 2–4 workflows, chooses, records why | — | reads the research note, chooses, records why | analyses all sources, writes the research note with a ranking in `_wip/research/` |
| **6. Rhino modelling** | models through Rook, File3dm for a user's open file (pipeline.md) | — | briefs what to model and what to leave out | models through Rook, captures views for the gate |
| **7. Model gate** (GAT_02) | shows captures + modelled/left-out list, waits for approval | — | same, from Codex's captures | prepares captures and the list |
| **8. Scene build** (import, UVs, camera, materials, lights) | writes the brief: helpers to reuse, real units, files owned | writes and runs the scripts, syntax-checks, renders the checks | writes the brief | same as normal |
| **9. Camera from a reference** | reads geometry from the ref, judges the overlay | runs `refsolve.py`, `framing_render`, `refmatch.py pair --overlay` | judges the overlay sheet | also takes the readings |
| **10. Material gate** (GAT_03) | shows the schedule, first-pass render, native crops, candidate sheets; waits for approval | renders the first pass, crops and candidate sheets | same, from Codex's sheets; passes the choices on | writes the schedule ([format](agent-exchange.md)), renders the first pass, crops and candidates |
| **11. Proof** (RULES VAL_02, VAL_01) | decides which controls prove the feature | renders controls, writes the numbers table + diff crops | same | same |
| **12. Look round** | tunes only approved materials; judges final camera + native crops vs ref, names the worst defect, sets the next fix | applies the fix, rerenders | same, from the stage report's sheet | same |
| **13. Code review** ([checklist](review-checklist.md)) | reviews Codex's code via a fresh subagent | reviews Claude's code | none; reads only the review's findings summary | a fresh read-only Codex reviewer per stage; the builder weighs the findings |
| **14. Preview + final** (GAT_04) | shows the preview, states resolution/time/noise, launches the final in the open UI | the full-frame test with final settings | shows the preview and asks; tells Codex to launch | full-frame test; launches the UI final (`finals.py`) |
| **15. Study notes** | writes Decisions, findings, open items | appends numbers and traps to its report | writes the Decisions section and the user's choices | writes findings, numbers, traps, open items |
| **16. Skill changes** | edits, `MIGRATE.md`, commits, pushes after Codex's review | reviews | reads Codex's proposed diff, commits and pushes it | drafts the change in the skill folder, uncommitted |
| **17. Close a study** (AST_02) | names the final scene, asks the user for milestone images, runs `study_close.py` | — | names the final scene, asks the user for milestone images | runs `study_close.py`, plan first, then `--apply` |

