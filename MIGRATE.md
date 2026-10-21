# Outstanding receiving-machine actions

- Pull this restructure into the existing skill clone, then follow the rename steps below.
- Update rule-ID references in active local CLAUDE.md, AGENTS.md and project memory using the map below (remove the map with this step); preserve history and completed studies.
  0→GOV_01, 0a→GOV_02, 1→REN_01, 2→REN_02, 2a→REN_03, 3→RES_01, 3a→RES_02, 4→PIP_01,
  5→LGT_01, 6→MAT_01, 7→RES_03, 8→MAT_02/MAT_03/MAT_04, 8a→LGT_02, 8b→VAL_01, 8c→MAT_05, 8d→MAT_06, 8e→GAT_02,
  9→VAL_02, 10→VAL_03, 10a→GAT_01, 10b→GAT_03, 10c→AST_03, 10d→AST_01/AST_04, 10e→AST_02, 11→VAL_04,
  12→SAF_01, 13→SAF_02, 14→AGT_01, 15→AGT_02, 15a→AGT_02, 15b→AGT_03, 16→AGT_04, 17→GOV_04.
- Delete stale `.pyc` files and `__pycache__` directories inside this skill after pulling.

- Rename the receiving clone folder to `bc-archviz` (keep its `.git` history).
- Recreate `~/.agents/skills/bc-archviz` as a junction to it; remove the old skill junction.
- After the owner renames GitHub, set origin to `https://github.com/bai-ting-chen/bc-archviz.git`; update clone URLs.
- Update active hooks/settings/project maps/memory paths and links; preserve history and completed studies.
- Move evaluation snapshots out of skill discovery; restart Claude Code and Codex/reimport skills.

Remove a line once every machine has done it.

## 2026-10-21: RULES.md format

- Check: `RULES.md` starts with `## House rules` and rules read `**GOV_01 — ...**`. Do: `git pull`; nothing else (format only, rule IDs and wording unchanged).
