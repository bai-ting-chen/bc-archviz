## House rules

### Governance

**GOV_01 — What Goes Into The Skill**  
Rule: Keep scene-independent methods, constants, traps, taste and generic code; scene results belong in study notes, and project data stays local and unnamed in this skill set. Write for new studies only: treat every existing study as finished, with no code or wording kept for a past one. One-time operations and their consequences go to the user in chat, never into the skill. The skill is self-contained: it runs with an empty CLAUDE.md and memory; machine files may name the skill, never its files or sections, and skill rules live only in the skill.  
Read: [skill-maintaining.md](references/workflow/skill-maintaining.md)

**GOV_02 — Synchronizing This Skill**  
Rule: Before editing, pull with the per-clone identity and apply MIGRATE.md if present. Write MIGRATE.md for any change that can break another clone.  
Read: [skill-maintaining.md](references/workflow/skill-maintaining.md)

**GOV_03 — Extending Code Or Documents**  
Rule: Keep one module per job and one authority per helper; use focused, readable functions and topic references; prove a refactor by reproducing a saved control baseline exactly. A reference that documents one script shares its name (`study-close.md` ↔ `study_close.py`). Before revising a file, settle its purpose with the user and propose the smallest design that serves it; add a safeguard only for a failure a review has shown.  
Read: [skill-maintaining.md](references/workflow/skill-maintaining.md)

### Pipeline

**PIP_01 — Transferring Rhino Geometry**  
Rule: Keep source Rhino documents read-only; author materials, lighting, camera look and rendering in Blender.  
Read: [pipeline.md](references/scene/pipeline.md)

**PIP_02 — A Phase Check Fails**  
Rule: Stop the phase and report what failed and what was tried; never carry a failed check into the next phase.  
Read: [pipeline.md](references/scene/pipeline.md)

### Approval Gates

A gate is a stop where Claude waits for your approval or input. Gates are numbered in the order they happen in a study.

**GAT_01 — Research Sources Are Ready**  
Rule: Show the question, the sources and the gaps; wait for the user's links before analysis; quick API lookups are exempt.  
Read: [gates.md](references/workflow/gates.md)

**GAT_02 — A Rhino Study Model Is Ready**  
Rule: Show captures and modelled/omitted items; wait for geometry approval before import.  
Read: [gates.md](references/workflow/gates.md)

**GAT_03 — The First Full Material Build Is Ready**  
Rule: Show schedule, final-camera render, native reference crops and uncertain candidates; wait for approval and re-gate swaps.  
Read: [gates.md](references/workflow/gates.md)

**GAT_04 — Launching A Final**  
Rule: Wait for preview approval; test the full frame, render unlimited in the open UI until stopped, then inspect the saved result.  
Read: [gates.md](references/workflow/gates.md)

### Research

**RES_01 — Building A New Technique**  
Rule: Research physics and full-resolution source evidence, compare workflows, cite and prove the chosen method.  
Read: [research-loop.md](references/research/research-loop.md)

**RES_02 — Making A Look Decision Or Recreating A Reference**  
Rule: Shortlist the reference library; solve the reference camera first and adjust exposure last.  
Read: [reference-library.md](references/research/reference-library.md), [reference-match.md](references/scene/reference-match.md)

### Renderer Choice

**REN_01 — Choosing An Implementation**  
Rule: Prefer editable Blender-native, unbiased methods, then native physical approximations, then external tools; declare every external tool, bias or fake. REN_02 is the one standing exception.  
Read: [renderer-choice.md](references/renderer/renderer-choice.md)

**REN_02 — Use LuxCore Only When Detailed Caustics Or Heavy Refraction Carries The Shot**  
Rule: Otherwise render in Cycles; say it is an external engine when you switch.  
Read: [renderer-choice.md](references/renderer/renderer-choice.md), [luxcore.md](references/renderer/luxcore.md)

### Lighting And Camera

**LGT_01 — Setting Lights Or Camera**  
Rule: Use photometric units and physical camera exposure; count each emitter once, white-balance and keep verticals parallel.  
Read: [lighting/index.md](references/scene/lighting/index.md), [camera.md](references/scene/camera/camera.md)

