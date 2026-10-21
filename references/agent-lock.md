# Agent lock


## AGT_04 procedure

**One agent at a time on Blender and on a file.** There is one Blender and one MCP port per
    machine, shared by every project. Before driving Blender or editing a study's files, check
    `%LOCALAPPDATA%\BlenderMCP\AGENT_LOCK` (machine-wide, beside the MCP server): absent →
    create it (`<agent> | <what: Blender, study or files> | <start, ISO time>`), work, delete it
    when done; present and not yours → stop and tell the user, never take it over. A
    render left running keeps the lock until it ends. A lock taken by a Codex builder that you
    directed and stopped is yours: once its process is gone, delete it and tell the user.
