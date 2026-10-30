# Material and effect reference format

Every material and effect reference uses the same five sections, in this order. A section with
nothing to say keeps its heading and says why in one line (e.g. "No code: the layers are node graph only").

## 1. Overview
- What the look is and which approach it takes, in one short paragraph.
- Name the neighbouring reference that covers the other case (attached vs falling water, printed fallback).
- **Use when:** one line, only when the file is easy to confuse with a neighbour.

## 2. Layers and node-editor diagram
- An ASCII box with the **specific** layers (described in this file, marked `§4.x`) and the **generic**
  layers (each in its own reference) with what each one drives.
- A flow block: order of evaluation and the node-editor output each step feeds (carrier → geometry →
  displacement → bump → colour → roughness).
- Assembly bullets only: how the layers combine (RULES MAT_07 layers, MAT_08 geometry fields).

## 3. Code
- Script paths under `scripts/`, the builder and its parameter dataclasses, and the control scene that
  checks the look. Paths stay portable (see skill-maintaining.md).
- No code listings. Only what a user needs to call or run.

## 4. Instructions and parameters, per layer
- One `###` per specific layer, numbered `4.1`, `4.2`, …: bullets with the method, the traps and the
  "why", then one parameter table (parameter | value).
- Table values are starting points. Size them from the shot (RULES MAT_03) and record the final values in
  the study notes (RULES GOV_01).
- Generic layers are not explained here. Close the section with one table:
  Layer | Reference | Note for this material.

## 5. Troubleshooting
- A table: Symptom | Cause | Fix, each fix pointing to the `§4.x` that holds it.
- Then a bullet list of generic problems that show up with this material, linking
  troubleshooting.md.

## Writing rules
- State each rule once, in RULES.md. Cite it as `(RULES MAT_07)`; do not restate it.
- Refer to sections inside the file as `§N.N`; renumber every reference when a section moves.
- No project names, study names or client names (RULES GOV_02).
- No reference loops between skill files (A → B → C → A). Deep nesting is fine. Links run one
  way, toward the file that holds the method or procedure the reader needs next: a router to
  its files, a material to the effect it uses, upstream water to downstream (a falling film links to
  its splash; the splash names the film). The other direction names the file in plain text, as a
  backtick path (`references/...`, checked but not a link) when it sits in another folder. Links to SKILL.md and RULES.md never close a loop (both are read first).
  `scripts/workflow/structure_check.py` reports every loop.
