# Variation: per unit, geometry

## 1. Overview
Repeated units that really tilt and step in or out. Tone and roughness per unit:
[variation-per-unit-shading.md](variation-per-unit-shading.md).

**Use when:** the unevenness must show at the joints or in raking light, where a shading tilt reads flat.

## 2. Layers and node-editor diagram
```
 ┌─ VARIATION: PER UNIT, GEOMETRY — PROCEDURE DIAGRAM ──────────────────────┐
 │ Where            Rhino or Blender, from how the units are modelled       │
 │   ▼                                                                      │
 │ Excursion        tilt + step per unit, one size for both routes          │
 │   ├─► In Rhino    units arrayed: instance transforms, then import        │
 │   │               ─► shading key `instancer` / `object`                  │
 │   └─► In Blender  one surface: import, then cut, move, weld; face number │
 │                   ─► shading key `geometry`                              │
 └──────────────────────────────────────────────────────────────────────────┘
```
- Switch: excursion 0 = flat units (RULES MAT_07). Measure geometry fields before the move (RULES MAT_08).

## 3. Code
- Rhino: Rook `rhino_block_transform_instance_batch`, one transform per instance.
- Blender: no builder yet.

## 4. Instructions and parameters
1. **Where.**

   | Units in the Rhino model | Tilt and step in | Why |
   |---|---|---|
   | modelled and arrayed (blocks, separate objects) | Rhino (step 3) | a re-import replaces the units, and any Blender move with them |
   | one surface; units only drawn or printed (cast concrete) | Blender (step 4) | nothing in Rhino to move |

   Jointed units that need a real gap (brick, paver, glass block) are design: model them in Rhino.
2. **Excursion.** Size it as the **edge excursion** (tilt + step), not a tilt angle: an angle grows with
   unit width. Per unit: one tilt about its long axis through its centre, one step along the normal; seeded.
   Check: under raking light the courses step at the joints, and no unit stands out. Undo: excursion 0.

   | Parameter | Value |
   |---|---|
   | Edge excursion per unit | ±1–3 mm (formwork boards) |
   | Tilt axis | the unit's long axis |
3. **In Rhino.** Transform each instance in the owned study `.3dm` (RULES PIP_01), before the GAT_02
   captures. Tune on a patch of a few units first: every change needs a re-export and a re-import. Key after
   import: blocks `instancer` (`set_unit_keys`), separate objects `object`.
4. **In Blender.** A non-destructive modifier on the imported surface, re-applied after a re-import. Cut the
   surface into units joined by a narrow joint strip that takes the step, so the mesh stays manifold.
   Alternative: displace each unit by lift + slope × its local position, as tiles' cracked pieces do
   (`references/materials/tile/tiles.md` §4.4). Store an integer per face while the units are still apart
   (*Store Named Attribute*, Face domain, `unit_key`); the shading key `geometry` reads it.
   Check: no open edges; the key as emission shows each unit flat.

### Generic layers
| Layer | Reference | Note for this material |
|---|---|---|
| Tone, roughness per unit | [variation-per-unit-shading.md](variation-per-unit-shading.md) › step 1 | key from step 3 or 4 |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Tilt gone after a re-import | Rhino-modelled units moved in Blender | tilt in Rhino (step 1) |
| Courses do not step | normal tilt in the shading instead | excursion (step 2) |
| Wide units step more than narrow ones | tilt set as an angle | edge excursion (step 2) |
| Holes or overlaps at welded joints | units moved without a joint strip | joint strip (step 4) |

Generic problems: troubleshooting.md.
