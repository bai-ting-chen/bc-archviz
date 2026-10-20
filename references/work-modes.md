# Work modes — who does what (RULES 15, 15a, 15b)

The split between Claude and Codex for each stage of a study, in both modes. RULES 15a holds the
rule; this file is the detail. How to launch the sessions: maintaining.md › Handing work to Codex.

- **Normal mode** (default): Claude plans, researches, models, judges and decides; Codex builds
  from briefs, runs, measures and reviews Claude's code.
- **Codex priority mode, CPM** (Claude's budget is low, the user names it): Claude only directs —
  decisions, direction, taste, briefs, user gates. Codex does every hands-on task. Claude reads
  short documents, not logs (below).

While both models work, Claude talks to the user, brings the gates (3a, 10a, 8e, 10b) and commits to the
skill repo (RULES 15a). When one model works alone, it does all of that itself
(`research-loop.md`).

## Stage by stage

| Stage | Normal: Claude | Normal: Codex | CPM: Claude | CPM: Codex |
|---|---|---|---|---|
| **1. Brief intake** | reads the request and refs, writes the study goal and open questions in STUDY_NOTES | — | same | — |
| **2. Reference analysis** | picks the refs (Render Reference Library shortlist), reads them at full resolution, names the character to match (RULES 8) | `refmatch.py grid/patches`, measured numbers on request | names what to match from a contact sheet; picks among Codex's shortlist | greps `library.jsonl` to a shortlist, makes the contact sheet, crops and `imgstats` numbers |
| **3. Gather sources** (RULES 3) | finds papers, manual, forums, videos; writes the source list | gathers sources into a file on request | — | finds the sources; writes the source list (below) |
| **4. Research gate** (3a) | shows the question, source list and gaps; waits; adds the user's links | — | same, from Codex's list; passes the user's links on | adds the user's links to the list |
| **5. Analysis + method** | reads the sources at full resolution, compares 2–4 workflows, chooses, records why | — | reads the research note, chooses, records why | analyses all sources, writes the research note with a ranking in `_wip/research/` |
| **6. Rhino modelling** | models through Rook, File3dm for a user's open file (pipeline.md) | — | briefs what to model and what to leave out | models through Rook, captures views for the gate |
| **7. Model gate** (10a) | shows captures + modelled/left-out list, waits for approval | — | same, from Codex's captures | prepares captures and the list |
| **8. Scene build** (import, UVs, camera, materials, lights) | writes the brief: helpers to reuse, real units, files owned | writes and runs the scripts, syntax-checks, renders the checks | writes the brief | same as normal |
| **9. Camera from a reference** | reads geometry from the ref, judges the overlay | runs `refsolve.py`, `framing_render`, `refmatch.py pair --overlay` | judges the overlay sheet | also takes the readings |
| **10. Material gate** (8e) | shows the schedule, first-pass render, native crops, candidate sheets; waits for approval | renders the first pass, crops and candidate sheets | same, from Codex's sheets; passes the choices on | writes the schedule (below), renders the first pass, crops and candidates |
| **11. Proof** (RULES 9, 8b) | decides which controls prove the feature | renders controls, writes the numbers table + diff crops | same | same |
| **12. Look round** | tunes only approved materials; judges final camera + native crops vs ref, names the worst defect, sets the next fix | applies the fix, rerenders | same, from the stage report's sheet | same; adds its self-judgement when training is on |
| **13. Code review** (RULES 14) | reviews Codex's code via a fresh subagent | reviews Claude's code (`codex_review.py`) | none; reads only the review's findings summary | a fresh read-only Codex reviewer per stage; the builder weighs the findings |
| **14. Preview + final** (10b) | shows the preview, states resolution/time/noise, launches the final in the open UI | the full-frame test with final settings | shows the preview and asks; tells Codex to launch | full-frame test; launches the UI final (`finals.py`) |
| **15. Study notes** | writes Decisions, findings, open items | appends numbers and traps to its report | writes the Decisions section and the user's choices | writes findings, numbers, traps, open items |
| **16. Skill changes** | edits, MIGRATE.md, commits, pushes after Codex's review | reviews | reads Codex's proposed diff, commits and pushes it | drafts the change in the skill folder, uncommitted |
| **17. Training** (15b) | compares its verdict with Codex's self-judgement, writes lessons | self-judgement at the end of each report | only when the user asks for it in CPM | same |
| **18. Close a study** (10e) | lists the milestones, runs `study_close.py` | — | lists the milestones | runs `study_close.py`, plan first, then `--apply` |

The agent driving Blender holds AGENT_LOCK (RULES 16); in CPM that is the Codex builder.

## Handoff documents
Every stage starts with a brief and ends with a report; files live in the study's `_wip/codex/`.

**Brief** (Claude → Codex, `brief_<stage>.md`, ≤ 40 lines):
- goal in one sentence, and the design intent it serves;
- files Codex owns this stage (others stay untouched);
- helpers to reuse (`helpers.md`) and the interface in real units;
- outputs and where they go; the camera(s) the images use;
- run budget (maintaining.md › Handing work to Codex);
- done when: the check or image that answers the question;
- the report to write, and whether training is on.

A brief for a **user-requested change to an approved state** names that state and the one change,
says "retune nothing else; if something else must change, stop and report", and carries none of
Claude's or the reviewer's other fixes — those go to a later stage. Bundled extras cost rounds:
they change the look the user approved.

**Stage report** (Codex → Claude, `report_<stage>.md`, ≤ 20 lines on top, detail below):
- what was done, files changed;
- one line per image: "this shows X" (codex-coaching.md);
- the deciding numbers, with the control's noise floor;
- open issues and risks, worst first;
- with training on: *Self-judgement* — what still differs from the ref or intent, worst first,
  and the next step with why.

**Source list** (for the research gate, `_wip/research/<topic>_sources.md`):
- the question in one sentence;
- one line per source: what it is, link or path, what it should answer (mechanism, measured
  data, implementation, reference look);
- gaps: what no source covers yet;
- the user's added links, marked as theirs.

**Material schedule** (for the material gate, `_wip/materials_schedule.md`): one row per layer —
material, source (Poly Haven asset id, procedural, own file), real size and direction, target
albedo and roughness, the reference crop it matches, and "in doubt" with the candidate sheet.

**Research note** (Codex → Claude in CPM, `_wip/research/<topic>.md`, after the gate):
- the question; the mechanism with numbers and sources (papers, measured data);
- 2–4 workflows compared on 1–2 criteria, with cost (time, VRAM, cache);
- a recommendation and what it approximates;
- full-resolution evidence: frames or crops saved beside the note, not only text.

**Review** (fresh Codex reviewer, `review_<stage>.md`): findings only, most severe first, with
file:line, against the brief, RULES.md and api-traps.md. With training on, the reviewer also
opens the images and checks them against the design intent (codex-coaching.md › Reviewing).

## What Claude reads in CPM
To keep Claude's tokens for decisions: the top of each report, the review's findings, and the
images it judges (the final camera plus 2–4 native crops beside the ref, or one sheet). Not:
logs, study-script diffs, or long research text beyond the note's recommendation and evidence.
Claude opens a file only when a report leaves a decision unclear. One exception: a proposed skill
change, whose full diff Claude reads before committing it (stage 16).

## Switching modes
The user names the mode; it holds until they switch back or the round ends. Before switching,
the agent at work stops at a clean point (a finished stage, the lock released, the report
written). Going back to normal: when Claude's tokens refilled, code made during CPM gets its
Claude review (RULES 14).
