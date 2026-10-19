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
Do: read it. Local memories that describe a one-off "Codex does all coding" arrangement can point at it.

## 261018 — RULES 15a revised: Rhino modelling and research per mode
Docs only. Normal mode: Claude does Rhino modelling and the detailed research (online, YouTube) and
summarises it. Codex priority mode: Codex does coding, Rhino modelling and detailed research (notes in
`_wip/research/`); Claude digests the notes, decides and commands Codex.

### 4. Read the revised RULES 15a
Check: this machine's session has read the RULES 15a that assigns Rhino modelling and research per mode.
Do: read RULES 15a and the amended RULES 15 sentence on Rhino modelling.

## 261018 — RULES 15a: CPM = Claude directs, Codex does all labour
Docs only. In Codex priority mode (CPM) Claude takes the user's seat as director (big decisions, direction,
taste, research digest, briefs, user gates); Codex does all hands-on work. Never two Codex builders at once
(the machine-wide AGENT_LOCK stops the second).

### 5. Read RULES 15a (CPM)
Check: this machine's session has read the RULES 15a that names CPM.
Do: read RULES 15a.

### Last. Delete this file only after this machine carried out a required migration
If the checks already pass, leave this file for the other machines. Otherwise follow
references/maintaining.md after carrying out the step.
