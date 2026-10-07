# blender-archviz (Claude Code skill)

Photoreal architectural visualization in Blender 5.2 + Cycles, driven from Claude Code through the
Blender Lab MCP, with Rhino as geometry only. `SKILL.md` is the entry point, `RULES.md` the house
rules, `references/` the detail.

## Install on another machine
```
git clone https://github.com/bai-ting-chen/blender-archviz-skill.git %USERPROFILE%\.claude\skills\blender-archviz
```
Update later with `git pull` in that folder.

The skill drives code in the project folder `ARCHVIZ_BLENDER` — its own private repo
github.com/bai-ting-chen/archviz-blender (setup in its README); paths assume `%USERPROFILE%\PROJECT\ARCHVIZ_BLENDER`. Setup of Blender,
the MCP server and add-ons: `references/pipeline.md`.
