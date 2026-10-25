---
name: bc-archviz
description: >-
  Photoreal architectural visualization in Blender 5.2 with Cycles and LuxCore,
  with Rhino as the geometry source. Use when the user asks to create or revise an
  architectural render or animation, or wants to maintain this skill (pull, edit, push).
---
<!-- bc-archviz-skill-loaded-marker -->

# bc-archviz

Read [RULES.md](RULES.md), then the task reference below. Check outstanding actions in
[MIGRATE.md](MIGRATE.md) when present; complete only applicable receiving-machine actions.
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
- [Materials](references/materials/index.md): material families and techniques

### 4. Look rounds and controls (→ GAT_04)
- [Renderer choice](references/renderer/renderer-choice.md): Cycles, or LuxCore for caustics
- [Caustics](references/materials/caustics.md), [LuxCore](references/renderer/luxcore.md): when caustics are needed
- [Render settings](references/renderer/render-settings.md): quality, VRAM, denoising
- [Validation](references/review/validation.md): PNG measurements, crops, controls, bisects

### 5. Final and closure
- [Pipeline](references/scene/pipeline.md) › Final render in the open UI
- [Study lifecycle](references/workflow/study-lifecycle.md): the user calls the study finished

### Skill maintenance
- [Maintaining](references/workflow/skill-maintaining.md): skill changes, Git, review, sync

Code: `scripts/blender/` for Blender; `scripts/blender/materials/` for material families;
`scripts/controls/` for headless controls; `scripts/rhino/` for Rook geometry extraction;
`scripts/` for host measurement, asset and maintenance tools. Invocation details live in Pipeline.
