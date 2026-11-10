# Sources
Use when: looking for an asset or a research source, or adding a new one.

A map of every outside input, one row each. Rules stay in [RULES.md](../../RULES.md) and procedures in
the reference each row points to; this file only says where to look. A new source gets a row here
and, once it is used, a procedure in its topic reference.

## Assets
| Source | Gives | Access | Licence / cost | Who downloads | Procedure |
|---|---|---|---|---|---|
| Poly Haven | materials, HDRIs | public API (`polyhaven_fetch.py`) | CC0 | agent | [pipeline.md](../scene/pipeline.md) › Assets |
| Quixel Megascans (Fab) | materials, 3D models, plants, decals, brushes | built-in browser (`fab-search.js`, `fab-download.js`) + `fab_fetch.py`, RULES AST_06 | free, Fab Standard License (since Nov 2026) | agent, after the user's picks | [pipeline.md](../scene/pipeline.md) › Assets |
| Quixel Megaplants (Fab) | procedural trees; Blender only via USD | built-in browser (`fab-search.js`, `fab-download.js`) + `fab_fetch.py`, RULES AST_06 | free, Fab Standard License | agent, after the user's picks | [pipeline.md](../scene/pipeline.md) › Assets |
| Maxtree | plant models (single models and volumes) | public Store API (`maxtree_search.py`), RULES AST_06 | paid per model or volume | user | [pipeline.md](../scene/pipeline.md) › Assets |
| 3ds Max files | models from the user's own libraries | local files | per file | user | [max-import.md](../scene/max-import.md) |
| IES files | measured light distributions | manufacturer sites | per manufacturer | user or agent | [lighting-camera.md](../scene/lighting-camera.md) |

Candidate lists: RULES MAT_10. "Agent" is whoever builds in the current work mode ([study-stages.md](study-stages.md)).

## Research
| Source | Gives | Access | Procedure |
|---|---|---|---|
| Render Reference Library | tagged reference images for look decisions | per-machine folder | [reference-library.md](../research/reference-library.md) |
| Blender manual and API docs | Blender facts | Blender MCP doc search | [pipeline.md](../scene/pipeline.md) |
| GitHub | real API usage, known bugs, workarounds | `gh search code/repos/issues` | [research-loop.md](../research/research-loop.md) |
| Papers (arXiv and others), measured data | physics, numbers, methods | web search | [research-loop.md](../research/research-loop.md) |
| Forums | workflows, fixes | web search | [research-loop.md](../research/research-loop.md) |
| YouTube | technique walkthroughs | `yt_learn.py` (captions first) | [learning-from-video.md](../research/learning-from-video.md) |

When to stop for the user: RULES GAT_01.
