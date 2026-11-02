# Variation: per unit, shading

## 1. Overview
Repeated units (brick, tile, plank, board, glass block, panel, leaf) each get their own tone, roughness,
bump, map offset and normal tilt from one key per unit (RULES MAT_06). Shading only: units that really tilt
or step are variation-per-unit-geometry.md.

**Use when:** a surface is made of separate units that look identical.

## 2. Layers and node-editor diagram
```
 ┌─ VARIATION: PER UNIT, SHADING — PROCEDURE DIAGRAM ─────────────────┐
 │ Key              one value per unit, from how the units are built  │
 │   ▼                                                                │
 │ Per-unit values  tint ─► colour; roughness; bump strength ─► Bump; │
 │                  map offset ─► lookup; normal tilt ─► Normal       │
 └────────────────────────────────────────────────────────────────────┘
```
- Each value is a multiplier around 1 or an offset around 0 (RULES MAT_07); amount 0 = all units equal.

## 3. Code
- `scripts/blender/effects/variation_per_unit_shading.py`: `unit_key`, `set_unit_keys` (step 1),
  `unit_values` (step 2), `random_tone_material` (one tone per leaf).
- Control: `scripts/controls/effects/variation_lab.py --only units`.
- Tiles: their own, `scripts/blender/materials/tile/tile_albedo.py` (`variation`).

## 4. Instructions and parameters
1. **Key.** Pick the source from how the units are built:

   | Units are | `source` | Key |
   |---|---|---|
   | separate objects | `object` | Object Info › Random |
   | copies of a block | `instancer` | Attribute › Instancer, a value stored on each copy (`set_unit_keys`) |
   | pieces of one mesh that share no edges (islands) | `island` | Random per Island (Cycles only) |
   | faces of one welded mesh | `geometry` | Attribute, a face number stored by the build |
   | a grid in the map only | `cell` | hash of floor(coordinate / unit size) |

   `cell` fits an aligned grid only. A bonded layout (running bond, herringbone) takes its unit number from
   its own layout, as tiles do. Check: the key as emission shows each unit flat, neighbours different, and
   all parts of one unit equal.
2. **Per-unit values.** Offset the map, never rotate it: a rotation breaks a tangent-space normal map.
   Normal tilt bends the shading only: faces stay flat and joints straight. Check: no two neighbours match,
   and no unit stands out (spread too wide). Undo: amount 0.

   | Parameter | Value |
   |---|---|
   | Tint | ±2–5 % value |
   | Roughness | ±0.05 |
   | Bump strength | varied per unit |
   | Map offset | random; offsets only |
   | Normal tilt | small, tile and glass block |

### Generic layers
| Layer | Reference | Note for this material |
|---|---|---|
| Concave joint dust | [edge-wear.md](edge-wear.md) › Edge dust | darkest in the corner (RULES MAT_06) |
| Repeat inside one unit | variation-tiling.md | large units |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Identical units | no key, or one key for all | per-unit key (step 1) |
| Parts of one Rhino block differ (frame vs glass) | Object Info › Random per part | `instancer` (step 1) |
| All boards of a welded wall equal | `island` on a welded mesh | `geometry` (step 1) |
| Tilt flat at joints and in raking light | normal tilt is shading only | variation-per-unit-geometry.md |
| Seams in relief on offset units | map rotated | offsets only (step 2) |

Generic problems: troubleshooting.md.
