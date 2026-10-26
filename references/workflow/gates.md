# Gates — when the user must approve

A gate is a stop where Claude waits for the user's approval or input.

Gates in workflow order: research GAT_01, model GAT_02, materials GAT_03, final preview GAT_04.

See [pipeline.md for GAT_02](../scene/pipeline.md#gat_02-procedure#gat_02-procedure) and [pipeline.md for GAT_04](../scene/pipeline.md#gat_04-procedure#gat_04-procedure).

## GAT_01 procedure

**Research gate** (both modes). After gathering sources and before analysing them, stop and
   show the user: the question, a source list (one line each: what it is, link or path, what it
   should answer) and the gaps still open. Wait — the user often adds links; read them like any
   other source (RULES RES_01). Then analyse, compare workflows and choose. A quick lookup during a
   build (one API detail, one trap) needs no gate.

## GAT_03 procedure

**Material gate** (both modes). After the first build (camera and light set, first-pass
    materials on every layer) and before any look round, stop and show the user: a material
    schedule (per layer: material, source — Poly Haven asset, procedural or own file — real size
    and direction, target albedo and roughness, the reference it matches), a first-pass render at
    the final camera, native crops of each material beside the reference (VAL_01), and 2–3 candidates
    side by side for any material in doubt. Wait for approval; the look rounds only tune approved
    materials, and a material swap after approval comes back to this gate.
