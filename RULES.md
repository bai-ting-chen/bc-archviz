# House rules — standing, do not re-litigate

## Priorities (user, 2026-10-06)
1. **Native first.** Blender's own features (Cycles, shader nodes, Geometry Nodes, modifiers, Sky
   Texture) before self-written external tools — native work stays editable in the .blend and
   survives Blender updates; external tools are a last resort, and say so when used.
2. **Unbiased first.** Order: (a) Cycles path tracing; (b) native physically based approximations
   (MNEE, GN wavefront caustics) only when (a) cannot converge — state why and the bias;
   (c) external tools only when nothing native works — tell the user. Fakes (light-path tricks,
   projected patterns) only as a declared fallback. The point of the studies is renders that
   hold up as physics, so a bias must always be named, never hidden.
3. **Research before anything new.** Manual/API, forums, YouTube (`yt_learn.py`); compare 2–4
   workflows, choose by 1–2, cite sources, then build and prove. Building first and researching
   late is how the caustics work drifted (261006). Videos are evidence, not authority.

## Split
4. **Rhino = geometry only.** Materials, lights, camera look and render settings live in Blender
   (one place to edit the look; Rhino materials don't translate). Layer/block/object names are the
   hooks; discard .3dm materials. Rhino files are read-only; re-meshing imported meshes is fine.

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
8. **Edge wear = dirty edge (shading). Edge chip = geometry.** The user's definitions; keep separate.

## Process
9. **A control render is the only proof.** Feature OFF + same scene twice (noise floor; same seed
   for the feature diff); read *changed > 2 %* and look at a diff/crop; verify the control really
   removed the feature. Whole-frame averages hide local effects, and a broken control looks like
   "no effect".
10. Measure on the PNG the renderer wrote (`imgstats.py`, `refmatch.py`) — AgX rolls off whites,
    so linear values mislead. Process frames → study `_wip/`; finals through the open Blender UI
    so the user sees them.
11. Bisect odd behaviour in a minimal headless scene (`tools/controls/`) before tuning the real
    one — the MNEE and green-ceiling problems were each found in minutes that way.

## Safety
12. MCP code runs unguarded in the user's Blender: save first, rebuild-from-script study files,
    never delete user data blocks without asking.
13. GPU is 8 GB: no adaptive subdivision over large diced surfaces (it ran out of memory).
