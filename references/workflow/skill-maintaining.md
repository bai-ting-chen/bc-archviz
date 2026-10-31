# Maintaining the skill set

Read this before changing, pulling or pushing the skill. One person keeps it in sync across
several machines through GitHub (`github.com/bai-ting-chen/bc-archviz`). Git carries
the files but not what each machine has to do about them, so every push also has to leave
instructions behind.

## What may go in (RULES GOV_01, GOV_02)
- **Methods, constants, traps, taste and scene-independent code.** Test any number with "would
  it be the same in a different scene?". If not, it is a result and belongs in that project's
  study notes. Physical constants (albedo, IOR, lm/W, typical EV100), conventions, procedures and taste belong here. A chip's scene-specific size belongs in the study notes; size it from the shot (MAT_03).
- **Never anything from a project:** no project files, study scripts, scenes, renders, and no
  names that point at one (project folder names, project repos, study folder names (`<yymmdd>-<topic>`),
  client or site names). Lessons from a study go in stripped of where they came from. Say "a
  pool soffit rendered cyan from the bounce" and leave out which study it was.
- **Paths stay portable:** `~`, `%LOCALAPPDATA%`, or the current project found by
  `archviz.project_root()`, never a user folder or a fixed project path. A machine-specific
  resource such as the Render Reference Library gets a default location plus "ask if missing".
- Code goes into `scripts/` only once it runs on a scene it was not written for.
- **No one-time operations** (RULES GOV_01): a folder rename or a single migration stays in chat; a note the other
  machine needs goes in MIGRATE.md.
- **Purpose first, smallest design** (RULES GOV_04): prefer allow-lists to inference; Codex briefs and review
  prompts say "no extra safeguards without a failure scenario".
- **State each rule once, in [RULES.md](../../RULES.md).** [SKILL.md](../../SKILL.md) and the references carry only the how-to
  (commands, functions, numbers) and a pointer such as "(RULES AST_03)". A rule repeated in several
  files drifts apart the first time it changes.
- **Reference layout:** every material and effect reference follows [reference-format.md](reference-format.md)
  (Overview, Layers and node-editor diagram, Code, Instructions and parameters, Troubleshooting).
- **Writing patterns:** other references take the pattern from Anthropic's skill guide that fits their
  job, applied only when the user asks for that file's revision (one file at a time):

  | Pattern | Use when | Write it with | Files |
  |---|---|---|---|
  | Sequential workflow | steps in a fixed order | numbered steps; what each step needs from the one before; a check after each step; how to undo a failed step | pipeline.md, max-import.md, study-close.md, gates.md, §4 of material and effect references |
  | Multi-MCP coordination | one job spans Rhino (Rook), Blender and host tools | one phase per tool; what is handed to the next phase (file, path, names); a check before the next phase; errors handled in one place | pipeline.md (Rhino → Blender) |
  | Iterative refinement | quality improves round by round | measurable criteria first; the check script; the loop (fix, re-render, re-measure); when to stop | validation.md, research-loop.md, the look rounds in pipeline.md |
  | Context-aware selection | same outcome, different method by case | a decision table with its criteria; the fallback; say which was chosen and why | renderer-choice.md, materials/index.md, texture-selection.md, caustics.md §1 |
  | Domain intelligence | knowledge beyond the tools | rules applied before acting; numbers with units and sources; record what was decided | physical-ranges.md, scale.md, lighting-camera.md, blender-api-traps.md |

  Lookup files (blender-python-helpers.md, capabilities.md, troubleshooting.md) keep their own format.

## Before editing
1. `git pull` in the skill folder. Other machines push too, and editing a stale copy means a
   merge later or, worse, a force-push that deletes their work. Never force-push over commits
   you have not seen. If you rewrite history, `git fetch` first and check `main..origin/main`.
2. Identity, set once per clone and not globally (work machines hold other repos):
   `git config user.name bai-ting-chen`, `git config user.email baitingchen.arch@gmail.com`.

