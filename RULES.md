## House rules

### Governance

**GOV_01 — Recording reusable knowledge.**  
Rule: Keep scene-independent methods, constants, traps and taste; scene results belong in study notes.  
Read: [maintaining.md](references/maintaining.md)

**GOV_02 — Working with skill and project files.**  
Rule: Publish only generic skill code and method; keep data specific to each project local and unnamed here.  
Read: [maintaining.md](references/maintaining.md)

**GOV_03 — Synchronizing this skill.**  
Rule: Pull before editing, use the per-clone identity, and leave outstanding receiving-machine actions with pushes.  
Read: [maintaining.md](references/maintaining.md)

**GOV_04 — Extending code or documents.**  
Rule: Keep one module per job and one authority per helper; use focused functions and topic references.  
Read: [maintaining.md](references/maintaining.md)

### Renderer

**REN_01 — Choosing an implementation.**  
Rule: Prefer editable Blender-native methods; declare external fallbacks, subject to REN_03.  
Read: [caustics.md](references/caustics.md)

**REN_02 — Choosing a transport method.**  
Rule: Prefer unbiased transport, then native physical approximations, then external tools; disclose every bias or fake.  
Read: [caustics.md](references/caustics.md)

**REN_03 — Use LuxCore when detailed caustics or heavy refraction carries the shot.**  
Rule: Use LuxCore PATH with light tracing; otherwise default to Cycles and disclose the external engine.  
Read: [luxcore.md](references/luxcore.md)

### Research

**RES_01 — Building a new technique.**  
Rule: Research physics and full-resolution source evidence, compare workflows, cite and prove the chosen method.  
Read: [research-loop.md](references/research-loop.md)

**RES_02 — Sources are gathered for a new technique.**  
Rule: Show the question, sources and gaps; wait for user links before analysis; quick API lookups are exempt.  
Read: [work-modes.md](references/work-modes.md)

**RES_03 — Making a look decision or recreating a reference.**  
Rule: Shortlist the reference library; solve the reference camera first and adjust exposure last.  
Read: [reference-library.md](references/reference-library.md)

### Pipeline

**PIP_01 — Transferring Rhino geometry.**  
Rule: Keep source Rhino documents read-only; author materials, lighting, camera look and rendering in Blender.  
Read: [pipeline.md](references/pipeline.md)

### Lighting and camera

**LGT_01 — Setting lights or camera.**  
Rule: Use photometric units and physical camera exposure; count each emitter once, white-balance and keep verticals parallel.  
Read: [lighting-camera.md](references/lighting-camera.md)

**LGT_02 — Lighting daylight.**  
Rule: Use a matching HDRI as the sole natural source; declare Sky Texture fallback only if none fits.  
Read: [lighting-camera.md](references/lighting-camera.md)

### Materials

**MAT_01 — Authoring surface materials.**  
Rule: Use all applicable maps, real-scale directional UVs and physically plausible surface ranges.  
Read: [physical-ranges.md](references/materials/physical-ranges.md)

**MAT_02 — Authoring edge damage.**  
Rule: Keep dirty-edge shading distinct from geometric chips.  
Read: [edge-wear.md](references/materials/edge-wear.md)

**MAT_03 — Sizing visible detail.**  
Rule: Size from the final shot; pair every close-up with a native final-view crop.  
Read: [scale.md](references/materials/scale.md)

**MAT_04 — Features are sub-pixel.**  
Rule: Model their aggregate appearance and ask before building micro-geometry.  
Read: [scale.md](references/materials/scale.md)

**MAT_05 — Authoring natural surface marks.**  
Rule: Make marks patchy, able to disappear, with physically shaped extents.  
Read: [variation.md](references/materials/variation.md)

**MAT_06 — Using repeated units or tiled maps.**  
Rule: Add per-unit variation, hide repeats and fade concave-joint dust outward from corners in the first pass.  
Read: [variation.md](references/materials/variation.md)

### Validation

**VAL_01 — Judging material or effect character.**  
Rule: Compare native-resolution crops beside the reference and repeat after changing that feature.  
Read: [validation.md](references/validation.md)

**VAL_02 — Claiming a feature works.**  
Rule: Prove it with feature-off and repeated-baseline renders, noise-floor measurements and inspected diffs.  
Read: [validation.md](references/validation.md)

**VAL_03 — Measuring the rendered look.**  
Rule: Measure renderer-written display PNGs; use linear energy data only for physical calibration controls.  
Read: [validation.md](references/validation.md)

**VAL_04 — Diagnosing odd behaviour.**  
Rule: Bisect in a minimal control scene before tuning the full scene.  
Read: [validation.md](references/validation.md)

### Approval gates

**GAT_01 — A Rhino study model is ready.**  
Rule: Show captures and modelled/omitted items; wait for geometry approval before import.  
Read: [pipeline.md](references/pipeline.md)

**GAT_02 — The first full material build is ready.**  
Rule: Show schedule, final-camera render, native reference crops and uncertain candidates; wait for approval and re-gate swaps.  
Read: [work-modes.md](references/work-modes.md)

**GAT_03 — Launching a final.**  
Rule: Wait for preview approval; test the full frame, render unlimited in the open UI until stopped, then inspect the saved result.  
Read: [pipeline.md](references/pipeline.md)

### Assets and lifecycle

**AST_01 — Producing study output.**  
Rule: Keep every output in its study folder and process artifacts in its _wip; tell other agents the path.  
Read: [pipeline.md](references/pipeline.md)

**AST_02 — The user declares a study finished.**  
Rule: List milestones, plan then apply checked cleanup, localize dependencies and verify preserved milestone references.  
Read: [study-lifecycle.md](references/study-lifecycle.md)

**AST_03 — Acquiring study assets.**  
Rule: Keep every asset and metadata in that study’s own library for a self-contained handoff.  
Read: [pipeline.md](references/pipeline.md)

**AST_04 — Installing Blender extensions or add-ons.**  
Rule: Use Blender’s extension installer and software folders; delete downloaded installer zips afterward.  
Read: [pipeline.md](references/pipeline.md)

### Agents

**AGT_01 — Code is authored.**  
Rule: Get a fresh review, weigh findings and disclose rejected findings; disclose same-model review when applicable.  
Read: [maintaining.md](references/maintaining.md)

**AGT_02 — Dividing work or handing over.**  
Rule: Follow the user-selected mode, default normal; keep one builder and the documented handoff and review roles.  
Read: [work-modes.md](references/work-modes.md)

**AGT_03 — Reporting a Codex stage.**  
Rule: Train judgement in normal mode; in CPM perform training only when the user opts in.  
Read: [codex-coaching.md](references/codex-coaching.md)

**AGT_04 — Driving Blender or editing study files.**  
Rule: Hold the exclusive machine/file lock; stop and tell the user if another owner holds it; never clear a live or unknown lock.  
Read: [agent-lock.md](references/agent-lock.md)

### Safety

**SAF_01 — Operating the user’s Blender.**  
Rule: Preserve user datablocks; save first when explicitly authorized, otherwise stop before destructive scene operations; rebuild only owned study files.  
Read: [pipeline.md](references/pipeline.md)

**SAF_02 — Planning a heavy scene.**  
Rule: Check GPU VRAM before allocating heavy geometry, dicing or textures.  
Read: [render-settings.md](references/render-settings.md)
