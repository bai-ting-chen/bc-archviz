# Maintaining this skill

Read this before changing, pulling or pushing the skill. One person keeps it in sync across
several machines through GitHub (`github.com/bai-ting-chen/blender-archviz-skill`). Git carries
the files but not what each machine has to do about them, so every push also has to leave
instructions behind.

## What may go in (RULES 0, 0a)
- **Methods, constants, traps, taste and scene-independent code.** Test any number with "would
  it be the same in a different scene?". If not, it is a result and belongs in that project's
  study notes. Physical constants, conventions and procedures belong here.
- **Never anything from a project:** no project files, study scripts, scenes, renders, and no
  names that point at one (project folder names, project repos, study folder names (`<yymmdd>_<topic>`),
  client or site names). Lessons from a study go in stripped of where they came from. Say "a
  pool soffit rendered cyan from the bounce" and leave out which study it was.
- **Paths stay portable:** `~`, `%LOCALAPPDATA%`, or the current project found by
  `archviz.project_root()`, never a user folder or a fixed project path. A machine-specific
  resource such as the Render Reference Library gets a default location plus "ask if missing".
- Code goes into `scripts/` only once it runs on a scene it was not written for.
- **State each rule once, in `RULES.md`.** SKILL.md and the references carry only the how-to
  (commands, functions, numbers) and a pointer such as "(RULES 10c)". A rule repeated in several
  files drifts apart the first time it changes.

## Before editing
1. `git pull` in the skill folder. Other machines push too, and editing a stale copy means a
   merge later or, worse, a force-push that deletes their work. Never force-push over commits
   you have not seen. If you rewrite history, `git fetch` first and check `main..origin/main`.
2. Identity, set once per clone and not globally (work machines hold other repos):
   `git config user.name bai-ting-chen`, `git config user.email baitingchen.arch@gmail.com`.

## Every push leaves a MIGRATE.md
In the same commit as the change, add or extend `MIGRATE.md` in the skill root. It tells the
other machines what to do after they pull. `SKILL.md` has a permanent line telling Claude to run
it first whenever it exists.

- **Cover:** machine setup (installs, versions, the MCP server, env vars), project-folder layout,
  moved or renamed scripts and how projects import them, and new rules or habits that local
  memory or project `CLAUDE.md` files should pick up.
- **Pull-only updates still get a section,** one line long, listing the rules or references that
  changed so the other machine reads them.
- **One dated section per update:** `## yymmdd — <topic>`. If a previous `MIGRATE.md` is still
  there (another machine hasn't run it yet), append a section and never overwrite it.
- **Each step is a Check and a Do.** Write the Check so it is already true on the machine that
  wrote it. That is the guard: a machine where every Check passes, the author included, leaves
  the file alone.
- **The machine that actually carries out the steps** deletes `MIGRATE.md` (only that file; the
  pointer line in `SKILL.md` stays), commits as `bai-ting-chen`, runs `git pull --rebase`, then
  pushes. Finally it tells the user anything that needs a restart, such as MCP changes.

Template:

```markdown
# MIGRATE — run before anything else, then delete

## yymmdd — <topic>
<one paragraph: what changed and why>

### 1. <step>
Check: <command or condition that is true once done>
Do: <what to run or edit>

### Last. Delete this file
Only after the steps above changed something here: delete MIGRATE.md, commit, pull --rebase, push.
```

## Helpers changed?
Run `python scripts/helper_index.py` (MCP venv python) so `references/helpers.md` matches the
code, and give every new public helper a one-line docstring — that line is its index entry.
Refactoring a helper: prove nothing else moved with `scripts/regress_helpers.py` (dump with the
old and the new code, then compare; its docstring has the steps).
Keep one builder per job (one dielectric, one node-graph builder `study_materials.G`, one
`archviz.read_meta`, `archviz.use_gpu`); extend it rather than writing a second.

## Review (RULES 14)
**Claude's code → Codex.** After committing, before pushing, with the MCP venv python:
`python scripts/codex_review.py --commit <sha>` (`--base origin/main` for everything unpushed,
`--uncommitted` for the working tree). It runs `codex exec` read-only at high reasoning effort
against this file, RULES.md and api-traps.md, and prints the findings.

**Codex's code → a fresh Claude subagent.** Start a general-purpose subagent with only: the task
brief, the complete change (`git show <sha>` once committed; before that `git diff HEAD` plus
the new files listed by `git status --short`), and "review against RULES.md, maintaining.md
and api-traps.md: correctness bugs, rule breaks, docs out of date; findings only, most severe
first, with file:line". Only its verdict enters the main session.

Check each finding against the code before acting, fix what holds in a new commit, and list for
the user what was rejected and why. One model only (out of tokens, or the user asks for a fresh
session of the same model as reviewer): a fresh session reviews, and the user is told the
cross-check was same-model (RULES 14).

## Handing work to Codex (RULES 15)
For detail work, from the project folder:
`codex exec -s workspace-write "<brief>" < NUL > <study>\_wip\codex\<task>.log`
(stdin closed, or it waits). Put the brief in a file when it is longer than a few lines. The
brief names the goal, the helpers to reuse (`helpers.md`), the interface in real units, where
outputs go (the study's `_wip/`) and asks for a report file with a summary of at most 20 lines.
Read the summary, not the log. Codex takes the agent lock (RULES 16) when it drives Blender.
- **Codex runs the headless Blender tests itself:** launch with `--sandbox danger-full-access`
  (the unelevated Windows sandbox cannot spawn Blender) and list in the brief the files it owns;
  the other agent keeps off them until it ends. A fix round resumes the writer's session
  (`codex exec resume <id>`); a review is a new session, read-only.
- **Budget the runs in the brief:** a control that builds its own scene renders on the GPU
  (api-traps), probes are small and packed (several outputs in R/G/B of one render), sections run
  alone (`--only`), slow convergence comparisons sit behind `--full`. Cap: one fail-first run,
  one run per real fix, one final pass; never rerun controls of modules the task did not touch.
- **Codex priority mode (RULES 15a):**
  - **Builder:** one `--sandbox danger-full-access` session per stage, owning the stage's files.
    Each stage ends with a commit-sized change and a report in `_wip/codex/`.
  - **Reviewer:** `codex exec -s read-only` started as soon as a stage report lands, while the
    builder goes on with the next stage on other files.
    - Its brief holds only: the stage brief, the diff (or the list of changed files), and "review
      against RULES.md, api-traps.md and the brief: correctness bugs, rule breaks, wrong units;
      findings only, most severe first, file:line".
    - Output: `_wip/codex/review_<stage>.md`.
  - The next builder stage starts by weighing that review and fixing what holds.
  - Claude reads only the reports and reviews, and steers by writing the next brief.
  - At most two Codex sessions at once (builder + reviewer). Plan usage limits are small, so keep
    briefs lean.
- **Codex low on tokens:** stop it between steps and take over (RULES 15) rather than let it die
  mid-edit; its report and the brief are the handover.

## Commit and push
Commit messages say what changed and why. End them with the session's attribution line, if
there is one. Push only the skill. Project folders stay local and never get a remote.
