# Study documents for agent exchange

The brief, bug brief, report and review formats are ai-work-modes › exchange.md. This file adds
what a study needs on top. Run folders live in the study's `_wip/codex/` (`--out <study>\_wip\codex\<tag>`).

## Brief additions
- **Helpers:** Reads lists [blender-python-helpers.md](../scene/blender-python-helpers.md) and the
  interface in real units; the brief names the camera(s) the images use.
- **Tools:** a run that drives Blender or Rhino launches with `--needs blender` / `--needs rook` and `--lock "<what it drives>"`.
- **Textures:** when the run applies or swaps a texture, the attach workflow: real size from the
  asset's metadata; Rhino UVs discarded and `archviz.box_uv(obj, size_m)` on the final mesh
  (`directional_uv` only for an asked grain axis); no stretch (UV area × size² ≈ world area, feature
  size in a native crop); Image Texture through a named UV Map, Non-Color for data maps; colour by
  gains only, never a flat-colour Mix.
- **Checks line.** A resumed builder carries the proof habits of earlier stages (fingerprints, hash,
  area and readback audits) into simple stages, and a geometry import then takes three times as long.
  For imports, previews and plain look rounds the brief says: "Checks: look at each image, measure
  only what the items name; no audits unless something looks wrong."
- **Render budget:** a control that builds its own scene renders on the GPU (api-traps); probes are
  small and packed (several outputs in R/G/B of one render); sections run alone (`--only`); slow
  convergence comparisons sit behind `--full`. Never rerun controls of modules the task did not touch.

## Report additions
One line per image ("this shows X"), and the deciding numbers with the control's noise floor.

## Source list (for the research gate, `_wip/research/<topic>-sources.md`)
- the question in one sentence;
- one line per source: what it is, link or path, what it should answer (mechanism, measured
  data, implementation, reference look);
- gaps: what no source covers yet;
- the user's added links, marked as theirs.

## Material schedule (for the material gate, `_wip/materials-schedule.md`)
One row per layer: material, source (Poly Haven asset id, procedural, own file), real size and
direction, target albedo and roughness, the reference crop it matches, and "in doubt" with the
candidate sheet.

## Research note (Codex → Claude in CPM, `_wip/research/<topic>.md`, after the gate)
- the question; the mechanism with numbers and sources (papers, measured data);
- 2–4 workflows compared on 1–2 criteria, with cost (time, VRAM, cache);
- a recommendation and what it approximates;
- full-resolution evidence: frames or crops saved beside the note, not only text.
