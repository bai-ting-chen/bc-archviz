---
name: bc-archviz
description: >-
  Photoreal architectural visualization in Blender 5.3 with Cycles and LuxCore,
  with Rhino as the geometry source. Use when the user asks to create or revise an
  architectural render or animation, or wants to maintain this skill (pull, edit, push).
---
<!-- bc-archviz-skill-loaded-marker -->

# bc-archviz

Read [RULES.md](RULES.md), then the task reference below. When the skill is pulled or loaded, follow [skill-maintaining.md](references/workflow/skill-maintaining.md) › Pull, then MIGRATE.md:
if `MIGRATE.md` holds sections from another machine (their `From:` line), apply and remove only those.
Method and code live here; study data lives in the current project.

## Workflow
GAT_xx = a user approval gate ([RULES.md](RULES.md)).
Research → GAT_01 → Rhino geometry → GAT_02 → import/camera/light/materials → GAT_03 → look
rounds and control proof → GAT_04 → open-UI final → study notes → user-declared closure.

Work mode: if the ai-work-modes skill is installed, it handles modes, briefs, Codex runs, reviews and the machine
lock, and the stage table and study documents below plug into it. Without it, Claude works alone.

## Task router
Read the files for the stage you are in.

### General
- [Study stages](references/workflow/study-stages.md): each stage's split between Claude and Codex
- [Study documents](references/workflow/agent-exchange.md): brief additions, source list, material schedule, research note
- [Review checklist](references/workflow/review-checklist.md): what a reviewer of this skill checks
- [Gates](references/workflow/gates.md): what to show the user at GAT_01–04
- [Sources](references/workflow/sources.md): every asset and research source, and where its procedure lives
- Writing Blender code: [Blender Python helpers](references/scene/blender-python-helpers.md) (use these first),
  [Blender API traps](references/scene/blender-api-traps.md) (check before running)
- [Troubleshooting](references/workflow/troubleshooting.md): errors and unexpected images

### 1. Research (→ GAT_01)
- [Capabilities](references/scene/capabilities.md): check what the pipeline already does
- [Reference library](references/research/reference-library.md): find reference images
- [Research loop](references/research/research-loop.md): a new method is needed
- [Learning from video](references/research/learning-from-video.md): the source is a video

### 2. Rhino geometry and import (→ GAT_02)
- [Pipeline](references/scene/pipeline.md): setup, MCP, runtime checks, Rhino import, assets
- [Max import](references/scene/max-import.md): 3ds Max assets
- [Terrain](references/scene/environment/terrain.md): naturally sloped ground around a building pad

### 3. Camera, light and materials (→ GAT_03)
- [Lighting and camera](references/scene/lighting-camera.md): HDRI, lumens/IES, camera, reference solve, fog
- [Materials](references/materials/index.md): general rules, material families (water in `materials/water/`) and
  shared effects (`references/effects/`: wear, variation, wet surfaces, caustics, anisotropy); the index routes all three

### 4. Look rounds and controls (→ GAT_04)
- [Renderer choice](references/renderer/renderer-choice.md): Cycles, or LuxCore for caustics
- [Caustics](references/effects/caustics.md), [LuxCore](references/renderer/luxcore.md): when caustics are needed
- [Render settings](references/renderer/render-settings.md): quality, VRAM, denoising
- [Validation](references/review/validation.md): PNG measurements, crops, controls, bisects

### 5. Final and closure
- [Pipeline](references/scene/pipeline.md) › Final render in the open UI
- [Closing a study](references/workflow/study-close.md): the user calls the study finished

### Skill maintenance
- [Maintaining](references/workflow/skill-maintaining.md): skill changes, Git, review, sync

## Repository map
Reference folders and code folders use the same topic names. Each code folder's README (where present) names the reference it implements.

| Topic | Reference folder | Code folder |
|---|---|---|
| Workflow, study tools | `references/workflow/` | `scripts/workflow/` |
| Research (reference matching, solving, video) | `references/research/` | `scripts/research/` |
| Scene: Rhino and Max import, camera, lighting, environment | `references/scene/` | `scripts/blender/core/`, `scripts/blender/scene/`, `scripts/scene/` |
| Materials, one folder per family | `references/materials/` | `scripts/blender/materials/` |
| Effects: caustics, variation, wet surfaces | `references/effects/` | `scripts/blender/effects/` |
| Wear by mechanism and shared locations/patterns | `references/effects/wear/` | `scripts/blender/effects/wear/` |
| Renderer: Cycles and LuxCore, finals | `references/renderer/` | `scripts/blender/renderer/` |
| Review: controls, validation | `references/review/` | `scripts/controls/`, `scripts/review/` |
| Rook geometry extraction (host) | — | `scripts/rhino/` |

| Stage | Reference | Code |
|---|---|---|
| 1. Research | `references/research/` | `scripts/research/` |
| 2. Rhino geometry and import | `references/scene/pipeline.md` | `scripts/blender/scene/io/`, `scripts/blender/core/` |
| 3. Camera, light, materials | `references/scene/lighting-camera.md`, `references/materials/` | `scripts/blender/scene/lighting/`, `scripts/blender/materials/` |
| 4. Look rounds and controls | `references/renderer/`, `references/review/` | `scripts/blender/renderer/`, `scripts/controls/` |
| 5. Final and closure | `references/scene/pipeline.md`, `references/workflow/study-close.md` | `scripts/blender/renderer/finals/`, `scripts/workflow/` |

Invocation details live in Pipeline.