**LGT_02 — Lighting Daylight**  
Rule: Use a matching HDRI as the sole natural source; declare Sky Texture fallback only if none fits.  
Read: [hdri.md](references/scene/lighting/hdri.md)

### Materials

**MAT_01 — Authoring Surface Materials**  
Rule: Use all applicable maps, real-scale directional UVs and physically plausible surface ranges.  
Read: [physical-ranges.md](references/materials/physical-ranges.md)

**MAT_02 — Sizing Visible Detail**  
Rule: Size every feature from the final shot and pair every close-up with a native final-view crop; model sub-pixel features by their aggregate appearance and ask before building micro-geometry.  
Read: [scale.md](references/materials/scale.md)

**MAT_03 — Authoring Natural Surface Marks**  
Rule: Make marks patchy, able to disappear, with physically shaped extents.  
Read: [wear-locations.md](references/effects/wear/wear-locations.md)

**MAT_04 — Using Repeated Units Or Tiled Maps**  
Rule: Add per-unit variation and hide repeats in the first pass; ask the user before adding stochastic tiling to a material.  
Read: [variation-per-unit-shading.md](references/effects/variation-per-unit-shading.md), [variation-per-unit-geometry.md](references/effects/variation-per-unit-geometry.md), [variation-tiling.md](references/effects/variation-tiling.md)

**MAT_05 — Composing Material Layers**  
Rule: Build each look layer as its own term — colour and roughness as multipliers around 1, height as its own displacement or bump term — and give each layer an on/off switch in its builder, so the user and every control can turn it off.  
Read: [index.md](references/materials/index.md)

**MAT_06 — Choosing A Material Method Or File**  
Rule: Choose from the router's decision table and say which method and file you chose and why; no row fits → RES_01.  
Read: [index.md](references/materials/index.md)

### Validation

**VAL_01 — Claiming A Feature Works**  
Rule: Prove it with feature-off and repeated-baseline renders, noise-floor measurements and inspected diffs.  
Read: [validation.md](references/review/validation.md)

**VAL_02 — Judging And Ending A Look Round**  
Rule: Write the match list before the first round. Each round makes one change for one failing line and is kept only when that line improves and no passing line gets worse in native-resolution crops; otherwise return to the best version. Done when every line passes with exposure set last; after 2 rounds in a row reverted, change the approach; after 3 rounds without a new passing line, stop, record why and show the user the best version.  
Read: [validation.md](references/review/validation.md)

### Assets And Lifecycle

**AST_01 — Keeping A Study Self-Contained**  
Rule: Keep every output, process artifact (in `_wip/`) and acquired asset with its metadata in that study's own folder and library, so it hands over self-contained; tell other agents the path.  
Read: [pipeline.md](references/scene/pipeline.md), [sources.md](references/workflow/sources.md)

**AST_02 — The User Declares A Study Finished**  
Rule: Name the final scene, ask the user for milestone images, check the final scene's references, plan then apply the cleanup of known-safe items only, and mark the study with closed.md.  
Read: [study-close.md](references/workflow/study-close.md)

**AST_03 — Naming Study Files And Folders**  
Rule: Name new files and folders in lowercase kebab-case and Python files in snake_case; `_wip/` keeps its name.  
Read: [pipeline.md](references/scene/pipeline.md)

**AST_04 — Proposing Materials And Shop Assets**  
Rule: Send every candidate (textures, plants, models) for the user's review in one list across all sources (Poly Haven, Quixel, Maxtree and others), preferred first, each with its source, id, real size and why it fits; list only real fits, so one fit is a list of one. Build or download only the user's picks. Quixel is free: the picks approve the agent downloading them through the user's Fab sign-in, under the free Professional licence of the Fab Standard License. Maxtree is paid: the user buys and downloads.  
Read: [texture-selection.md](references/materials/texture-selection.md), [sources.md](references/workflow/sources.md)

### Safety

**SAF_01 — Operating The User’s Blender**  
Rule: Preserve user datablocks; save first when explicitly authorized, otherwise stop before destructive scene operations; rebuild only owned study files.  
Read: [pipeline.md](references/scene/pipeline.md)
