# File ownership (agent lock)
Use when: before working in Blender or Rhino, running a script, or editing any project or study file (RULES AGT_04).

One Blender and one MCP port serve every project on the machine, so one agent at a time owns Blender, Rhino,
scripts and files. The owner holds `%LOCALAPPDATA%\BlenderMCP\AGENT_LOCK` (machine-wide, beside the MCP server).

## Steps
**Step 1. Check.** Read `AGENT_LOCK`.
- Absent: go to step 2.
- Yours: carry on with step 3.
- Present and not yours: stop and tell the user who holds it and since when. Never take it over or delete it.

**Step 2. Take.** Create `AGENT_LOCK` with one line: `<agent> | <what: Blender, Rhino, script, study or files> | <start, ISO time>`.
Check: the file reads back with your line. Another agent's line there means it won the race: back to step 1.

**Step 3. Work.** Hold the lock for the whole task. A render left running keeps the lock until it ends.

**Step 4. Release.** When the task is done, delete `AGENT_LOCK`. Check: the file is gone.
A task stopped half-way: finish or revert the half-written work first, then delete the lock, so the
next owner starts from a clean state.

## A lock left behind by a Codex builder
A lock taken by a Codex builder that you directed and stopped is yours. Once its process is gone, delete the
lock and tell the user. Any other lock stays until its owner or the user removes it.
