# House rules — standing, do not re-litigate

## What belongs in this skill
0. **Methods, constants, traps and taste — never one scene's numbers.** Scenes, software and
   parameters all change; what carries you is knowing how to operate, how to experiment and
   where to get resources. The test for any number: *would it be the same in a different scene?*
   A chipped edge is 5 mm on one job and 100 mm on the next, so it is a result, not knowledge —
   size it from the shot (RULES 8) and record it in the project's study notes. Physical
   constants (albedo, IOR, lm/W, typical EV100), conventions, procedures and taste belong here.
0a. **Skill is generic, projects are local**. Only the skill goes to GitHub;
   project folders (data, studies, scenes, renders) stay on their machine and are never pushed.
   The skill names no project, project path, repo or study. Every machine and every project
   loads it, so a project name in here is wrong everywhere else. Lessons go in without where they
   came from. Changing the skill: `references/maintaining.md` (pull first, git identity, and a
   `MIGRATE.md` with every push).

## Priorities
1. **Native first.** Blender's own features (Cycles, shader nodes, Geometry Nodes, modifiers, Sky
   Texture) before self-written external tools — native work stays editable in the .blend and
   survives Blender updates; external tools are a last resort, and say so when used.
2. **Unbiased first.** Order: (a) Cycles path tracing; (b) native physically based approximations
   (MNEE, GN wavefront caustics) only when (a) cannot converge — state why and the bias;
   (c) external tools only when nothing native works — tell the user. Fakes (light-path tricks,
   projected patterns) only as a declared fallback. The point of the studies is renders that
   hold up as physics, so a bias must always be named, never hidden.
2a. **Renderer: Cycles by default, LuxCore for detailed caustics**. When
   caustics or heavy refraction carry the shot — sun through patterned glass or glass block,
   glass-on-water, multi-interface glass — render in LuxCore (BlendLuxCore, path tracing with
   light tracing: GPU camera paths + CPU light paths). It is the one standing exception to
   native-first: Cycles path tracing, path guiding and MNEE all fail on specular–diffuse–specular
   paths from a sun-sized source, while LuxCore light tracing is unbiased and energy-correct there (caustics.md › Decision). Say it is
   an external engine when you switch.
3. **Research before anything new — from the physics down, not from tutorials up.** Order:
   (a) the mechanism: optics/physics papers, measured data, the governing equations (why does wet
   concrete darken? Lekner–Dorf: internal reflection in the water film, non-linear in albedo);
   (b) how others implement it: manual/API, forums, papers' renderers, YouTube (`yt_learn.py`);
   (c) map the model onto native nodes and say which terms are kept and which approximated.
   Compare 2–4 workflows, choose by 1–2, cite sources, then build and prove. Read a source's own
   pictures and video frames at full resolution, not a summary of its text: the method is often
   only in the images, and a near-copy built from the summary misses it. More and more
   requests will be things few people have done in Blender or archviz: a
   tutorial can only copy a look, the science lets you build a new method and know its limits.
   Videos are evidence, not authority.

## Split
4. **Rhino = geometry only.** Materials, lights, camera look and render settings live in Blender
   (one place to edit the look; Rhino materials don't translate). Layer/block/object names are the
   hooks; discard .3dm materials. Rhino files are read-only; re-meshing imported meshes is fine.

## Look
5. **Real units everywhere.** Daylight: calibrated HDRI in lux, nothing else (8a). Artificial: lumens at
   683 lm/W — the same constant the camera uses, so a real ISO/f/shutter gives the right exposure
   without eyeballing. A specified fixture uses the manufacturer's photometric file (IES; LDT
   converted) at its catalogue output — never a power set by eye (lighting-camera › IES).
   Model each fixture once (a visible lens *and* an analytic light both lighting
   double the flux). White balance is a camera setting. Parallel verticals.
6. Wire every map that applies; real-world UVs; physically plausible albedo/IOR (materials.md) —
   wrong scale or albedo reads as "CG" faster than any lighting error.
7. Profile the Render Reference Library slice before a look decision — a tagged image library in a
   per-machine folder (usually `%USERPROFILE%\PROJECT\Render Reference Library`; ask if it isn't
   there). Grep its `library.jsonl` to a shortlist of
   5-10 paths and open only those, never browse. Its `CLAUDE.md` is the facet schema.
   Recreating a reference: solve its camera first, then balance lights region by region;
   global exposure is the last knob because it hides which light is wrong.
