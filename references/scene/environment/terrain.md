# Naturally sloped terrain

Sloped terrain around a building on a hill, as geometry; its shading is the ground material's.

## Code
`scene.environment.terrain` exports the builders from `scripts/blender/scene/environment/terrain_graph.py` and `scripts/blender/scene/environment/terrain_objects.py`. Call them in this order in Blender; `material` is an existing material. Names below override the API defaults.

```python
import scene.environment.terrain as terrain

group = terrain.landform_group(
    name="terrain-landform", centre=(0.0, 0.0), pad_half=(4.0, 4.0),
    size=300.0, verts=601, pad_z=-0.03, crest=1.5, fall=6.0,
    run=40.0, warp=7.0, roll=2.5, hummock=0.12,
)
obj = terrain.add_terrain(group, material, name="terrain", collection=None)
```

## Steps
1. Set the pad and fall dimensions in metres using the table. Check that the pad covers the building footprint and the base grade meets the intended slope limit.
2. With those dimensions, call `landform_group`. Use an unused group name: the builder replaces a group with the same name. Check the returned group's `params` against the dimensions from step 1; correct the arguments and rebuild if they differ.
3. Pass that group and the existing material to `add_terrain`; `collection=None` uses the scene collection. Check the evaluated mesh: the pad is flat at its specified elevation, the fall joins smoothly, and contours wander. If it fails, remove the created object and its mesh, correct the group settings and repeat steps 2–3.

## Parameters
Noise scales below are fixed in the script, not function arguments. Amplitudes are maximum offsets about the base grade; noise and roll can increase local slopes beyond the base profile.

| Parameter | Default or guidance |
|---|---|
| `centre`, `pad_half` | (0, 0) m in XY; (4, 4) m half-widths |
| `size`, `verts` | 300 m square; 601 vertices per side (0.5 m spacing) |
| `pad_z` | −0.03 m elevation |
| `crest` | 1.5 m apron before the unwarped fall starts |
| `fall`, `run` | 6 m vertical drop over 40 m horizontal distance |
| Steepest base slope | 1.5 × fall / run; defaults give 22.5 % |
| Gentle / mowable | slope ≤25 % (4:1 horizontal:vertical or flatter) |
| Maintained grass | usual limit 3:1 horizontal:vertical (~33 %) |
| `warp` | ±7 m contour-distance offset; noise scale 0.025 m⁻¹; fades in over 0–12 m from pad |
| `roll` | ±2.5 m broad roll; noise scale 0.012 m⁻¹; fades in over 6–30 m from pad |
| `hummock` | ±0.12 m default; pasture reads best at 0.05–0.10 m; noise scale 0.6 m⁻¹ (~1.5 m bumps); fades in over 0.5–3 m from pad |

`terrain.height(x, y, centre, pad_half, pad_z=-0.03, crest=1.5, fall=6.0, run=40.0)` gives the no-noise height for approximate ground placement; sample the evaluated mesh for exact contact.

## Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Hill reads as a cone or ramp | linear fall in a custom setup | rebuild with the step 2 graph |
| Contours too regular | insufficient distance warp | increase `warp` and repeat the mesh check in step 3 |
| Local slope too steep | base grade or added noise too strong | increase `run`, reduce `fall`, or reduce noise amplitudes; check the evaluated slope |
| Hummocks look faceted | grid spacing too coarse | increase `verts` for the same `size` |
