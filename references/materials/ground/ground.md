# Ground

## 1. Overview
Two cases: **exposed-aggregate precast** (columns, slab edges), a box-mapped aggregate at real size;
and **landform terrain**, a graded ground for a building on a hill. The terrain is built as geometry
from a flat pad, an apron and a rounded fall, with a broad roll and hummocks beyond. Relief of a
ground mesh set up as true displacement is in displacement.md.

**Use when:** a building sits on a sloping site and its ground is graded to a landform. Ground relief
set up as true displacement: displacement.md.

## 2. Layers and node-editor diagram
Specific layers are described in §4. No generic layers apply to this file.

```
                            GROUND
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ SPECIFIC (§4)                                                             │
 │ 1 Aggregate precast   → material (box map, real size)                     │
 │ 2 Landform grade      → geometry (smoothstep fall from the pad)           │
 │ 3 Roll and hummocks   → geometry (noise on the terrain)                   │
 └───────────────────────────────────────────────────────────────────────────┘
   distance from the pad (2), warped by slow noise ─► fall height ─► terrain grid
   broad roll and hummocks (3) added beyond the fall ─► same terrain grid
   aggregate (1) on fascia and soffit bands ─► precast material; soffits on a second slot
```


## 3. Code
- `scripts/blender/scene/environment/`: `terrain.py` (the `terrain` module the calls use),
  `terrain_graph.py` (`landform_group`, the pad distance), `terrain_objects.py` (`add_terrain`),
  `terrain_height.py` (`height`, the no-noise twin).
- Aggregate precast: no script is named in this file.
- Control: none named in this file.

## 4. Instructions and parameters, per layer

### 4.1 Exposed-aggregate precast
- Box-map an aggregate map at real size. Use the same map on fascia and soffit bands.
- Soffits (Normal Z < −0.5) go on a smoother, darker concrete via a second material slot.

| Parameter | Value |
|---|---|
| Projection | box map at real size |
| Bands | fascia and soffit, same map |
| Soffit test | Normal Z < −0.5 |
| Soffit material | smoother, darker concrete, second material slot |

### 4.2 Landform grade (geometry)
- A building on a hill: a flat pad just under the slab, an apron, then the fall as a smoothstep in the
  distance from the pad. That gives a rounded crest **and** a rounded toe (landform grading, natural
  slopes), never a cone or a linear batter.
- Warp the distance with a slow noise so the contours wander.
- Steepest slope of a smoothstep fall = 1.5 × fall / run. Gentle or mowable: ≤ 4:1 (25 %); 3:1 is the
  usual limit for maintained grass.
- To read as a hill, the camera stands down the slope with the crest against the sky. The edge of the
  generated grid must stay out of frame (the frustum mask hides the rest).
- `terrain.height(x, y, ...)` is the no-noise twin for placing a camera at eye height.

| Parameter | Value |
|---|---|
| Fall profile | smoothstep in the distance from the pad (rounded crest and toe) |
| Steepest slope | 1.5 × fall / run |
| Gentle / mowable | ≤ 4:1 (25 %) |
| Maintained grass | 3:1 usual limit |
| Grid edge | out of frame |

### 4.3 Roll and hummocks (geometry)
- Add a broad roll beyond the fall, and pasture hummocks.

| Parameter | Value |
|---|---|
| Hummocks | ±5–10 cm at ~1.5 m |

### Generic layers, ground settings
No generic layers apply to this file.

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Hill reads as a cone or a ramp | linear batter or cone fall | smoothstep fall with a rounded crest and toe (§4.2) |
| Contours too regular | no noise on the distance | warp the distance with a slow noise (§4.2) |
| Grid edge visible in frame | camera position | stand down the slope with the crest against the sky (§4.2) |
| Slope too steep to mow | fall / run too large | keep to ≤ 4:1; 3:1 for maintained grass (§4.2) |
| Camera floats or sinks at eye height | noisy height at the camera | use `terrain.height` (§4.2) |
| Soffits look like the fascia | one material slot | second slot for Normal Z < −0.5 (§4.1) |

No generic problems are listed in this file. The general list is in troubleshooting.md (named here,
not linked, so this file adds no reference loop).
