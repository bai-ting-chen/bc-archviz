# Gates — when the user must approve
Use when: a stage is finished and its result goes to the user before the next stage (RULES GAT_01–04).

At each gate: show, wait for the user, and start the next stage only after approval. A rejection sends the
work back to the stage before the gate.

## GAT_01 Research gate
Before analysing the gathered sources (RULES RES_01), show the question, the source list (one line each: what
it is, link or path, what it should answer) and the open gaps. The user often adds links: read them like any
other source. Approved: analyse, compare workflows, choose. A quick lookup during a build needs no gate.

## GAT_02 Model gate
After the Rhino model passes its checks (pipeline.md › Phase 1; from a reference image, also
`scripts/research/edge_overlay.py`), show viewport captures and what was modelled and left out.
Approved: import into Blender. Rejected: fix in Rhino and show again; rework in Rhino is cheap, a look round
on wrong geometry is not.

## GAT_03 Material gate
After the first build (camera, light, first-pass materials on every layer), show:
- a material schedule, per layer: material, source (Poly Haven, procedural or own file), real size and
  direction, target albedo and roughness, the reference it matches;
- a first-pass render at the final camera;
- native crops of each material beside the reference (RULES VAL_01);
- the other candidates (RULES MAT_10) side by side for any material in doubt.

Approved: look rounds tune only approved materials. A material swap later comes back to this gate.

## GAT_04 Final render gate
**Step 1. Preview.** Show it with the final's resolution, time budget and expected noise; wait for approval.
A material or light change after approval means a new preview.

**Step 2. Full-frame test.** Before a long or unattended final, render a short full frame with exactly the
final's settings, raw and denoised; look at every surface. Bring known risks and their tested fixes to the
user before launch. A defect: fix it, back to step 1.

**Step 3. Launch** in the open Blender UI, with no time or sample limit: the user watches and stops it, and
saving and denoising run on stop (a halt time cannot be changed once rendering starts, nor a finished render
resumed). Headless is for tests and previews. Mechanics:
[pipeline.md › Final render in the open UI](../scene/pipeline.md#final-render-in-the-open-ui-rules-gat_04).

**Step 4. Saved result.** Look at every surface of the saved file before calling it done or sending it.
