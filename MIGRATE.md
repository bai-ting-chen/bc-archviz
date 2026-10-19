# MIGRATE — check before work

## 261018 — thin-sheet simulation limits and hybrid boundaries
Generic reference corrections only; no new code, installation, or scene migration.

### 1. Read the inlet and boundary guidance
Check: the operator has read water-features.md “Thin-sheet inlets and hybrid boundaries”,
materials.md's offset-projection note, and the fluid-simulation capability state.
Do: read those sections before planning a sheet-fed simulation or duplicating scan lookups.
Verify the selected FLIP edition's upstream README; public Demo caches contain mesh watermarks.

## 261018 — Closing a study cleans it (RULES 10e)
New `scripts/study_close.py` + `scripts/blender/blend_refs.py`: on close, keep the milestone scenes
listed under `## Milestones` in STUDY_NOTES.md, make them self-contained, delete `_wip/`, other .blend,
unused library files and vendor/cache folders, verify references. Linked-library image paths resolve
from their library .blend. No installs.

### 2. Read RULES 10e
Check: this machine's session has read RULES 10e (or the user says so).
Do: read it; run the tool (plan first) when the user next closes a study.

## 261018 — Two work modes: normal and Codex priority (RULES 15a)
Docs only. RULES 15a names two Claude/Codex modes. In Codex priority mode (Claude low on budget,
the user names it) Codex builds everything and a parallel read-only Codex session reviews it.
How to launch: maintaining.md > Handing work to Codex. No installs.

### 3. Read RULES 15a
Check: this machine's session has read RULES 15a (or the user says so).
Do: read it (it also splits Rhino modelling and research between the modes). Local memories that describe a one-off "Codex does all coding" arrangement can point at it.

### Last. Delete this file only after this machine carried out a required migration
If the checks already pass, leave this file for the other machines. Otherwise follow
references/maintaining.md after carrying out the step.
