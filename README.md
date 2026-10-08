# blender-archviz (Claude Code skill)

Photoreal architectural visualization in Blender 5.2 + Cycles, driven from Claude Code through the
Blender Lab MCP, with Rhino as geometry only. `SKILL.md` is the entry point, `RULES.md` the house
rules, `references/` the detail.

## Install on another machine
```
git clone https://github.com/bai-ting-chen/blender-archviz-skill.git %USERPROFILE%\.claude\skills\blender-archviz
```
Update later with `git pull` in that folder.

Method and code travel together: `scripts/` holds the helpers run inside Blender
(`scripts/blender/`), in Rhino via Rook (`scripts/rhino/`), headless controls (`scripts/controls/`)
and host tools (measurement, reference matching, asset fetch, MCP client). Run host tools with the
MCP server's venv python, `%LOCALAPPDATA%\BlenderMCP\venv\Scripts\python` (it has numpy + Pillow).

Data and machine setup stay in the project folder `%USERPROFILE%\PROJECT\ARCHVIZ_BLENDER` (private
repo github.com/bai-ting-chen/archviz-blender; override with env `ARCHVIZ_PROJECT`): `library/`,
`studies/`. The Blender MCP server is a per-machine install in `%LOCALAPPDATA%\BlenderMCP\`. Setup of Blender, the MCP server and
add-ons: `references/pipeline.md`.

**Never commit project files, study scripts, scenes or renders here** — only scene-independent
methods and code.
