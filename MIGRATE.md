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

### Last. Delete this file
Only after the steps above changed something here: delete MIGRATE.md, commit, pull --rebase, push.
