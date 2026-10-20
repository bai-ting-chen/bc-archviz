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

## 261019 — RULES 15b: training Codex; references/codex-coaching.md
Docs only. Codex stage reports end with a self-judgement; Claude writes each gap between its verdict and
Codex's as a checkable lesson in references/codex-coaching.md (craft lessons go to topic references).

### 6. Read RULES 15b and codex-coaching.md
Check: this machine's session has read RULES 15b and references/codex-coaching.md.
Do: read both; Codex briefs on this machine tell Codex to read codex-coaching.md before reporting.

## 261019 — RULES 15b: training in normal mode only
Docs only. Codex training (self-judgement + lessons) runs only in normal mode; CPM skips it to save tokens.

### 7. Read RULES 15b (normal mode only)
Check: this machine's session knows training runs only in normal mode.
Do: read RULES 15b.

## 261019 — Work modes spelled out: references/work-modes.md
Docs only. RULES 15a now points to `references/work-modes.md`: a stage-by-stage table of who does
what in normal mode and CPM, the brief / stage report / research note / review formats in
`_wip/codex/`, and what Claude reads in CPM. RULES 15b: training is normal-mode by default, and
runs in CPM too when the user asks.

### 8. Read work-modes.md and the revised RULES 15a/15b
Check: this machine's session has read references/work-modes.md.
Do: read it; Codex briefs on this machine follow its brief and report formats.

## 261019 — Research gate (RULES 3a)
Docs only. A third stop in every study, both modes: after gathering sources and before analysing,
show the question, source list and gaps, and wait for the user's links. Stops are now research
(3a), model (10a), final preview (10b). work-modes.md table renumbered; new source-list format.

### 9. Read RULES 3a
Check: this machine's session has read RULES 3a.
Do: read it and the work-modes.md stages 3–5.

## 261019 — Material gate (RULES 8e)
Docs only. A fourth stop, both modes: after the first build and before any look round, show the
material schedule, a first-pass render at the final camera, native crops and candidate sheets;
wait for approval. Stops: research (3a), model (10a), materials (8e), final preview (10b).

### 10. Read RULES 8e
Check: this machine's session has read RULES 8e.
Do: read it and work-modes.md stage 10 and the material schedule format.

### Last. Delete this file only after this machine carried out a required migration
If the checks already pass, leave this file for the other machines. Otherwise follow
references/maintaining.md after carrying out the step.

## 261020 — board-formed concrete as relief; ballistic curtain; Codex handling
Docs only, no installs. New: materials.md › Concrete "Board-formed concrete is relief, not a print" (three relief
scales, grain source map, tone target vs AgX roll-off, build traps); water-features.md "Free curtain off a lip"
(ballistic carrier, ribbon traps); work-modes.md brief rule for user-requested changes; maintaining.md watching
and queueing Codex sessions; codex-coaching.md five new lessons (contrast, patch stop, mechanism, user-named
asset, whole-frame diff, API lookup); api-traps.md adaptive subdivision lives on the modifier.

### 11. Read the new sections
Check: this machine's session has read the sections listed above.
Do: read them before the next board-formed concrete, water-curtain or Codex-led stage.
