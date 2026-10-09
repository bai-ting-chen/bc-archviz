# MIGRATE — run before anything else, then delete

## 261008 — LuxCore for caustics, per-study assets, final-render gate
A study of sun caustics through patterned glass showed Cycles (path tracing, path guiding, MNEE)
cannot converge them; LuxCore CPU light tracing can and is energy-correct. The user made three
standing rules: Cycles stays default but LuxCore is preferred for detailed caustics (RULES 2a);
every study owns its assets in its own `library/` (RULES 10c); a final render needs the user's
approval of a preview and runs in the open Blender UI (RULES 10b). New `references/luxcore.md`;
caustics, lighting-camera, materials, pipeline, api-traps, capabilities and SKILL.md updated.

### 1. Install BlendLuxCore (needs Blender 5.2)
Check: `%APPDATA%\Blender Foundation\Blender\5.2\extensions\user_default\blendluxcore\blender_manifest.toml` exists with `version = "2.11.1"` or newer.
Do: `gh release download v2.11.1 -R LuxCoreRender/BlendLuxCore -p "BlendLuxCore-2.11.1.zip" -D <empty temp folder>`;
compare its sha256 with `gh release view v2.11.1 -R LuxCoreRender/BlendLuxCore --json assets`;
`"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b -c extension install-file -r user_default --enable <zip>`
(the log must say `BlendLuxCore 2.11.1 registered (with pyluxcore …)`); delete the zip.

### 2. Pick up the new rules in local memory
Check: the project's memory index (`~/.claude/projects/<project>/memory/MEMORY.md`) has entries for per-study assets, the final-render gate and LuxCore for caustics.
Do: add one memory file each (feedback type) summarising RULES 10c, 10b and 2a, and the index lines.

### 3. Project layout
Check: new studies are created with their own `library/` (`polyhaven/`, `local/`); the project `CLAUDE.md` does not describe a shared `library/` as where studies read assets.
Do: update the project `CLAUDE.md` table: assets live in each study's `library/`; a top-level
`library/` remains only for studies that already use it (leave finished studies untouched).

### 4. Directional UVs moved into archviz
Check: `scripts/blender/archviz.py` defines `directional_uv` (it does after pulling).
Do: nothing to run. New code calls `archviz.directional_uv(obj, size_m, axis)` for any
directional texture (grain, boards, brushing, veining, long tiles); `wood_wear.grain_uv` still
works as an alias for older study scripts.

### 5. HDRI is the sole natural light
Check: the project's memory index has an entry saying an HDRI sky is never combined with a sun lamp.
Do: add that memory (feedback type) from RULES 8a; in any open study script, remove sun lamps
that sit alongside an HDRI and rotate the HDRI to place its own sun instead.

## 261009 — Review: general knowledge only, each rule once
Pull-only. RULES.md and every reference were reviewed: study anecdotes and one scene's tuned
numbers removed or generalised, provenance tags dropped, each rule stated once in RULES.md with
pointers elsewhere, the clean-arcs Rhino rule removed, `archviz.directional_uv` added. Re-read
RULES.md; drop any local memory that repeats the removed clean-arcs Rhino rule.

### 6. Local memory
Check: the project's memory has no entry telling Rhino models to use one arc per curved edge.
Do: delete such a memory file and its index line.

### Last. Delete this file
Only after the steps above changed something here: delete MIGRATE.md, commit, pull --rebase, push.
