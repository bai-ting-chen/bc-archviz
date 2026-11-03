# Sources
Use when: looking for an asset or a research source, or adding a new one.

A map of every outside input, one row each. Rules stay in [RULES.md](../../RULES.md) and procedures in
the reference each row points to; this file only says where to look. A new source gets a row here
and, once it is used, a procedure in its topic reference.

## Assets
| Source | Gives | Access | Licence / cost | Who downloads | Procedure |
|---|---|---|---|---|---|
| Poly Haven | materials, HDRIs | public API (`polyhaven_fetch.py`) | CC0 | Claude | [pipeline.md](../scene/pipeline.md) › Assets |
| Quixel Megascans (Fab) | materials, 3D models, plants, decals, brushes | built-in browser (`fab-search.js`), RULES AST_06 | user's Fab licence | user | [pipeline.md](../scene/pipeline.md) › Assets |
| Quixel Megaplants (Fab) | procedural trees; Blender only via USD | built-in browser (`fab-search.js`), RULES AST_06 | user's Fab licence | user | [pipeline.md](../scene/pipeline.md) › Assets |
| Maxtree | plant models | not set up: catalog access still to be checked | paid | user | none yet |
| 3ds Max files | models from the user's own libraries | local files | per file | user | [max-import.md](../scene/max-import.md) |
| IES files | measured light distributions | manufacturer sites | per manufacturer | user or Claude | [lighting-camera.md](../scene/lighting-camera.md) |

Material candidates from every asset source go to the user in one list (RULES MAT_10).

## Research
| Source | Gives | Access | Procedure |
|---|---|---|---|
| Render Reference Library | tagged reference images for look decisions | per-machine folder | [reference-library.md](../research/reference-library.md) |
| Blender manual and API docs | Blender facts | Blender MCP doc search | [pipeline.md](../scene/pipeline.md) |
| GitHub | real API usage, known bugs, workarounds | `gh search code/repos/issues` | [research-loop.md](../research/research-loop.md) |
| Papers (arXiv and others), measured data | physics, numbers, methods | web search | [research-loop.md](../research/research-loop.md) |
| Forums | workflows, fixes | web search | [research-loop.md](../research/research-loop.md) |
| YouTube | technique walkthroughs | `yt_learn.py` (captions first) | [learning-from-video.md](../research/learning-from-video.md) |

Research sources are gathered and shown at the research gate before analysis (RULES GAT_01).
