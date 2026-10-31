---
name: bc-archviz
description: >-
  Photoreal architectural visualization in Blender 5.2 with Cycles and LuxCore,
  with Rhino as the geometry source. Use when the user asks to create or revise an
  architectural render or animation, or wants to maintain this skill (pull, edit, push).
---
<!-- bc-archviz-skill-loaded-marker -->

# bc-archviz

Read [RULES.md](RULES.md), then the task reference below. When the skill is pulled or loaded, follow [skill-maintaining.md](references/workflow/skill-maintaining.md) › Pull, then MIGRATE.md:
if `MIGRATE.md` is present, check it, apply it and delete it.
Method and code live here; study data lives in the current project.

## Workflow
GAT_xx = a user approval gate ([RULES.md](RULES.md)).
[Work mode](references/workflow/work-modes.md) (the user's choice, RULES AGT_02) → Research →
GAT_01 → Rhino geometry → GAT_02 → import/camera/light/materials → GAT_03 → look rounds and
control proof → GAT_04 → open-UI final → study notes → user-declared closure.
Each stage opens with a brief and closes with a report ([agent exchange documents](references/workflow/agent-exchange.md)).

## Task router
Read the files for the stage you are in.

### General
- [Work modes](references/workflow/work-modes.md): who does what, Normal or CPM
- [Study stages](references/workflow/study-stages.md): each stage's split between models
- [Agent exchange documents](references/workflow/agent-exchange.md): brief, report and review formats
- [Gates](references/workflow/gates.md): what to show the user at GAT_01–04
- [Agent lock](references/workflow/agent-lock.md): before touching Blender or study files
- [Coaching](references/review/codex-coaching.md): before every stage report or review
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

### 3. Camera, light and materials (→ GAT_03)
- [Lighting and camera](references/scene/lighting-camera.md): HDRI, lumens/IES, camera, reference solve, fog
- [Materials](references/materials/index.md): general rules, material families (water in `materials/water/`) and
  shared effects (`references/effects/`: edge wear, variation, wet surfaces, caustics); the index routes all three

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
| Workflow, study tools, Codex review | `references/workflow/` | `scripts/workflow/` |
| Research (reference matching, solving, video) | `references/research/` | `scripts/research/` |
| Scene: Rhino and Max import, camera, lighting, environment | `references/scene/` | `scripts/blender/core/`, `scripts/blender/scene/`, `scripts/scene/` |
| Materials, one folder per family | `references/materials/` | `scripts/blender/materials/` |
| Effects: edge wear, caustics, variation, wet surfaces | `references/effects/` | `scripts/blender/effects/` |
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
