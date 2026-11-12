# Glass block

## 1. Overview
Hollow glass blocks and walls laid from them. The relief on their inner faces is in
[glass-relief.md](glass-relief.md); the plain glass is `glass.md` §4.1.

## 2. Layers and node-editor diagram
```
 ┌─ GLASS BLOCK — PROCEDURE DIAGRAM ────────────────────────────────────────┐
 │ Unit            two pressed halves, hollow ─► block definition           │
 │   ▼                                                                      │
 │ Wall layout     stack bond, joints, perimeter band ─► instances          │
 │   ▼                                                                      │
 │ Curved wall     joints open on the convex side ─► minimum radius         │
 │   ▼                                                                      │
 │ Relief          inner faces ─► glass-relief.md                           │
 │   ▼                                                                      │
 │ Mortar          joint mesh, clear of the glass ─► its own material       │
 │   ▼                                                                      │
 │ Variation       per-unit tone and variants ─► instances                  │
 └──────────────────────────────────────────────────────────────────────────┘
```
- Off switch: none; the wall is geometry. Relief off is the flat-faced unit.

## 3. Code
No builder: units are modelled in Rhino as block definitions and the wall as their instances (RULES
PIP_01). Glass: `materials.glass.glass.clear_glass`; in LuxCore a per-instance tint is
`renderer.luxcore.luxcore.glass_instance_tint`.

## 4. Instructions and parameters
Table values are starting points; take the real unit from the manufacturer's sheet when there is one.

### Step 1. The unit
- Two pressed halves are fused hot and sealed hollow. The pattern is on the **inner** faces; the outer
  faces are smooth with slight pressing waviness; the sides are coated to key to the mortar.
- Model both walls of glass and the cavity.

| Parameter | Value |
|---|---|
| Common units | 190×190×80 mm (2.3 kg); 240×240×80 mm (4.1 kg) |
| Face glass / side glass | ~8 mm / ~7 mm (from the weight) |

### Step 2. Wall layout
- Stack bond with continuous joints both ways, a wider band at the perimeter, and a limit on panel
  area.

| Parameter | Value |
|---|---|
| Joints | 10 mm |
| Perimeter band | ≥ 15 mm |
| Panel area | ≤ ~15 m² |

### Step 3. Curved wall
- On a curve the joint on the concave side stays constant and the convex one opens:
  E = (L + g)(1 + s/r) − L, with L unit length, g inner joint, s unit depth, r inner radius.
- The widest acceptable outer joint sets the minimum radius.

| Parameter | Value |
|---|---|
| Inner / outer joint | g 10 mm / E ≤ 25 mm |
| Minimum inner radius | ~1.05 m (190 units); ~1.33 m (240 units) |

### Step 4. Relief
- Shape the inner faces as in glass-relief.md: geometry, faded to flat towards the block's edge,
  several variants.

### Step 5. Mortar
- A separate joint mesh with its own material. Leave a fraction of a millimetre of air between
  mortar and glass so the two surfaces never coincide.

### Step 6. Variation
- Per-unit tone and tilt, and which relief variant each unit gets (RULES MAT_06).

### Generic layers
| Layer | Reference | Note for this material |
|---|---|---|
| Relief on the inner faces | [glass-relief.md](glass-relief.md) | step 4 |
| Per-unit tone | [variation-per-unit-shading.md](../../effects/variation-per-unit-shading.md) | small normal tilt |
| Light thrown into the room | [caustics.md](../../effects/caustics.md) | when it carries the shot (RULES REN_03) |

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Mortar and glass flicker or z-fight | surfaces coincide | air gap (step 5) |
| Curved wall joints look wrong | convex joint not opened, or radius below the minimum | joint formula and minimum radius (step 3) |
| Wall reads as one sheet of pattern | every unit identical | variants and per-unit tone (steps 4 and 6) |

Generic problems: troubleshooting.md.
