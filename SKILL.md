---
name: blender-archviz
description: >-
  Default for any rendering or visualization work: photoreal archviz in Blender 5.2 + Cycles
  (LuxCore for detailed caustics through glass or water), with Rhino
  (.3dm) as geometry only. Covers materials (Poly Haven PBR, procedural concrete, wood, stone,
  metal, glass, water; edge wear, chips, cracks, leak streaks, anti-tiling), HDRI
  daylight and lights in real lumens (IES/LDT), physical camera, caustics, fog and mist,
  terrain, grass and meadow scatter, wet surfaces, matching a reference image, controls
  and finals. Use whenever the user mentions Blender, Cycles, LuxCore, shader or geometry nodes,
  Poly Haven, rendering, lookdev, lighting, HDRI, lux, caustics, fireflies or
  denoising, a Render Reference Library image, or wants a photoreal image of a Rhino model, even
  without naming Blender. Also for bringing 3ds Max (.max) assets into Blender (Maxtree,
  Evermotion, Forest Pack vegetation; V-Ray or Corona props), and for pulling, editing or
  pushing this skill (MIGRATE.md and maintenance rules).
---
<!-- blender-archviz-skill-loaded-marker -->

# Blender archviz

Read [RULES.md](RULES.md), then the task reference below. Check outstanding actions in
[MIGRATE.md](MIGRATE.md) when present; complete only applicable receiving-machine actions.
Method and code live here; study data lives in the current project.

## Workflow
Research → RES_02 → Rhino geometry → GAT_01 → import/camera/light/materials → GAT_02 →
look rounds and control proof → GAT_03 → open-UI final → study notes → user-declared closure.
Use [work modes](references/work-modes.md) for ownership and handoff artifacts.

## Stack and task router
| Task | Read |
|---|---|
| Setup, MCP, Rhino import, assets, runtime checks, finals | [Pipeline](references/pipeline.md) |
| Cycles by default; LuxCore caustics exception | [Caustics](references/caustics.md), [LuxCore](references/luxcore.md) |
| Material families and techniques | [Materials](references/materials/README.md) |
| HDRI lux, lumens/IES, camera, reference solve, fog | [Lighting and camera](references/lighting-camera.md) |
| Render quality, VRAM and denoising | [Render settings](references/render-settings.md) |
| Python helpers and node/GN API | [Helper index](references/helpers.md), [API traps](references/api-traps.md) |
| Renderer PNG measurements, crops, controls, bisects | [Validation](references/validation.md) |
| Reference discovery and new methods | [Reference library](references/reference-library.md), [Research](references/research-loop.md), [Video](references/learning-from-video.md) |
| 3ds Max assets | [Max import](references/max-import.md) |
| Errors and unexpected images | [Troubleshooting](references/troubleshooting.md) |
| Study closure | [Lifecycle](references/study-lifecycle.md) |
| Machine/file ownership | [Agent lock](references/agent-lock.md) |
| Skill changes, Git, review, sync | [Maintaining](references/maintaining.md) |
| Model roles, training, proven/research features | [Work modes](references/work-modes.md), [Coaching](references/codex-coaching.md), [Capabilities](references/capabilities.md) |

Code: `scripts/blender/` for Blender; `scripts/blender/materials/` for material families;
`scripts/controls/` for headless controls; `scripts/rhino/` for Rook geometry extraction;
`scripts/` for host measurement, asset and maintenance tools. Invocation details live in Pipeline.
