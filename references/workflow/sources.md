# Sources
Use when: looking for an asset or a research source, downloading an asset, or adding a new source.

Where every outside input comes from, one row each. A new source gets a row here and, once used, a
procedure in its topic reference.

## Assets
| Source | Gives | Access | Licence / cost | Who downloads | Procedure |
|---|---|---|---|---|---|
| Poly Haven | materials, HDRIs | public API (`polyhaven_fetch.py`) | CC0 | agent | *Poly Haven* below |
| Quixel Megascans (Fab) | materials, 3D models, plants, decals, brushes | built-in browser pane (`fab-search.js`, `fab-download.js`) + `fab_fetch.py`, RULES AST_04 | free, Fab Standard License (since Nov 2026) | agent, after the user's picks | *Quixel on Fab* below |
| Quixel Megaplants (Fab) | procedural trees; Blender only via USD | built-in browser pane (`fab-search.js`, `fab-download.js`) + `fab_fetch.py`, RULES AST_04 | free, Fab Standard License | agent, after the user's picks | *Quixel on Fab* below |
| Maxtree | plant models (single models and volumes) | public Store API (`maxtree_search.py`), RULES AST_04 | paid per model or volume | user | *Maxtree* below |
| 3ds Max files | models from the user's own libraries | local files | per file | user | [max-import.md](../scene/max-import.md) |
| IES files | measured light distributions | manufacturer sites | per manufacturer | user or agent | [ies-profiles.md](../scene/lighting/ies-profiles.md) |

Candidate lists: RULES AST_04. "Agent" is whoever builds in the current work mode ([study-stages.md](study-stages.md)).

## Research
| Source | Gives | Access | Procedure |
|---|---|---|---|
| Render Reference Library | tagged reference images for look decisions | per-machine folder | [reference-library.md](../research/reference-library.md) |
| Blender manual and API docs | Blender facts | Blender MCP doc search | [machine-setup.md](machine-setup.md) › MCP tools |
| GitHub | real API usage, known bugs, workarounds | `gh search code/repos/issues` | [research-loop.md](../research/research-loop.md) |
| Papers (arXiv and others), measured data | physics, numbers, methods | web search | [research-loop.md](../research/research-loop.md) |
| Forums | workflows, fixes | web search | [research-loop.md](../research/research-loop.md) |
| YouTube | technique walkthroughs | `learning_from_video.py` (captions first) | [learning-from-video.md](../research/learning-from-video.md) |

When to stop for the user: RULES GAT_01.

## Where assets go (RULES AST_01)
Each study owns its assets, so it moves, archives or hands over self-contained: HDRIs, textures,
edited HDRIs, generated maps and their `meta.json` live in the study's own `library/`, downloaded
again even when another study has the same file. Never repoint a study at another study's or a
shared copy.
- Host scripts take `ARCHVIZ_PROJECT=<study>`; Blender takes `archviz.set_project(<study>)`. Run from
  inside a study, both find it without the setting. A shared `library/` above is read only by studies
  listed in its `legacy_studies.txt`; `polyhaven_fetch` prints a NOTE when it downloads anywhere
  but a study.
- Anything not from Poly Haven goes in `library/local/<name>/` with a `meta.json` stating the
  source (IES files, Quixel, Maxtree, edited HDRIs, baked maps and the script that made them).
  Ask before using any asset. Choosing a texture: [texture-selection.md](../materials/texture-selection.md).

## Poly Haven
`polyhaven_fetch.py search textures <cat>`, `tex <id> --resolution 2k`, `hdri <id> --resolution 4k`;
maps diff, arm, nor_gl, disp; `meta.json` has `dimensions_mm`. `search` matches categories only: for
names and tags, query `api.polyhaven.com/assets?t=textures|hdris` and judge a thumbnail contact sheet.
HTTP 520–525 is Cloudflare: retry the same call. Credit "Powered by Poly Haven" if the live API is
used in published work.

## Quixel on Fab (RULES AST_04)
Two sellers: `Quixel Megascans` (Blender takes the texture-set zip, FBX or glTF) and
`Quixel Megaplants` (only listings with `usd` import into Blender). Plain HTTP gets a Cloudflare 403,
so the catalog is read in the app's built-in browser pane (`mcp__Claude_Browser__*`), which runs on
this machine even while hidden. Claude in Chrome is not used: it may drive a Chrome on another machine.
Browse and download only through the scripts below (navigate, javascript, host scripts), never by clicking
or from screenshots.
1. Open `https://www.fab.com/sellers/Quixel%20Megascans` in the pane.
2. In one `javascript_tool` call send the text of `scripts/scene/assets/fab-search.js` followed by
   `await fabSearch({query, type, category, max_results})` (options in the file header). Each row
   holds the Megascans id, title, category, tags, formats, scan size, texel density, maps, plant
   species, Fab link and thumbnail. Category slugs come from a row's `category` path (`a/b` → `a--b`).
3. Save the rows to `<study>/_wip/fab/<topic>.json`, run
   `python scripts/scene/assets/asset_sheet.py <topic>.json <topic>-sheet.png` and judge the sheet.
4. Send the fits as the candidate list (RULES AST_04) with each Fab link, download file and size
   (`file`, `size_mb`; the first file is the largest, so name a smaller one when 2K is enough).
   Megaplants have no id: give the USD file name and check it names the listed species.
5. After the user's picks, in the same tab send `fab-search.js`, `scripts/scene/assets/fab-download.js`
   and `await fabDownloadLinks(picks)` in one call. "not signed in" → show the pane and ask the user
   to sign in there once with "remember me" (or import only the fab.com and epicgames.com cookies
   through the pane's ⋮ menu).
6. The links expire within minutes: save them straight away to `<study>/_wip/fab/<topic>-links.json`
   and run `python scripts/scene/assets/fab_fetch.py <topic>-links.json` (`ARCHVIZ_PROJECT=<study>`).
   It saves each pick to `library/local/<id>/`, checks the size, unzips, writes `meta.json` and
   deletes the zip. Check the map names carry the id, then delete the links file.

## Maxtree (RULES AST_04)
Plant models read over plain HTTP from the shop's public Store API; its own search knows Latin names only.
1. `python scripts/scene/assets/maxtree_search.py <study>/_wip/maxtree search <words>
   [--category Conifers] [--min-height-cm 300 --max-height-cm 800] [--out <topic>.json]`. The first
   run fetches the catalog (about 2 min; refetched after 7 days). Words match model, Latin and common
   names and categories; heights are per variant.
2. `asset_sheet.py <topic>.json <topic>-sheet.png`, then send the candidate list with each id
   (e.g. `V113_Olea_europaea_03`), its volume (the user may own the whole volume), height range and link.
3. The user downloads the chosen models into the study's `library/local/`; check the file names
   against the ids.
