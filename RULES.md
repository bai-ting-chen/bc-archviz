## House rules

### Governance

**GOV_01 — Recording Reusable Knowledge**  
Rule: Keep scene-independent methods, constants, traps and taste; scene results belong in study notes.  
Read: [skill-maintaining.md](references/workflow/skill-maintaining.md)

**GOV_02 — Working With Skill And Project Files**  
Rule: Publish only generic skill code and method; keep data specific to each project local and unnamed in this skill set.  
Read: [skill-maintaining.md](references/workflow/skill-maintaining.md)

**GOV_03 — Synchronizing This Skill**  
Rule: Pull before editing, use the per-clone identity, and leave outstanding receiving-machine actions with pushes.  
Read: [skill-maintaining.md](references/workflow/skill-maintaining.md)

**GOV_04 — Extending Code Or Documents**  
Rule: Keep one module per job and one authority per helper; use focused, readable functions and topic references; prove a refactor by reproducing a saved control baseline exactly.  
Read: [skill-maintaining.md](references/workflow/skill-maintaining.md)

### Agent Cooperation

**AGT_02 — Choosing A Working Mode**  
Rule: At the start of each project the user chooses Normal or CPM mode (Codex Priority Mode: Claude directs, Codex does all hands-on work), and the mode holds until the user switches or the round ends. Only one Codex builder works at a time, and each handoff follows the documented roles.  
Read: [work-modes.md](references/workflow/work-modes.md)

**AGT_01 — Code Review**  
Rule: Every code change gets a fresh review. Weigh each finding, and disclose any finding you reject. If the reviewer is the same model that wrote the code, say so.  
Read: [skill-maintaining.md](references/workflow/skill-maintaining.md)

**AGT_03 — Codex Reports On A Finished Stage**  
Rule: In Normal mode Claude trains its own judgement from Codex's reports. In CPM, training runs only when the user asks for it.  
Read: [codex-coaching.md](references/review/codex-coaching.md)

**AGT_04 — File Ownership**  
Rule: Only one agent may own Blender, Rhino, scripts or any project or study file at a time; the owner holds the machine lock. If another agent holds it, stop and tell the user. Never delete a lock that may still be live or whose owner is unknown.  
Read: [agent-lock.md](references/workflow/agent-lock.md)

### Pipeline

**PIP_01 — Transferring Rhino Geometry**  
Rule: Keep source Rhino documents read-only; author materials, lighting, camera look and rendering in Blender.  
Read: [pipeline.md](references/scene/pipeline.md)

### Approval Gates

A gate is a stop where Claude waits for your approval or input. Gates are numbered in the order they happen in a study.

**GAT_01 — Research Sources Are Ready**  
Rule: Show the question, the sources and the gaps; wait for the user's links before analysis; quick API lookups are exempt.  
Read: [gates.md](references/workflow/gates.md)

**GAT_02 — A Rhino Study Model Is Ready**  
Rule: Show captures and modelled/omitted items; wait for geometry approval before import.  
Read: [pipeline.md](references/scene/pipeline.md)

**GAT_03 — The First Full Material Build Is Ready**  
Rule: Show schedule, final-camera render, native reference crops and uncertain candidates; wait for approval and re-gate swaps.  
Read: [gates.md](references/workflow/gates.md)

**GAT_04 — Launching A Final**  
Rule: Wait for preview approval; test the full frame, render unlimited in the open UI until stopped, then inspect the saved result.  
Read: [pipeline.md](references/scene/pipeline.md)

### Research

**RES_01 — Building A New Technique**  
Rule: Research physics and full-resolution source evidence, compare workflows, cite and prove the chosen method.  
Read: [research-loop.md](references/research/research-loop.md)

**RES_03 — Making A Look Decision Or Recreating A Reference**  
Rule: Shortlist the reference library; solve the reference camera first and adjust exposure last.  
Read: [reference-library.md](references/research/reference-library.md)

### Renderer Choice

**REN_01 — Choosing An Implementation**  
Rule: Prefer editable Blender-native methods; declare external fallbacks, subject to REN_03.  
Read: [renderer-choice.md](references/renderer/renderer-choice.md)

**REN_02 — Choosing A Transport Method**  
Rule: Prefer unbiased transport, then native physical approximations, then external tools; disclose every bias or fake.  
Read: [renderer-choice.md](references/renderer/renderer-choice.md)