## Pull, then MIGRATE.md (every machine)
Pulling (run before any edit, on either machine):
1. `git fetch origin`, then `git pull --ff-only origin main`. Never force. If the pull refuses, stop and report.
2. If `MIGRATE.md` exists in the skill folder, read it before using the skill. Its "Check after pull" lines are the
   caveats (moved paths, renamed names, setup) to verify.
3. Run `python scripts/workflow/structure_check.py` (0 problems) and each check in MIGRATE.md.
4. Only if steps 1-3 pass: `git rm MIGRATE.md` and commit "Apply MIGRATE: <topic>". This commit goes out with the
   machine's next push; nothing is pushed automatically. If any step fails: keep MIGRATE.md, report what failed, change nothing else.

Writing MIGRATE.md (before pushing a change):
- Pull first (above), so no unapplied MIGRATE.md is in place.
- If the change can break another clone (moved, renamed or deleted paths or names; changed setup; new install steps;
  references in memory or CLAUDE.md files), write MIGRATE.md in the same commit:
  `# MIGRATE: <topic>`, then `## What changed` (only what can break), `## Check after pull` (concrete checks or commands),
  and `## Steps` if an action is needed. End it with "Delete this file after applying it."
- Not a change log. If the change cannot break another clone, write nothing.

## Helpers changed?
Run `python scripts/workflow/helper_index.py` (MCP venv python) so [blender-python-helpers.md](../scene/blender-python-helpers.md) matches the
code, and give every new public helper a one-line docstring — that line is its index entry.
Refactoring a helper: prove nothing else moved with `scripts/review/regress_helpers.py` (dump with the
old and the new code, then compare; its docstring has the steps).
Keep one builder per job (one dielectric, one socket helper, one node-graph builder `materials.shared.nodes.G`, one
`archviz.read_meta`, `archviz.use_gpu`); extend it rather than writing a second.

## Review (RULES AGT_01)
**Claude's code → Codex.** After committing, before pushing, with the MCP venv python:
`python scripts/workflow/codex_review.py --commit <sha>` (`--base origin/main` for everything unpushed,
`--uncommitted` for the working tree). It runs `codex exec` read-only at high reasoning effort
against this file, [RULES.md](../../RULES.md) and [blender-api-traps.md](../scene/blender-api-traps.md), and prints the findings.

**Codex's code → a fresh Claude subagent.** Start a general-purpose subagent with only: the task
brief, the complete change (`git show <sha>` once committed; before that `git diff HEAD` plus
the new files listed by `git status --short`), and "review against [RULES.md](../../RULES.md), [skill-maintaining.md](skill-maintaining.md)
and [blender-api-traps.md](../scene/blender-api-traps.md): correctness bugs, rule breaks, docs out of date; findings only, most severe
first, with file:line". Only its verdict enters the main session.

A new technique also needs its control render (VAL_02). Check each finding against the code before acting, fix what holds in a new commit, and list for
the user what was rejected and why. One model only (out of tokens, or the user asks for a fresh
session of the same model as reviewer): a fresh session reviews, and the user is told the
cross-check was same-model (RULES AGT_01).

