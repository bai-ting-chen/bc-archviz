# Machine setup

Use when: setting up a machine, after a Blender upgrade, when a tool will not start, or to look up
where a tool lives and how to call it.

Skill code lives in `~/.claude/skills/bc-archviz`, project data in the current study, and the MCP
server in `%LOCALAPPDATA%\BlenderMCP`.

## MCP tools
`execute_blender_code` (assign a dict to `result`), `get_objects_summary`,
`get_screenshot_of_window_as_image`, `render_viewport_to_path` (writes to
`<tempdir>/blender_mcp/`; copy out), `search_manual_docs`, `get_python_api_docs`. Timeout 300 s.
The bundled 5.x manual and API docs are the authority for generic Blender facts. Anything in a
Blender panel is RNA and scriptable; hand tools (sculpt, knife, gizmos) are not.

In Blender code: `sys.path.insert(0, os.path.expanduser(r"~\.claude\skills\bc-archviz\scripts\blender"))`.
Without the MCP tools loaded (session started elsewhere):
`scripts/workflow/mcp_call.py execute_blender_code --file script.py`; the script assigns a **dict** to `result`.
Only one Blender may hold the MCP port: quit an idle finished-final window first.

## Stack
| Piece | Where |
|---|---|
| Blender | `C:\Program Files\Blender Foundation\Blender 5.3\blender.exe` |
| MCP | server `%LOCALAPPDATA%\BlenderMCP\venv\Scripts\blender-mcp.exe` (user scope, `claude mcp get blender`); add-on `mcp` autostarts on 127.0.0.1:9876 |
| Host python | MCP venv `%LOCALAPPDATA%\BlenderMCP\venv\Scripts\python` (numpy, Pillow) for every host tool in `scripts/research/`, `scripts/scene/`, `scripts/workflow/` |
| Blender helpers | `scripts/blender/` ([blender-python-helpers.md](../scene/blender-python-helpers.md)); `core.archviz` re-exports the everyday ones |
| Caustics renderer | LuxCore via the BlendLuxCore extension ([luxcore.md](../renderer/luxcore.md)) |
| Controls | `scripts/controls/`: rerun after a Blender upgrade (`blender -b --factory-startup --python …`) |
| Maintenance | `helper_index.py`, `structure_check.py`, `study_close.py` in `scripts/workflow/`; `helper_regression.py` in `scripts/review/` |

## Install
- Blender: `winget install --id BlenderFoundation.Blender --version 5.3.0 --exact` (upgrades in
  place; use the portable zip for side-by-side versions). If download.blender.org answers **403**,
  fetch the same MSI from an official mirror, check its SHA256 against
  `winget show --id BlenderFoundation.Blender --version <v> --exact`, then `msiexec /i … /qn`
  elevated (the user accepts the UAC prompt).
- MCP (Blender Lab, projects.blender.org/lab/blender_mcp, Blender ≥ 5.1): `mcp-<v>.zip` = add-on,
  `blender-<v>.mcpb` = server. The site is behind Cloudflare; the Gitea API
  `/api/v1/repos/lab/blender_mcp/...` works with curl.
- Add-ons and extensions install through Blender's own installer into its extension folder:
  `blender -c extension install-file -r user_default --enable <zip>`. Delete the downloaded zip
  afterwards; software is not study output (RULES AST_04).
- Prefs, set headless with `blender -b --python set_prefs.py` ending in `bpy.ops.wm.save_userpref()`:
  `system.use_online_access = True` (required even for localhost), MCP `use_autostart` and port
  9876, Cycles `compute_device_type = OPTIX` + `refresh_devices()`.
- Server: unzip the `.mcpb` into `%LOCALAPPDATA%\BlenderMCP\app`,
  `python -m venv %LOCALAPPDATA%\BlenderMCP\venv`, then `venv\Scripts\pip install app numpy pillow`
  (Python ≥ 3.10). A venv can't be moved; rebuild it.
- Claude Code, user scope: `claude mcp add-json blender
  '{"type":"stdio","command":"<LOCALAPPDATA>/BlenderMCP/venv/Scripts/blender-mcp.exe","env":{...}}'
  --scope user`; check with `claude mcp get blender`. A project `.mcp.json` named `blender`
  overrides it; don't keep one. Server env: `BLENDER_MCP_HOST/PORT`, `BLENDER_PATH`.
- Codex on the same machine: link the skill into `~/.agents/skills` as a directory junction, so a
  `git pull` updates both agents:
  `mklink /J "%USERPROFILE%\.agents\skills\bc-archviz" "%USERPROFILE%\.claude\skills\bc-archviz"`.
  Register the MCP in `~/.codex/config.toml` as `[mcp_servers.blender]` with the same command and
  an `[mcp_servers.blender.env]` table; check with `codex mcp list`. A project used from Codex gets
  an `AGENTS.md` that only names the skill.

Last full check: Blender 5.3.0 and BlendLuxCore 2.11.1, headless controls and a Cycles final in the
open UI; not yet checked: the Esc cancel path, a LuxCore final in the open UI, `import_3dm`.
