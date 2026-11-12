# Variation: tiling

## 1. Overview
Hiding the repeat of an image map on a continuous surface.

**Use when:** one image map covers a continuous surface and its repeat shows.

## 2. Layers and node-editor diagram
```
 ┌─ VARIATION: TILING — PROCEDURE DIAGRAM ────────────────────────────┐
 │ Coordinates      box_uv UVs                                        │
 │   ▼                                                                │
 │ Decide           ask the user; go on only if a repeat shows        │
 │   ▼                                                                │
 │ Lookups          2–3 offset copies, mixed by one slow noise        │
 │   ▼                                                                │
 │ All maps         albedo, roughness, height: same offsets and noise │
 │   ▼                                                                │
 │ Relief           height ─► Bump ─► Normal                          │
 │   ▼                                                                │
 │ Leftover stains  diffuse part-way to its mean ─► colour            │
 └────────────────────────────────────────────────────────────────────┘
```
- Switch: amount 0 = the plain lookup (RULES MAT_07).

## 3. Code
- `scripts/blender/effects/variation_tiling.py`: `anti_tile(g, texs, …, amount)`; `texs`: step 4.
- Control: `scripts/controls/effects/variation_lab.py --only tiling`.

## 4. Instructions and parameters
1. **Coordinates.** The mesh's real-size UVs (`box_uv`, texture-selection.md).
2. **Decide.** Ask the user first (RULES MAT_06). Not for a featureless map (nothing to repeat) or a scan with
   joints or tie holes (formwork, boards: units; offsets break the joints). Go on only if, on a wall four
   repeats wide, a feature recurs on a grid.
3. **Lookups.** Offset both U and V; noise ~1.5 m, world space. Copies keep the original's settings. Offsets only: a rotation breaks the tangent space. Methods: table.
   **LuxCore:** native Image › Randomized Tiling, 2D Mapping › Randomized UV ([luxcore.md](../renderer/luxcore.md)).
   Check: the grid is gone on the same wall. Undo: amount 0.
4. **All maps together.** Albedo, roughness and height go in one `texs` list, so they share offsets and
   noise and a stain stays on its own relief.
5. **Relief.** Height through a Bump node; a tangent-space normal map seams where copies blend. Check: no
   seams under grazing light.
6. **Leftover stains.** Distinct stains still recur, off the grid: mix the diffuse part-way toward its mean.

| Method | Cost and note |
|---|---|
| 2–3 offset lookups mixed by noise | ×2–3; `anti_tile` |
| Hex tiling | 3 lookups; weight-sharpened blend (Mikkelsen 2022); not built |
| Voronoi-cell offsets | cheap; seams at cell edges unless blended there |

### Generic layers
| Layer | Reference | Note for this material |
|---|---|---|
| Macro tone | variation-surface-marks.md | leftover stains |
| Per-unit offset | variation-per-unit-shading.md | jointed scans, units |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Some rows still in phase | an offset left at zero | offset U and V (step 3) |
| Stain and its relief apart | maps given separate `anti_tile` calls | one `texs` list (step 4) |
| Seams in relief | tangent-space normal map | Bump from height (step 5) |
| Joints broken into a brick pattern | offsets on a jointed scan | treat the panels as units (step 2) |

Generic problems: troubleshooting.md.