## Handing work to Codex (RULES AGT_02)
For detail work, from the project folder:
`codex exec -s workspace-write "<brief>" < NUL > <study>\_wip\codex\<task>.log`
(stdin closed, or it waits). Put the brief in a file when it is longer than a few lines. The
brief names the goal, the helpers to reuse ([blender-python-helpers.md](../scene/blender-python-helpers.md)), the interface in real units, where
outputs go (the study's `_wip/`) and asks for a report file with a summary of at most 20 lines.
Read the summary, not the log. Codex takes the agent lock (RULES AGT_04) when it works in Blender, Rhino, scripts or files.
- **Codex runs the headless Blender tests itself:** launch with `--sandbox danger-full-access`
  (the unelevated Windows sandbox cannot spawn Blender) and list in the brief the files it owns;
  the other agent keeps off them until it ends. A fix round resumes the writer's session
  (`codex exec resume <id>`); a review is a new session, read-only.
- **Budget the runs in the brief:** a control that builds its own scene renders on the GPU
  (api-traps), probes are small and packed (several outputs in R/G/B of one render), sections run
  alone (`--only`), slow convergence comparisons sit behind `--full`. Cap: one fail-first run,
  one run per real fix, one final pass; never rerun controls of modules the task did not touch.
- **Codex priority mode, CPM (RULES AGT_02):** who does which stage and the brief/report formats:
  work-modes.md, study-stages.md, [agent-exchange.md](agent-exchange.md).
  - **Builder:** one `--sandbox danger-full-access` session per stage, owning the stage's files.
    Each stage ends with a commit-sized change and a report in `_wip/codex/`.
  - **Reviewer:** `codex exec -s read-only` started as soon as a stage report lands, while the
    builder goes on with the next stage on other files.
    - Its brief holds only: the stage brief, the diff (or the list of changed files), and "review
      against [RULES.md](../../RULES.md), [blender-api-traps.md](../scene/blender-api-traps.md) and the brief: correctness bugs, rule breaks, wrong units;
      findings only, most severe first, file:line".
    - Output: `_wip/codex/review-<stage>.md`.
  - The next builder stage starts by weighing that review and fixing what holds.
  - Claude reads only the reports and reviews, and steers by writing the next brief.
  - Session cap: RULES AGT_02. Plan usage limits are small, so keep briefs lean.
- **Watching and queueing sessions:** a watcher for the plan limit greps the exact error text
  ("hit your usage limit"), not "usage limit" — the brief text echoed in the log contains it. Give
  every launch its own log tag. On Windows, stopping a background shell that queues sessions can
  leave its wait loop alive and start a duplicate builder later: list the surviving processes by
  script name and stop each by PID before relaunching. A lock left by a session that ended stays
  (RULES AGT_04): report it to the user with the check that no process working in Blender, Rhino, scripts or files still runs.
- **Fast tier:** `service_tier = "fast"` in `~/.codex/config.toml` (or `-c service_tier="fast"`
  per run) when the user asks for speed. It uses the plan allowance faster. A run already going
  keeps its tier.
- **Amending a running stage:** if it has written no outputs yet, stop it, clear the lock it took
  (RULES AGT_04: a stopped builder's lock is the director's; check first that no process whose
  command line is `codex exec` with this stage's brief or log tag still runs, and tell the user),
  add the item to the brief and resume with "restart from the amended brief". That is cheaper
  than a second round afterwards.
- **Cut off mid-stage** (plan limit): images and the .blend may be saved with no report. Record
  the state as unreviewed in the study notes, and next time ask for the report from what was saved
  before any new render.
- **Codex low on tokens:** stop it between steps and take over (RULES AGT_02) rather than let it die
  mid-edit; its report and the brief are the handover.

## Commit and push
Commit messages say what changed and why. End them with the session's attribution line, if
there is one. Push only the skill. Project folders stay local and never get a remote.


## Module boundaries (GOV_04)

Canonical packages import their owners, never obsolete flat material modules. Keep one project-root state
in archviz, and one canonical implementation per shared helper. Functions do one thing, take real-unit
arguments and have a one-line docstring, with no hidden global state. Split a module that gathers unrelated
jobs or requires reading the whole file to change one part. Extend by focused functions or modules;
keep one topic per reference and link to shared procedure instead of repeating it.

**Readable code (RULES GOV_04).** The user reviews references, not code, so code must explain itself:
- one statement per line; names that say the role or unit (`throw`, `fall_speed`, `s` along a lip, `o` outward),
  one name per quantity across a package;
- a comment on every constant whose meaning is not obvious (`# m`, `# share of impacts`, why a cap exists);
- long functions split into named steps; section comments in modules with several layers;
- geometry, materials and motion in separate modules; parameters in a dataclass with a docstring and units.

**Refactoring proof (RULES GOV_04).** Before tidying or restructuring, save the control's numeric output as a baseline; after,
the same control must reproduce it exactly (and an image diff at noise level). A difference means the
refactor changed behaviour: find it, do not accept it.
