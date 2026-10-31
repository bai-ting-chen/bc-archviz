# File ownership (agent lock)
Use when: before working in Blender or Rhino, running a script, or editing a project or study file (RULES AGT_04).

One Blender and MCP port serve every project, so one agent owns them at a time through
`%LOCALAPPDATA%\BlenderMCP\AGENT_LOCK`.

**Step 1. Check.** Absent: step 2. Yours: step 3. Another agent's: stop and tell the user; never take it over.

**Step 2. Take.** Write `<agent> | <Blender, Rhino, script, study or files> | <ISO start time>`; read it back.

**Step 3. Work.** A render left running keeps the lock until it ends.

**Step 4. Release.** Finish or revert half-written work, then delete the lock.

A lock from a Codex builder you directed and stopped is yours: once its process is gone, delete it and tell the user.
