# Cracks

## 1. Overview
Cracks from openings or outside edges, continuing across faces, with a core, halo and shallow groove.
**Use when:** material splits; removed fragments and flaked coating belong to chipping.md.

## 2. Layers and node-editor diagram
Opening or edge origins seed jagged paths across a face. Core and halo change colour; the
shallow groove changes normal. Edge origin is a location input, not a separate kind of crack.
Field capture: [wear-locations.md](wear-locations.md). Family assembly:
`references/effects/wear/wear.md`.

## 3. Code
- `scripts/blender/effects/wear/cracks.py`: `CRACK`, `crack_masks`, `add_cracks`, `apply_crack_masks`.
- `edge_cracks.py`: `EDGE_CRACK`, `edge_crack_edges`, `add_edge_cracks`.
- `crack_ribbon.py`: shared `crooked_ribbon_masks`; both origin builders use this one path helper.
- `edge_crack_edges` captures clean mesh before dicing/displacement. `amount=0` disables each layer.
- Controls: `scripts/controls/effects/edge_wear_lab.py`, `edge_wear_graph_check.py`.

## 4. Instructions and parameters
### 4.1 Opening and edge cracks
Never straight: kink at irregular steps, add fine wobble and short branches, taper/vary width.
Opening cracks head out of re-entrant corners. Edge cracks are short sparse paths roughly square
into the face. Keep a few; symmetric opposite pairs read as one long line. At room scale a true
hairline vanishes; a dirt-darkened core and halo over a shallow groove carries the reading.
Glazed tile cracking is a separate per-tile network in `references/materials/tile/tiles.md`.

| Parameter | Starting point (RULES MAT_03) |
|---|---|
| Opening direction / length | 45 degrees ±15 / 0.4–1 m |
| Edge length | approximately 0.05–0.20 m |
| Opening core / halo / depth | 0.005 / 0.020 / 0.003 m |
| Edge core / halo / depth | 0.0016 / 0.006 / 0.0008 m |
| Variation | irregular jag, wobble, branches and tapered width |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Two cracks read as one | opposite/symmetric pair | sparse asymmetric origins (§4.1) |
| Drawn line | straight uniform path | kink, wobble, branch and taper (§4.1) |
| Crack disappears | true hairline below pixel size | size core/halo from shot (§4.1) |

Generic problems: troubleshooting.md.
