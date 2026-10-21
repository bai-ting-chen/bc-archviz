# House rules

## Governance

When: GOV_01 — recording reusable knowledge.
Rule: Keep scene-independent methods, constants, traps and taste; scene results belong in study notes.
Read: references/maintaining.md (before publishing knowledge).

When: GOV_02 — working with skill and project files.
Rule: Publish only generic skill code and method; keep project data local and unnamed here.
Read: references/maintaining.md (before editing the skill).

When: GOV_03 — synchronizing this skill.
Rule: Pull before editing, use the per-clone identity, and leave outstanding receiving-machine actions with pushes.
Read: references/maintaining.md (before synchronizing).

When: GOV_04 — extending code or documents.
Rule: Keep one module per job and one authority per helper; use focused functions and topic references.
Read: references/maintaining.md (before extending helpers).

## Renderer

When: REN_01 — choosing an implementation.
Rule: Prefer editable Blender-native methods; declare external fallbacks, subject to REN_03.
Read: references/caustics.md (before choosing a method).

When: REN_02 — choosing a transport method.
Rule: Prefer unbiased transport, then native physical approximations, then external tools; disclose every bias or fake.
Read: references/caustics.md (before choosing transport).

When: REN_03 — detailed caustics or heavy refraction carries the shot.
Rule: Use LuxCore PATH with light tracing; otherwise default to Cycles and disclose the external engine.
Read: references/luxcore.md (before selecting the renderer).

## Research

When: RES_01 — building a new technique.
Rule: Research physics and full-resolution source evidence, compare workflows, cite and prove the chosen method.
Read: references/research-loop.md (before building).

When: RES_02 — sources are gathered for a new technique.
Rule: Show the question, sources and gaps; wait for user links before analysis; quick API lookups are exempt.
Read: references/work-modes.md (before analysing research).

When: RES_03 — making a look decision or recreating a reference.
Rule: Shortlist the reference library; solve the reference camera first and adjust exposure last.
Read: references/reference-library.md (before look decisions).

## Pipeline

When: PIP_01 — transferring Rhino geometry.
Rule: Keep source Rhino documents read-only; author materials, lighting, camera look and rendering in Blender.
Read: references/pipeline.md (before importing).

## Lighting and camera

When: LGT_01 — setting lights or camera.
Rule: Use photometric units and physical camera exposure; count each emitter once, white-balance and keep verticals parallel.
Read: references/lighting-camera.md (before lighting).

When: LGT_02 — lighting daylight.
Rule: Use a matching HDRI as the sole natural source; declare Sky Texture fallback only if none fits.
Read: references/lighting-camera.md (before setting daylight).

## Materials

When: MAT_01 — authoring surface materials.
Rule: Use all applicable maps, real-scale directional UVs and physically plausible surface ranges.
Read: references/materials/physical-ranges.md (before authoring materials).

When: MAT_02 — authoring edge damage.
Rule: Keep dirty-edge shading distinct from geometric chips.
Read: references/materials/edge-wear.md (before authoring wear).

When: MAT_03 — sizing visible detail.
Rule: Size from the final shot; pair every close-up with a native final-view crop.
Read: references/materials/scale.md (before tuning detail).

When: MAT_04 — features are sub-pixel.
Rule: Model their aggregate appearance and ask before building micro-geometry.
Read: references/materials/scale.md (before building detail).

When: MAT_05 — authoring natural surface marks.
Rule: Make marks patchy, able to disappear, with physically shaped extents.
Read: references/materials/variation.md (before authoring marks).

When: MAT_06 — using repeated units or tiled maps.
Rule: Add per-unit variation, hide repeats and fade concave-joint dust outward from corners in the first pass.
Read: references/materials/variation.md (before building repeated surfaces).

## Validation

When: VAL_01 — judging material or effect character.
Rule: Compare native-resolution crops beside the reference and repeat after changing that feature.
Read: references/validation.md (before declaring a match).

When: VAL_02 — claiming a feature works.
Rule: Prove it with feature-off and repeated-baseline renders, noise-floor measurements and inspected diffs.
Read: references/validation.md (before claiming proof).

When: VAL_03 — measuring the rendered look.
Rule: Measure renderer-written display PNGs; use linear energy data only for physical calibration controls.
Read: references/validation.md (before measuring).

When: VAL_04 — diagnosing odd behaviour.
Rule: Bisect in a minimal control scene before tuning the full scene.
Read: references/validation.md (before debugging).

## Approval gates

When: GAT_01 — a Rhino study model is ready.
Rule: Show captures and modelled/omitted items; wait for geometry approval before import.
Read: references/pipeline.md (before importing the model).

When: GAT_02 — the first full material build is ready.
Rule: Show schedule, final-camera render, native reference crops and uncertain candidates; wait for approval and re-gate swaps.
Read: references/work-modes.md (before look rounds).

When: GAT_03 — launching a final.
Rule: Wait for preview approval; test the full frame, render unlimited in the open UI until stopped, then inspect the saved result.
Read: references/pipeline.md (before launching finals).

## Assets and lifecycle

When: AST_01 — producing study output.
Rule: Keep every output in its study folder and process artifacts in its _wip; tell other agents the path.
Read: references/pipeline.md (before producing output).

When: AST_02 — the user declares a study finished.
Rule: List milestones, plan then apply checked cleanup, localize dependencies and verify preserved milestone references.
Read: references/study-lifecycle.md (before closing a study).

When: AST_03 — acquiring study assets.
Rule: Keep every asset and metadata in that study’s own library for a self-contained handoff.
Read: references/pipeline.md (before acquiring assets).

When: AST_04 — installing Blender extensions or add-ons.
Rule: Use Blender’s extension installer and software folders; delete downloaded installer zips afterward.
Read: references/pipeline.md (before installing software).

## Agents

When: AGT_01 — code is authored.
Rule: Get a fresh review, weigh findings and disclose rejected findings; disclose same-model review when applicable.
Read: references/maintaining.md (before accepting code).

When: AGT_02 — dividing work or handing over.
Rule: Follow the user-selected mode, default normal; keep one builder and the documented handoff and review roles.
Read: references/work-modes.md (before dividing work).

When: AGT_03 — reporting a Codex stage.
Rule: Train judgement in normal mode; in CPM perform training only when the user opts in.
Read: references/codex-coaching.md (before reporting).

When: AGT_04 — driving Blender or editing study files.
Rule: Hold the exclusive machine/file lock; stop and tell the user if another owner holds it; never clear a live or unknown lock.
Read: references/agent-lock.md (before driving Blender).

## Safety

When: SAF_01 — operating the user’s Blender.
Rule: Preserve user datablocks; save first when explicitly authorized, otherwise stop before destructive scene operations; rebuild only owned study files.
Read: references/pipeline.md (before scene operations).

When: SAF_02 — planning a heavy scene.
Rule: Check GPU VRAM before allocating heavy geometry, dicing or textures.
Read: references/render-settings.md (before building a heavy scene).
