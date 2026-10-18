# Research loop — running studies alone

How one agent (Claude or Codex) runs research, studies and experiments end to end without a human
or a second model in the loop: when the user is away, or the other model is out of tokens
(RULES 15). The rules still hold; this file is the order of work and the decisions you make
yourself. Stop points that stay: the Rhino model gate (RULES 10a) and the final render gate (RULES 10b).
A study built from a scripted test scene (no Rhino) has no model gate.

## The loop (one question at a time)
1. **Question.** Write it in `STUDY_NOTES.md` › Open questions as one testable sentence with a
   measurable answer ("does a FLIP plunge read closer to the refs than the procedural one, at what
   bake cost?"). Take the next one from the study's open items, `capabilities.md` rows marked
   `research` / `test`, or a failure you just saw. One question per loop.
2. **Physics first** (RULES 3): mechanism and numbers from papers or measured data; write each
   number with its source into STUDY_NOTES. Then 2–4 workflows (manual, forums, GitHub
   `gh search code`, video via `yt_learn.py`), pick one by 1–2 criteria, say why.
3. **Plan the proof before the build.** Which control (RULES 9), which images, which number decides
   it, the run budget (lean-run habits: few short headless runs, `--only`, probes packed into one
   render). Write the plan as 5–10 lines in STUDY_NOTES before coding.
4. **Build** small modules in the study (RULES 17). Syntax-check before every Blender run.
5. **Prove**: control render, imgstats numbers, native-resolution crops beside the reference
   (RULES 8b). A number that matches while the image does not is a fail.
6. **Judge as the steering model would**: does it read like the reference at the final camera?
   Name the worst defect in the crop, fix only that, rerun. Stop after 3 rounds without a clear
   gain and record why (a dead end is a result).
7. **Record** in STUDY_NOTES: answer, numbers, renders, traps, cost (time, VRAM, cache size).
   Promote what is scene-independent to the skill (step 9); keep scene results in the study.
8. **Next question** — back to 1. Keep a short log `STUDY/_wip/loop_log.md` (time, question,
   verdict, files) so the user and the other model can catch up in one read.
9. **Skill changes** (maintaining.md): pull first, one topic per reference, `capabilities.md` row
   with its state, `MIGRATE.md` section, commit as `bai-ting-chen`, push. Review per RULES 14; with
   one model available run the review in a fresh session of that model and say it was same-model.

## Decisions you make alone
Method choice, numbers, look tuning, HDRI and texture choice, adding a control, abandoning a dead
end, writing helpers into the skill once they ran on a scene they were not written for. Record
each with one line of why.

## Decisions you never make alone
Final renders (preview gate), approving Rhino geometry, deleting user data or other studies'
files, writes to GitHub other than this skill's repo, paid purchases or sign-ins, and editing a
file another agent holds (AGENT_LOCK, RULES 16).

## Ending a session
Leave the study resumable cold: STUDY_NOTES current, loop_log updated, no half-written module
(finish or revert it), AGENT_LOCK deleted, `studies/README.md` entry updated, a short summary
for the user at the top of the latest report.
