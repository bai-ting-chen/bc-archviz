# MIGRATE — run before anything else, then delete

## 261008 — machine layout: MCP to LocalAppData, local-only projects, git identity

The skill changed how a machine is laid out. Bring this machine in line, then remove this file.
Work through the steps in order; each one checks before it changes anything. Report to the user
what was done at the end.

**Guard.** First run the *Check* of every step. If all checks already pass, this machine was
migrated earlier: do nothing, and **do not delete this file** (another machine may still need it).
Delete it (step 9) only after you migrated a machine that needed it.

### Target layout
- **Skill** (`~/.claude/skills/blender-archviz`): method and all code (`scripts/`). The only thing
  pushed to GitHub. Never names a specific project or study.
- **Project folders**: data only (`library/`, `studies/`, scenes, renders). Local to the machine,
  no GitHub remote, never pushed. No `tools/`, no `.mcp.json`.
- **Blender MCP server**: per-machine install in `%LOCALAPPDATA%\BlenderMCP\` (`app\` source,
  `venv\`), like Rook in `%LOCALAPPDATA%\Rook\`, registered in Claude Code at **user** scope.
- **Git identity** for the skill repo: `bai-ting-chen <baitingchen.arch@gmail.com>`, set in the
  clone (not globally).

### 1. Skill clone
Check: `git -C ~/.claude/skills/blender-archviz config user.email` is `baitingchen.arch@gmail.com`.
Do: `git config user.name bai-ting-chen` and `git config user.email baitingchen.arch@gmail.com` in
that clone; `git pull`.

### 2. Find the old project folder(s)
Look under `%USERPROFILE%\PROJECT\` for folders holding `tools\blender-mcp-server\` or a
`.mcp.json` with a `blender` server. Each one found goes through steps 4-7. Read the old
`.mcp.json` first: its `env` (host, port, `BLENDER_PATH`) is reused in step 3.

### 3. MCP server in %LOCALAPPDATA%\BlenderMCP
Check: `claude mcp get blender` says *User config* and the command is
`…\AppData\Local\BlenderMCP\venv\Scripts\blender-mcp.exe`.
Do:
1. Source: copy `blmcp\`, `pyproject.toml`, `requirements.txt`, `manifest.json`, `README.md`,
   `blender_icon.png` from the old `tools\blender-mcp-server\` into `%LOCALAPPDATA%\BlenderMCP\app\`
   (no `build\`, `*.egg-info`, `__pycache__`). If there is no old copy, download the server
   `.mcpb` per `references/pipeline.md` and unzip it there.
2. Python: the one in the old venv's `pyvenv.cfg` (`home =`), else any Python ≥ 3.10.
   `python -m venv %LOCALAPPDATA%\BlenderMCP\venv`, then
   `venv\Scripts\python -m pip install <app> numpy pillow` (match the old venv's `mcp` version
   from its `pip freeze` if it had one). A venv can't be moved — always rebuild.
3. Register: `claude mcp add-json blender '{"type":"stdio","command":"<LOCALAPPDATA>/BlenderMCP/venv/Scripts/blender-mcp.exe","args":[],"env":{<old env>}}' --scope user`.
4. Smoke test: `venv\Scripts\python <skill>\scripts\imgstats.py stats <any png>`; and
   `scripts\mcp_call.py execute_blender_code --file <ping.py>`. If Blender is closed, that test
   ends with "Cannot connect to Blender at localhost:9876", which is fine because the server started.

### 4. Remove the project's MCP config
Check: no `.mcp.json` in the project; `.claude\settings.local.json` has no `enabledMcpjsonServers`.
Do: delete `.mcp.json` (it overrides the user-scope server); remove `enabledMcpjsonServers` from
`.claude\settings.local.json` (delete the file if it becomes empty). `claude mcp get blender`
must now say *User config*.

### 5. Delete the project's tools/
Check: no `tools\` in the project.
Do:
1. Any `.py` under `tools\` (outside `blender-mcp-server`) that is not identical to its copy in
   the skill's `scripts\` (compare with CR stripped) → show the user the diff and ask before
   going on; it may hold work that belongs in the skill (scene-independent only, RULES 0).
2. Stop processes running from it: in PowerShell, `Get-CimInstance Win32_Process` where
   `ExecutablePath` is under the project's `tools\` → `Stop-Process`. This is the old MCP server;
   Blender tools in the current session drop until restart.
3. Delete `tools\` entirely (old code, old server venv, installers — all replaced).

### 6. Project leaves GitHub
Check: `git -C <project> remote -v` prints nothing.
Do: `git remote remove origin`. (The GitHub repo `archviz-blender` was already deleted.) Never
add a remote to a project again.

### 7. Project docs
Rewrite the project's `CLAUDE.md` / `README.md` so they say: data only (`library/`, `studies/`);
all code is in the skill's `scripts/`; the MCP server is in `%LOCALAPPDATA%\BlenderMCP\` at user
scope; the project is local and never pushed. Drop rows for `tools/` and `.mcp.json`, and drop
`tools/blender-mcp-server/` from `.gitignore`. Commit locally only if the project is a git repo.
Do not touch old study scripts — finished studies are not revisited.

### 8. Memory on this machine
In this project's Claude memory folder, record the following, each as its own memory file with a
pointer added to `MEMORY.md`. Skip any that already exist.
- *Skill vs project* (feedback): only the skill is pushed; project folders stay local; the skill
  never names a specific project, project path, repo or dated study.
- *Git identity* (user): skill commits as `bai-ting-chen <baitingchen.arch@gmail.com>`, per clone;
  `git fetch` before any force-push, because other machines push too.
- *Blender MCP location* (project): `%LOCALAPPDATA%\BlenderMCP` at user scope since 2026-10-08.
- *Migrate file* (feedback): every skill push adds or extends `MIGRATE.md` for the other machines (SKILL.md).

### 9. Delete this file
Only after steps 1-8 actually changed something on this machine:
1. Delete `MIGRATE.md` (the pointer line in `SKILL.md` stays: it is permanent).
2. Commit as `bai-ting-chen` with a message such as "Machine migration done; remove MIGRATE.md".
3. `git pull --rebase`, then `git push`.

Last, tell the user to restart Claude Code so the user-scope Blender server loads.