8. **Edge wear = dirty edge (shading). Edge chip = geometry.** The user's definitions; keep
   separate. **Size every feature from the shot, never from a remembered value** — chips, grain,
   joints, ripples and grunge all read by how many pixels they occupy, so the same material wants
   different numbers on a close-up and on a wall 4 m away. Judge the first render and scale.
   A feature smaller than a pixel reads only as its aggregate (a wet lawn's sheen, not its
   drops): model that, and ask before building micro-geometry. **Keep the final view in sight:**
   size a detail feature in the final camera first, and pair every close-up shown to the user
   with a native-resolution crop of the final view — a feature tuned in a macro view can vanish
   in the shot.

8a. **Natural light = matching HDRI sky first**. Whenever sun, sky or any
   daylight is in the scene, light it with an HDRI whose sky matches the reference (overcast vs
   clear, sun height and direction, horizon content) before any Sky Texture, sun-only rig or
   fake. Search Poly Haven by tag/thumbnail for the match; fall back to Sky Texture only when no
   HDRI fits, and say so. **The HDRI is the sole natural light source**:
   never a sun lamp alongside it — not "matched", not to boost a weak sun, not after painting the
   disc out. The HDRI's sun direction (`hdri_analyse`) only guides rotating and placing the map.
   If its sun is too weak or in the wrong place for the shot, choose another HDRI.
8b. **Detail pass at native resolution**. Region means match long
    before the image does. Once they agree, crop each material/effect at full resolution beside
    the same crop of the reference and judge its *character*: feature size, edge sharpness,
    contrast, density, orientation, distribution — a feature can match in mean and still read
    wrong in character. Repeat after every change to that feature; half-res pairs hide it.
8c. **Nature is patchy, never continuous or uniform**. Wetness, stains,
    wear, dirt, splashes: large here, small there, absent elsewhere. A constant-width band or a
    contour ring reads as impossible. Drive extent with a slow noise that can reach zero, and
    give marks a physical shape (dried splash = blob darker at its rim, not a line).
8d. **Repetition and imperfection**. Every surface of repeated units or tiled maps (glass block,
    brick, stone, tile, curtain wall, mortar) gets randomness: no visible texture repeat, variation
    per unit (tint, roughness, pattern, small tilt), and concave joints get dust, darkest in the
    corner and fading outward. Plan it into the first material pass; perfectly regular units and
    razor-clean corners read as CG. How: materials.md › Randomness, edge-wear.md › Concave corners.
## Process
9. **A control render is the only proof.** Feature OFF + same scene twice (noise floor; same seed
   for the feature diff); read *changed > 2 %*, several times the noise floor, and look at a
   diff/crop; verify the control really
   removed the feature. Whole-frame averages hide local effects, and a broken control looks like
   "no effect".
10. Measure on the PNG the renderer wrote (`imgstats.py`, `refmatch.py`) — AgX rolls off whites,
    so linear values mislead. Process frames → study `_wip/`.
10a. **Rhino → Blender gate**. After the Rhino model is finished, stop and
    show the user (viewport captures + a list of what was modelled and left out); pipe to
    Blender only after the user approves the geometry. Rework in Rhino is cheap, a look-dev
    round on wrong geometry is not.
10b. **Final render gate**. (1) Render a preview, show it, state the final's
    resolution, time budget and expected noise, and **wait for approval** — the user reviews the
    preview first; a material or light change after approval means a new preview. (2) Run the
    final **in the open Blender UI** so the user watches it live; headless renders are for tests,
    controls and previews. (3) Set **no time or sample limit** on the final: it renders until the
    user stops it, and saving/denoising run on stop. A halt time is fixed when the session starts
    and a finished render cannot be resumed, so a limit can only cut the user's choice short.
    (4) Before any long or unattended final, render a short **full-frame** test with exactly the
    final's settings (raw and denoised) and look at every surface, not only the one under
    discussion. Bring known risks and their tested fixes to the user *before* launch; a fix is
    not withheld because it is not yet approved. Look at the saved result before calling it done
    or sending it anywhere.
10c. **Each study owns its assets**. HDRIs, textures, edited HDRIs, generated
    maps and their `meta.json` live in the study's own `library/`, downloaded again even when
    another study has the same file, so a study moves, archives or hands over self-contained.
10d. **Everything a study makes stays in its folder**: crops, comparisons, test renders,
    measurements, downloads and throwaway scripts go in the study's `_wip/`, never the session
    scratchpad or %TEMP% — tell subagents the path too. One place holds all a study produced.
    Software is not study output: Blender extensions and add-ons install into Blender's own
    extension folder through the installer, and the downloaded zip is deleted afterwards.
