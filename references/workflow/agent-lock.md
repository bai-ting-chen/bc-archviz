# File ownership (agent lock)


## AGT_04 procedure

**One owner at a time for Blender, Rhino, scripts and files.** There is one Blender and one MCP port per
    machine, shared by every project. Before working in Blender or Rhino, running a script, or editing any project or study file, check
    `%LOCALAPPDATA%\BlenderMCP\AGENT_LOCK` (machine-wide, beside the MCP server): absent →
    create it (`<agent> | <what: Blender, Rhino, script, study or files> | <start, ISO time>`), work, delete it
    when done; present and not yours → stop and tell the user, never take it over. A
    render left running keeps the lock until it ends. A lock taken by a Codex builder that you
    directed and stopped is yours: once its process is gone, delete it and tell the user.
