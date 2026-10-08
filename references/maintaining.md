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

## Commit and push
Commit messages say what changed and why. End them with the session's attribution line, if
there is one. Push only the skill. Project folders stay local and never get a remote.
