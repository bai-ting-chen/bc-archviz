# Work modes — who does what (RULES AGT_02, AGT_03)

The split between Claude and Codex for each stage of a study, in both modes ([study stages](study-stages.md)). RULES AGT_02 holds the
rule; this file is the detail. How to launch the sessions: [skill-maintaining.md](skill-maintaining.md) › Handing work to Codex.

- **Normal mode** (default): Claude plans, researches, models, judges and decides; Codex builds
  from briefs, runs, measures and reviews Claude's code.
- **Codex priority mode, CPM** (Claude's budget is low, the user names it): Claude only directs —
  decisions, direction, taste, briefs, user gates. Codex does every hands-on task. Claude reads
  short documents, not logs ([agent exchange documents](agent-exchange.md)).

While both models work, Claude talks to the user, brings the gates (GAT_01–04) and commits to the
skill repo (RULES AGT_02). When one model works alone, it does all of that itself
([research-loop.md](../research/research-loop.md)).

## What Claude reads in CPM
To keep Claude's tokens for decisions: the top of each report, the review's findings, and the
images it judges (the final camera plus 2–4 native crops beside the ref, or one sheet). Not:
logs, study-script diffs, or long research text beyond the note's recommendation and evidence.
Claude opens a file only when a report leaves a decision unclear. One exception: a proposed skill
change, whose full diff Claude reads before committing it ([stage 16](study-stages.md#stage-by-stage)).

## Switching modes
The user names the mode; it holds until they switch back or the round ends. Before switching,
the agent at work stops at a clean point (a finished stage, the lock released, the report
written). Going back to normal: when Claude's tokens refilled, code made during CPM gets its
Claude review (RULES AGT_01).

## Mode ownership and takeover

Normal is the default until the user selects CPM. Either model can take over alone when the other is out of tokens: stop at a clean point, hand over the brief and project files, never leave context only in agent memory. While both work, Claude directs, brings gates and owns skill commits. In CPM one Codex builder does all labour, with at most one fresh read-only reviewer per stage; disclose same-model review and arrange Claude review after normal mode resumes. The mode ends when the user switches back or the round ends.

## Normal-mode judgement and report detail

Claude owns method/research conclusions, proof renders, reference-image analysis, look judgement and the
shape of the skill. Codex implements scripts from short briefs, gathers sources on request and reports
measurement runs as a numbers table plus one contact sheet. Long output goes to a file with a short
summary returned to the director. The [stage table](study-stages.md#stage-by-stage) gives the CPM exceptions and standalone handover.
