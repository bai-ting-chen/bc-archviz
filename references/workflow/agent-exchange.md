# Agent exchange documents

Every stage starts with a brief and ends with a report; files live in the study's `_wip/codex/`.

**Brief** (Claude → Codex, `brief_<stage>.md`, ≤ 40 lines):
- goal in one sentence, and the design intent it serves;
- files Codex owns this stage (others stay untouched);
- helpers to reuse ([blender-python-helpers.md](../scene/blender-python-helpers.md)) and the interface in real units;
- outputs and where they go; the camera(s) the images use;
- run budget (skill-maintaining.md › Handing work to Codex);
- done when: the check or image that answers the question;
- the report to write, and whether training is on.

A brief for a **user-requested change to an approved state** names that state and the one change,
says "retune nothing else; if something else must change, stop and report", and carries none of
Claude's or the reviewer's other fixes — those go to a later stage. Bundled extras cost rounds:
they change the look the user approved.

**Checks line.** A resumed builder carries the proof habits of earlier stages (fingerprints, hash,
area and readback audits) into simple stages, and a geometry import then takes three times as long.
For imports, previews and plain look rounds the brief says: "Checks: look at each image, measure
only what the items name; no audits unless something looks wrong." The reviewer (RULES AGT_01) is
skipped only for a stage that leaves no code behind (a preview or render from saved scripts).

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
file:line, against the brief, [RULES.md](../../RULES.md) and [blender-api-traps.md](../scene/blender-api-traps.md). With training on, the reviewer also
opens the images and checks them against the design intent (codex-coaching.md › Reviewing).
