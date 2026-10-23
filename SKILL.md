---
name: bc-archviz
description: >-
  Photoreal architectural visualization in Blender 5.2 with Cycles and LuxCore,
  using Rhino geometry. Use whenever the user wants a render or an architectural
  visualization, or wants to maintain this skill (pull, edit, push).
---
<!-- bc-archviz-skill-loaded-marker -->

# bc-archviz

Read [RULES.md](RULES.md), then the task reference below. Check outstanding actions in
[MIGRATE.md](MIGRATE.md) when present; complete only applicable receiving-machine actions.
Method and code live here; study data lives in the current project.

## Workflow
Research → GAT_01 → Rhino geometry → GAT_02 → import/camera/light/materials → GAT_03 →
look rounds and control proof → GAT_04 → open-UI final → study notes → user-declared closure.
Use [work modes](references/workflow/work-modes.md) for ownership and [handoff documents](references/workflow/handoff-documents.md) for handoff artifacts.

## Stack and task router
| Task | Read |
|---|---|
| Setup, MCP, Rhino import, assets, runtime checks, finals | [Pipeline](references/scene/pipeline.md) |
| Cycles by default; LuxCore caustics exception | [Renderer choice](references/renderer/renderer-choice.md), [Caustics](references/materials/caustics.md), [LuxCore](references/renderer/luxcore.md) |
| Material families and techniques | [Materials](references/materials/index.md) |
| HDRI lux, lumens/IES, camera, reference solve, fog | [Lighting and camera](references/scene/lighting-camera.md) |
| Render quality, VRAM and denoising | [Render settings](references/renderer/render-settings.md) |
| Python helpers and node/GN API | [Helper index](references/scene/helpers.md), [API traps](references/scene/api-traps.md) |
| Renderer PNG measurements, crops, controls, bisects | [Validation](references/review/validation.md) |
| Reference discovery and new methods | [Reference library](references/research/reference-library.md), [Research](references/research/research-loop.md), [Video](references/research/learning-from-video.md) |
| 3ds Max assets | [Max import](references/scene/max-import.md) |
| Errors and unexpected images | [Troubleshooting](references/workflow/troubleshooting.md) |
| Study closure | [Lifecycle](references/workflow/study-lifecycle.md) |
| Machine/file ownership | [Agent lock](references/workflow/agent-lock.md) |
| Skill changes, Git, review, sync | [Maintaining](references/workflow/skill-maintaining.md) |
| Model roles, training, proven/research features | [Work modes](references/workflow/work-modes.md), [Study stages](references/workflow/study-stages.md), [Handoff documents](references/workflow/handoff-documents.md), [Coaching](references/review/codex-coaching.md), [Capabilities](references/scene/capabilities.md) |

Code: `scripts/blender/` for Blender; `scripts/blender/materials/` for material families;
`scripts/controls/` for headless controls; `scripts/rhino/` for Rook geometry extraction;
`scripts/` for host measurement, asset and maintenance tools. Invocation details live in Pipeline.
