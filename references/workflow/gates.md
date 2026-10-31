# Gates — when the user must approve
Use when: a stage is finished and its result goes to the user before the next stage starts (RULES GAT_01–04).

A gate is a stop where Claude waits for the user's approval or input. The four gates run in this order;
each needs what the stage before it hands over, and a rejection sends the work back to that stage.
Never pass a gate on your own judgement, and never start the next stage while the user has not answered.

| Gate | After | Before | Rejected: back to |
|---|---|---|---|
| GAT_01 research | sources gathered | analysis and method choice | gathering sources |
| GAT_02 model | Rhino model finished | import into Blender | Rhino modelling |
| GAT_03 materials | first full build | any look round | the materials in doubt |
| GAT_04 final | look rounds approved | the final render | the look round |

Each gate runs the same steps: **Needs** (what must be ready), **Show**, **Wait**, then **Approved** (what
the approval covers) or **Rejected** (how to go back).

## GAT_01 Research gate
Both modes. A quick lookup during a build (one API detail, one trap) needs no gate.

1. **Needs:** the question and the gathered sources (RULES RES_01), not yet analysed.
2. **Show:** the question; a source list, one line each: what it is, link or path, what it should answer;
   the gaps still open.
3. **Wait.** The user often adds links: read them like any other source.
4. **Approved:** analyse, compare workflows and choose.
   **Rejected or gaps named:** gather more sources and show the list again.

## GAT_02 Model gate
Rework in Rhino is cheap; a look-dev round on wrong geometry is not.

1. **Needs:** the finished Rhino model with its checks passed (pipeline.md › Phase 1); from a reference
   image, the edge overlay checked (`scripts/research/edge_overlay.py`).
2. **Show:** viewport captures and a list of what was modelled and what was left out.
3. **Wait** for the user to approve the geometry.
4. **Approved:** import into Blender.
   **Rejected:** fix the model in Rhino, recapture, show again. Nothing goes to Blender before approval.

## GAT_03 Material gate
Both modes.

1. **Needs:** the first build: camera and light set, first-pass materials on every layer.
2. **Show:**
   - a material schedule, per layer: material, source (Poly Haven asset, procedural or own file), real
     size and direction, target albedo and roughness, the reference it matches;
   - a first-pass render at the final camera;
   - native crops of each material beside the reference (RULES VAL_01);
   - 2–3 candidates side by side for any material in doubt.
3. **Wait** for approval.
4. **Approved:** look rounds start; they only tune approved materials.
   **Rejected:** rebuild the materials named and show the gate again. A material swap after approval
   comes back to this gate.

## GAT_04 Final render gate
1. **Preview.** Render a preview, show it, state the final's resolution, time budget and expected noise,
   and wait for approval. A material or light change after approval means a new preview.
2. **Full-frame test.** Before any long or unattended final, render a short full-frame test with exactly
   the final's settings, raw and denoised, and look at every surface, not only the one under discussion.
   Bring known risks and their tested fixes to the user before launch; a fix is not withheld because it is
   not yet approved.
   Check: no surface shows a defect the preview did not. A defect found: fix it, back to step 1.
3. **Launch** in the open Blender UI so the user watches it live; headless renders are for tests, controls
   and previews. Set no time or sample limit: the final renders until the user stops it, and saving and
   denoising run on stop. A halt time is fixed when the session starts and a finished render cannot be
   resumed, so a limit can only cut the user's choice short. Mechanics:
   [pipeline.md › Final render in the open UI](../scene/pipeline.md#final-render-in-the-open-ui-rules-gat_04).
4. **Saved result.** Look at the saved file, every surface, before calling it done or sending it anywhere.
   A defect: report it; the next final starts again at step 1.
