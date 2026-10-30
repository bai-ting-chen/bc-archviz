# Research loop — running studies alone

How one agent (Claude or Codex) runs research, studies and experiments end to end without a human
or a second model in the loop: when the user is away, or the other model is out of tokens
(RULES AGT_02). The rules still hold; this file is the order of work and the decisions you make
yourself. Stop points that stay: the research gate (RULES GAT_01), the Rhino model gate (RULES GAT_02), the
material gate (RULES GAT_03) and the final render gate (RULES GAT_04).
A study built from a scripted test scene (no Rhino) has no model gate.

## The loop (one question at a time)
1. **Question.** Write it in `study-notes.md` › Open questions as one testable sentence with a
   measurable answer ("does a FLIP plunge read closer to the refs than the procedural one, at what
   bake cost?"). Take the next one from the study's open items, [capabilities.md](../scene/capabilities.md) rows marked
   `research` / `test`, or a failure you just saw. One question per loop.
2. **Physics first** (RULES RES_01): mechanism and numbers from papers or measured data; write each
   number with its source into study-notes.md. Gather the sources first and stop at the research
   gate (RULES GAT_01) before analysing them. Then 2–4 workflows (manual, forums, GitHub
   `gh search code`, video via `yt_learn.py`), pick one by 1–2 criteria, say why.
3. **Plan the proof before the build.** Which control (RULES VAL_02), which images, which number decides
   it, the run budget (lean-run habits: few short headless runs, `--only`, probes packed into one
   render). Write the plan as 5–10 lines in study-notes.md before coding.
4. **Build** small modules in the study (RULES GOV_04). Syntax-check before every Blender run.
5. **Prove**: control render, imgstats numbers, native-resolution crops beside the reference
   (RULES VAL_01). A number that matches while the image does not is a fail.
6. **Judge as the steering model would**: does it read like the reference at the final camera?
   Name the worst defect in the crop, fix only that, rerun. Stop after 3 rounds without a clear
   gain and record why (a dead end is a result).
7. **Record** in study-notes.md: answer, numbers, renders, traps, cost (time, VRAM, cache size).
   Promote what is scene-independent to the skill (step 9); keep scene results in the study.
8. **Next question** — back to 1. Keep a short log `STUDY/_wip/loop_log.md` (time, question,
   verdict, files) so the user and the other model can catch up in one read.
9. **Skill changes** (skill-maintaining.md): pull first, one topic per reference, [capabilities.md](../scene/capabilities.md) row
   with its state, `MIGRATE.md` action if a receiving machine must act, commit as `bai-ting-chen`, push. Review per RULES AGT_01; with
   one model available run the review in a fresh session of that model and say it was same-model.

## Decisions you make alone
Method choice, numbers, look tuning, HDRI and texture choice, adding a control, abandoning a dead
end, writing helpers into the skill once they ran on a scene they were not written for. Record
each with one line of why.

## Decisions you never make alone
Closing the research or material gate, final renders (preview gate), approving Rhino geometry, deleting user data or other studies'
files, writes to GitHub other than this skill's repo, paid purchases or sign-ins, and working in
Blender, Rhino, scripts or files another agent holds (AGENT_LOCK, RULES AGT_04).

## Ending a session
Leave the study resumable cold: study-notes.md current, loop_log updated, no half-written module
(finish or revert it), AGENT_LOCK deleted, `studies/README.md` entry updated, a short summary
for the user at the top of the latest report.


## RES_01 procedure

**Research before anything new — from the physics down, not from tutorials up.** Order:
   (a) the mechanism: optics/physics papers, measured data, the governing equations (why does wet
   concrete darken? Lekner–Dorf: internal reflection in the water film, non-linear in albedo);
   (b) how others implement it: manual/API, forums, papers' renderers, YouTube (`yt_learn.py`);
   (c) map the model onto native nodes and say which terms are kept and which approximated.
   Compare 2–4 workflows, choose by REN_01/REN_02, cite sources, then build and prove. Read a source's own
   pictures and video frames at full resolution, not a summary of its text: the method is often
   only in the images, and a near-copy built from the summary misses it. More and more
   requests will be things few people have done in Blender or archviz: a
   tutorial can only copy a look, the science lets you build a new method and know its limits.
   Videos are evidence, not authority.
