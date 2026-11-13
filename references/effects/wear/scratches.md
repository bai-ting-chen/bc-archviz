# Scratches

## 1. Overview
Fine crossing scratches, with procedural strokes, raw scans and the legacy hybrid option.

## 2. Layers and node-editor diagram
Scratch factors drive roughness and a slight groove normal. Source comparison is still undecided;
judge in a close scene. The current legacy hybrid placeholder is unchanged and does not use the
active region-times-interior composer. Family sources: `references/effects/wear/wear.md`;
locations: [wear-locations.md](wear-locations.md).

## 3. Code
`scripts/blender/effects/wear/scratches.py`: `scratches_field`, `scratch_hybrid`.
Select `WearLayer(source=...)` under key `scratches` through `wear.py`.
Control: `scripts/controls/effects/surface_wear_lab.py`, `surface_wear_graph_check.py`.

## 4. Instructions and parameters
### 4.1 Crossing strokes
Size thin strokes from final-view pixels (RULES MAT_03), vary lengths and independent phases.
Use grazing illumination or reflection of a bright area to resolve glints on painted/brushed metal.
Raw masks cross a rotated second copy. The held hybrid modulates procedural strokes by a scan
in the existing 0.7–1.0 range; this is the explicit legacy exception, not a newly judged source.
Missing scan uses procedural fallback and the shared missing-id log.

| Parameter | Existing setting |
|---|---|
| Key / current default | `scratches` / `hybrid` legacy; undecided |
| Scan | `vdekdjrc`, 0.5 m, 4K `_Mask` |
| Procedural directions | 13, 61, 112, 157 degrees |
| Relative lengths | 0.6, 1.1, 0.35, 0.85 × `scale_m` |
| `scale_m` / `scratch_width_m` | 0.25 m / 0.003 m; size resolved strokes from shot |
| Raw crossing | +90 degrees, offset (0.37, 0.19) UV tiles |
| Effect | roughness ×0.2 at factor 1; inverted bump 0.15 mm, strength 0.4 |
| Switch | layer `enabled`; `amount=0` disables |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Single-direction strokes | one orientation only | independent crossing fields / rotated raw copy (§4.1) |
| No glints | light/camera cannot resolve grooves | close view and bright grazing reflection (§4.1) |
| Repeated cross motifs | crossed scan pattern is recognizable | keep undecided; compare procedural closely (§4.1) |

Generic problems: troubleshooting.md.
