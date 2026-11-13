# Maintaining the skill set

Read this before changing, pulling or pushing the skill. It is kept in sync across several machines
through GitHub (`github.com/bai-ting-chen/bc-archviz`); a push that can break another clone also
leaves it instructions (MIGRATE.md).

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
  files drifts apart the first time it changes. `RULES.md` stays a separate file at the skill root, upper case.
- **Reference layout:** every material and effect reference follows [reference-format.md](reference-format.md)
  (Overview, Layers and node-editor diagram, Code, Instructions and parameters, Troubleshooting).
- **Writing patterns:** other references take the pattern from Anthropic's skill guide that fits their
  job, applied only when the user asks for that file's revision (one file at a time):

  | Pattern | Use when | Write it with | Files |
  |---|---|---|---|
  | Sequential workflow | steps in a fixed order | numbered steps; what each step needs from the one before; a check after each step; how to undo a failed step | pipeline.md, max-import.md, terrain.md, study-close.md, gates.md, §4 of material and effect references |
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
2. If `MIGRATE.md` exists, read it before using the skill. Each section starts with `From: <machine>`
   (`hostname`). Sections from this machine are notes for the others: leave them untouched.
3. Apply each section from another machine: its steps, then its "Check after pull" lines, then
   `python scripts/workflow/structure_check.py` (0 problems).
4. Only if step 3 passes: remove those sections (the whole file when none is left) and commit "Apply MIGRATE: <topic>".
   This commit goes out with the machine's next push; nothing is pushed automatically. If any step fails: keep the
   section, report what failed, change nothing else.

Writing MIGRATE.md (before pushing a change):
- Pull first (above). If MIGRATE.md holds sections the other machine has not applied, add a new section;
  never rewrite or remove an existing one.
- If the change can break another clone (moved, renamed or deleted paths or names; changed setup; new install steps),
  write MIGRATE.md in the same commit:
  `# MIGRATE: <topic>`, then `From: <machine>` (`hostname`), then `## What changed` (only what can break), `## Check after pull` (concrete checks or commands),
  and `## Steps` if an action is needed. The file ends with "Remove each section after applying it; delete this file when none is left."
- Not a change log. If the change cannot break another clone, write nothing.

## Helpers changed?
Run `python scripts/workflow/helper_index.py` (MCP venv python) so [blender-python-helpers.md](../scene/blender-python-helpers.md) matches the
code, and give every new public helper a one-line docstring — that line is its index entry.
Refactoring a helper: prove nothing else moved with `scripts/review/helper_regression.py` (dump with the
old and the new code, then compare; its docstring has the steps).
Keep one builder per job (one dielectric, one socket helper, one node-graph builder `materials.shared.node_graph.NodeGraph`, one
`archviz.read_meta`, `archviz.use_gpu`); extend it rather than writing a second.

## Review
A reviewer of a skill change checks [review-checklist.md](review-checklist.md). A new technique also
needs its control render (VAL_02).

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
