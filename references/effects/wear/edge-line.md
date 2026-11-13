# Edge line

## 1. Overview
The narrow connected dark line set behind a clean rounded edge.
**Use when:** a line follows an arris; broader build-up belongs to dirt.md.

## 2. Layers and node-editor diagram
This is a shading effect, separate from the edge-distance and rounding inputs in
[wear-locations.md](wear-locations.md). Dust sits beneath the line; a chip removes both, with the
existing local junction bridge preserved. Shared stacking: `references/effects/wear/wear.md`.

## 3. Code
- `scripts/blender/effects/wear/edge_line.py`: line profile; `edge_profile.py`: shared edge context.
- `dirt.edge_dirt_masks` returns independently controlled line/dust masks built from that context;
  `dirt.dust_surface(..., line=...)` applies their relative albedos with line priority.
- `concrete_shading.weathered_concrete` assembles them with clean geometry-chip fields.
- Controls: `scripts/controls/effects/edge_dirt_lab.py`, `edge_wear_graph_check.py`.

## 4. Instructions and parameters
### 4.1 Connected arris line
Long runs measured in metres, rare short gaps, near-constant width (about ±15%); variation belongs
mainly in darkness. Fine speckle stays inside the band (RULES MAT_05). Peak a few millimetres behind
the edge, leaving its rounding light. Strongest where water wraps onto an underside; about half
strength on up-facing edges. Continue through junctions rather than making dashed segments.
Inside corners have almost no line; use broader dust there. Exclude clean chip faces with
`1-chip`, preserving the established junction blend. Match band-to-face brightness and dirty
share of the edge against a reference, not just the amount value.

| Parameter | Existing starting point (RULES MAT_03) |
|---|---|
| `line_width` | 0.015 m nominal; about 20 mm is a visual starting estimate |
| `line_amount` | 1.70 mask gain |
| Relative albedo / roughness | ×0.50 / 0.93 |
| Edge setback | few millimetres; limited by local band width |
| Switch | `line_amount=0` disables |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Pencil outline / dashes | width/coverage modulation too strong | continuous run, darkness variation (§4.1) |
| Edge itself black | no light setback | peak behind rounding (§4.1) |
| Dark fresh chips | accumulated line not excluded | chip gate with existing junction bridge (§4.1) |

Generic problems: troubleshooting.md.