10e. **Closing a study cleans it.** When the user calls a study finished, list its milestone
    scenes (every final plus real turning points) under `## Milestones` in STUDY_NOTES.md, then run
    `scripts/study_close.py <study>` (plan) and `--apply`: it makes the milestones self-contained
    (copies outside or `_wip` files they use into `library/local/`), deletes `_wip/`, other .blend
    files, backups, library files no milestone uses and vendor/cache folders, and verifies every
    milestone reference still resolves. Finals, notes, scripts and .3dm stay. No asking per file.
11. Bisect odd behaviour in a minimal headless scene (`scripts/controls/`) before tuning the real
    one — a small scene isolates the cause in minutes where the full scene hides it.

## Agents
14. **Cross-check all code with the other model.** Code Claude writes is reviewed by Codex
    (`scripts/codex_review.py`); code Codex writes is reviewed by a fresh Claude subagent that
    sees only the task and the diff (maintaining.md › Review). A new technique also gets its
    control render (RULES 9). The writer weighs each finding, fixes what holds, and tells the
    user what it rejected and why. With only one model available, the review runs in a fresh
    session of that model, and the user is told the cross-check was same-model.
15. **Claude steers, Codex minds the details** (a guide, not a fence). Claude takes the big
    decisions: method and research conclusions, proof renders, look judgement, the shape of the
    skill. Codex suits detail work: scripts from a short brief, gathering sources into a brief,
    measurement runs (numbers table + one contact sheet), past workflows. Long output goes to a
    file with a short summary back. Skill changes reach the repo through Claude as a diff it
    commits. Reference-image analysis and Rhino modelling stay with Claude (CPM: Rhino goes to Codex, 15a). Either model may
    take over alone when the other is out of tokens (stop it at a clean point, not mid-edit);
    this skill and the project files are the whole handover (`references/research-loop.md`), so nothing lives only in one
    agent's memory.
15a. **Two work modes; the user names the mode, normal is the default.**
    - **Normal mode:** the split above.
      - Claude:
        - plans and decides;
        - does Rhino modelling;
        - does the detailed research itself (papers, manual, forums, online, YouTube via
          `yt_learn.py`) and summarises it;
        - reviews Codex's code.
      - Codex builds from briefs and reviews Claude's code (RULES 14).
    - **Codex priority mode (CPM)** (Claude's budget is low): Claude takes the user's seat as director,
      and all hard labour goes to Codex.
      - Claude: the big decisions, directional guidance and aesthetic opinions.
        - Reads Codex's research notes and turns them into the method decision.
        - Judges the look against the reference.
        - Writes short briefs that command Codex.
        - Still brings the user gates (10a, 10b) to the user.
      - Codex: everything else, done by hand:
        - all coding and test runs;
        - Rhino modelling (through Rook);
        - detailed research, online and YouTube included, written as separate notes in the
          study's `_wip/research/` with sources and full-resolution evidence (RULES 3);
        - measurements, crops and comparison sheets for Claude to judge.
      - A **Codex builder** session writes and runs the code (and does the modelling and research
        stages).
      - A **parallel Codex reviewer** session (fresh, read-only) cross-checks each stage's diff
        against the brief.
      - The builder weighs the findings, as in RULES 14.
      - At most two Codex sessions at once: one builder and one reviewer. Never two builders: the
        builder holds the study's AGENT_LOCK (RULES 16), so a second builder must stop.
      - This replaces the other-model review for the duration, and the user is told the review was
        same-model.
    - The mode lasts until the user switches back, or the round ends. Then return to normal mode:
      if Claude's tokens refilled, the code made during the mode also gets its Claude review.
    - How to launch both modes: maintaining.md › Handing work to Codex.
16. **One agent at a time on Blender and on a file.** There is one Blender and one MCP port per
    machine, shared by every project. Before driving Blender or editing a study's files, check
    `%LOCALAPPDATA%\BlenderMCP\AGENT_LOCK` (machine-wide, beside the MCP server): absent →
    create it (`<agent> | <what: Blender, study or files> | <start, ISO time>`), work, delete it
    when done; present and not yours → stop and tell the user, never take it over. A
    render left running keeps the lock until it ends.

17. **Modular code and docs, no god scripts.** Either model must be able to pick up any file
    cold. One module per job, functions that do one thing with real-unit arguments and a
    one-line docstring, no hidden global state; extend by adding a function or module, not by
    growing one file. A module that gathers unrelated jobs, or that cannot be changed without
    reading all of it, gets split. Docs the same: one topic per reference, short sections,
    pointers instead of repeats.

## Safety
12. MCP code runs unguarded in the user's Blender: save first, rebuild-from-script study files,
    never delete user data blocks without asking.
13. Know the GPU's VRAM before committing to a heavy scene; adaptive subdivision over large
    diced surfaces is the usual way to exhaust it (render-settings.md › Memory).
