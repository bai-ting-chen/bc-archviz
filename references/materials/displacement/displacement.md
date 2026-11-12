# Displacement

## 1. Overview
Setting up true displacement, where the mesh itself moves by a height map. The material that needs it
says where (e.g. joints in board-formed-concrete.md).

**Use when:** relief must show in the silhouette or cast its own shadow. Finer surface detail stays bump.

## 2. Layers and node-editor diagram
This is a single layer, not a shading stack: it sits on the mesh, not in the material. It is set up
on the mesh with a Subdivision modifier (SIMPLE, adaptive 1 px) last in the stack (§4.1).

## 3. Code
- `scripts/blender/materials/displacement/displacement.py`: `enable_true_displacement(obj, pixel_size=1.0)`.
- `displaced_ground()`: in `scripts/blender/materials/ground/gravel.py`, exported through `ground.py`.
- Control: none named in this file.

## 4. Instructions and parameters, per layer

### 4.1 True displacement setup
- Displacement Scale = the relief height. Midlevel = −shift / scale.
- Method BOTH; use Displacement Only once the mesh is finely diced.
- Subdivision SIMPLE, adaptive 1 px, last in the stack.
- `cycles.dicing_camera` = the render camera.

| Parameter | Value |
|---|---|
| Displacement Scale | the relief height |
| Midlevel | −shift / scale |
| Method | BOTH (Displacement Only once finely diced) |
| Subdivision | SIMPLE, adaptive 1 px, last in the stack |
| Dicing camera | the render camera (`cycles.dicing_camera`) |

### Generic layers, displacement settings
No generic layers apply to this file.

## 5. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| A shelf or fin where the surface should be flat | a distance field that drives a fin or a displacement went negative and was amplified (one case: ~100×, a shelf on the floor) | clamp every distance before it drives geometry |

Generic problems: troubleshooting.md (named here, not linked, so this file adds no reference loop).