**REN_03 — Use LuxCore Only When Detailed Caustics Or Heavy Refraction Carries The Shot**  
Rule: Use LuxCore PATH with light tracing; otherwise default to Cycles and disclose the external engine.  
Read: [renderer-choice.md](references/renderer/renderer-choice.md)

### Lighting And Camera

**LGT_01 — Setting Lights Or Camera**  
Rule: Use photometric units and physical camera exposure; count each emitter once, white-balance and keep verticals parallel.  
Read: [lighting-camera.md](references/scene/lighting-camera.md)

**LGT_02 — Lighting Daylight**  
Rule: Use a matching HDRI as the sole natural source; declare Sky Texture fallback only if none fits.  
Read: [lighting-camera.md](references/scene/lighting-camera.md)

### Materials

**MAT_01 — Authoring Surface Materials**  
Rule: Use all applicable maps, real-scale directional UVs and physically plausible surface ranges.  
Read: [physical-ranges.md](references/materials/physical-ranges.md)

**MAT_02 — Authoring Edge Damage**  
Rule: Keep dirty-edge shading distinct from geometric chips.  
Read: [edge-wear.md](references/effects/edge-wear.md)

**MAT_03 — Sizing Visible Detail**  
Rule: Size from the final shot; pair every close-up with a native final-view crop.  
Read: [scale.md](references/materials/scale.md)

**MAT_04 — Features Are Sub-Pixel**  
Rule: Model their aggregate appearance and ask before building micro-geometry.  
Read: [scale.md](references/materials/scale.md)

**MAT_05 — Authoring Natural Surface Marks**  
Rule: Make marks patchy, able to disappear, with physically shaped extents.  
Read: [variation.md](references/effects/variation.md)

**MAT_06 — Using Repeated Units Or Tiled Maps**  
Rule: Add per-unit variation, hide repeats and fade concave-joint dust outward from corners in the first pass.  
Read: [variation.md](references/effects/variation.md)

**MAT_07 — Composing Material Layers**  
Rule: Build each look layer as its own term — colour and roughness as multipliers around 1, height as its own displacement or bump term — so each can be switched off for a control.  
Read: [index.md](references/materials/index.md)

**MAT_08 — Ordering Geometry Fields**  
Rule: Measure geometry fields (edge, leak, proximity distances) on the clean mesh, before any modifier that moves or cracks it.  
Read: [edge-wear.md](references/effects/edge-wear.md)

### Validation

**VAL_01 — Judging Material Or Effect Character**  
Rule: Compare native-resolution crops beside the reference and repeat after changing that feature.  
Read: [validation.md](references/review/validation.md)

**VAL_02 — Claiming A Feature Works**  
Rule: Prove it with feature-off and repeated-baseline renders, noise-floor measurements and inspected diffs.  
Read: [validation.md](references/review/validation.md)

**VAL_03 — Measuring The Rendered Look**  
Rule: Measure renderer-written display PNGs; use linear energy data only for physical calibration controls.  
Read: [validation.md](references/review/validation.md)

**VAL_04 — Diagnosing Odd Behaviour**  
Rule: Bisect in a minimal control scene before tuning the full scene.  
Read: [validation.md](references/review/validation.md)

### Assets And Lifecycle

**AST_01 — Producing Study Output**  
Rule: Keep every output in its study folder and process artifacts in its _wip; tell other agents the path.  
Read: [pipeline.md](references/scene/pipeline.md)

**AST_02 — The User Declares A Study Finished**  
Rule: List milestones, plan then apply checked cleanup, localize dependencies and verify preserved milestone references.  
Read: [study-lifecycle.md](references/workflow/study-lifecycle.md)

**AST_03 — Acquiring Study Assets**  
Rule: Keep every asset and metadata in that study’s own library for a self-contained handoff.  
Read: [pipeline.md](references/scene/pipeline.md)

**AST_04 — Installing Blender Extensions Or Add-Ons**  
Rule: Use Blender’s extension installer and software folders; delete downloaded installer zips afterward.  
Read: [pipeline.md](references/scene/pipeline.md)

### Safety

**SAF_01 — Operating The User’s Blender**  
Rule: Preserve user datablocks; save first when explicitly authorized, otherwise stop before destructive scene operations; rebuild only owned study files.  
Read: [pipeline.md](references/scene/pipeline.md)

**SAF_02 — Planning A Heavy Scene**  
Rule: Check GPU VRAM before allocating heavy geometry, dicing or textures.  
Read: [render-settings.md](references/renderer/render-settings.md)
