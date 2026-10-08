# House rules — standing, do not re-litigate

## What belongs in this skill
0. **Methods, constants, traps and taste — never one scene's numbers.** Scenes, software and
   parameters all change; what carries you is knowing how to operate, how to experiment and
   where to get resources. The test for any number: *would it be the same in a different scene?*
   A chipped edge is 5 mm on one job and 100 mm on the next, so it is a result, not knowledge —
   size it from the shot (RULES 8) and record it in that study's `STUDY_NOTES.md`. Physical
   constants (albedo, IOR, lm/W, typical EV100), conventions, procedures and taste belong here.

## Priorities (user, 2026-10-06)
1. **Native first.** Blender's own features (Cycles, shader nodes, Geometry Nodes, modifiers, Sky
   Texture) before self-written external tools — native work stays editable in the .blend and
   survives Blender updates; external tools are a last resort, and say so when used.
2. **Unbiased first.** Order: (a) Cycles path tracing; (b) native physically based approximations
   (MNEE, GN wavefront caustics) only when (a) cannot converge — state why and the bias;
   (c) external tools only when nothing native works — tell the user. Fakes (light-path tricks,
   projected patterns) only as a declared fallback. The point of the studies is renders that
   hold up as physics, so a bias must always be named, never hidden.
3. **Research before anything new — from the physics down, not from tutorials up.** Order:
   (a) the mechanism: optics/physics papers, measured data, the governing equations (why does wet
   concrete darken? Lekner–Dorf: internal reflection in the water film, non-linear in albedo);
   (b) how others implement it: manual/API, forums, papers' renderers, YouTube (`yt_learn.py`);
   (c) map the model onto native nodes and say which terms are kept and which approximated.
   Compare 2–4 workflows, choose by 1–2, cite sources, then build and prove. More and more
   requests will be things few people have done in Blender or archviz (user, 2026-10-08): a
   tutorial can only copy a look, the science lets you build a new method and know its limits.
   Building first and researching late is how the caustics work drifted (261006). Videos are
   evidence, not authority.

## Split
4. **Rhino = geometry only.** Materials, lights, camera look and render settings live in Blender
   (one place to edit the look; Rhino materials don't translate). Layer/block/object names are the
   hooks; discard .3dm materials. Rhino files are read-only; re-meshing imported meshes is fine.

4a. **Rhino models are clean and fast** (user, 2026-10-08): one arc per curved edge, straight
    where straight, a few key readings per edge — not splines through readings or arcs fitted
    to pixels. Check once with `tools/edge_overlay.py`, then the approval gate (10a).
## Look
5. **Real units everywhere.** Daylight: calibrated HDRI in lux + matched sun. Artificial: lumens at
   683 lm/W — the same constant the camera uses, so a real ISO/f/shutter gives the right exposure
   without eyeballing. Model each fixture once (a visible lens *and* an analytic light both lighting
   double the flux). White balance is a camera setting. Parallel verticals.
6. Wire every map that applies; real-world UVs; physically plausible albedo/IOR (materials.md) —
   wrong scale or albedo reads as "CG" faster than any lighting error.
7. Profile the Render Reference Library slice before a look decision — 3,188 tagged images at
   `%USERPROFILE%\PROJECT\Render Reference Library`; grep `library.jsonl` to a shortlist of
   5-10 paths and open only those, never browse. Its `CLAUDE.md` is the facet schema.
   Recreating a reference: solve its camera first, then balance lights region by region;
   global exposure is the last knob because it hides which light is wrong.
8. **Edge wear = dirty edge (shading). Edge chip = geometry.** The user's definitions; keep
   separate. **Size every feature from the shot, never from a remembered value** — chips, grain,
   joints, ripples and grunge all read by how many pixels they occupy, so the same material wants
   different numbers on a close-up and on a wall 4 m away. Judge the first render and scale.

8a. **Natural light = matching HDRI sky first** (user, 2026-10-07). Whenever sun, sky or any
   daylight is in the scene, light it with an HDRI whose sky matches the reference (overcast vs
   clear, sun height and direction, horizon content) before any Sky Texture, sun-only rig or
   fake. Search Poly Haven by tag/thumbnail for the match; fall back to Sky Texture only when no
   HDRI fits, and say so.
8b. **Detail pass at native resolution** (user praised, 2026-10-08). Region means match long
    before the image does. Once they agree, crop each material/effect at full resolution beside
    the same crop of the reference and judge its *character*: feature size, edge sharpness,
    contrast, density, orientation, distribution. The trowel marks matched in mean but read as
    thin bright scratches against the ref's soft wisps — only the crop showed it. Repeat after
    every change to that feature; half-res pairs hide it.
8c. **Nature is patchy, never continuous or uniform** (user, 2026-10-08). Wetness, stains,
    wear, dirt, splashes: large here, small there, absent elsewhere. A constant-width band or a
    contour ring reads as impossible. Drive extent with a slow noise that can reach zero, and
    give marks a physical shape (dried splash = blob darker at its rim, not a line).
## Process
9. **A control render is the only proof.** Feature OFF + same scene twice (noise floor; same seed
   for the feature diff); read *changed > 2 %* and look at a diff/crop; verify the control really
   removed the feature. Whole-frame averages hide local effects, and a broken control looks like
   "no effect".
10. Measure on the PNG the renderer wrote (`imgstats.py`, `refmatch.py`) — AgX rolls off whites,
    so linear values mislead. Process frames → study `_wip/`; finals through the open Blender UI
    so the user sees them.
10a. **Rhino → Blender gate** (user, 2026-10-07). After the Rhino model is finished, stop and
    show the user (viewport captures + a list of what was modelled and left out); pipe to
    Blender only after the user approves the geometry. Rework in Rhino is cheap, a look-dev
    round on wrong geometry is not.
11. Bisect odd behaviour in a minimal headless scene (`tools/controls/`) before tuning the real
    one — the MNEE and green-ceiling problems were each found in minutes that way.

## Safety
12. MCP code runs unguarded in the user's Blender: save first, rebuild-from-script study files,
    never delete user data blocks without asking.
13. Know the GPU's VRAM before committing to a heavy scene; adaptive subdivision over large
    diced surfaces is the usual way to exhaust it (render-settings.md › Memory).
