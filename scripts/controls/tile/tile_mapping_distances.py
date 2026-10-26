"""Planar and open-cylinder UV metric checks."""

import os as _os
import sys as _sys
_CONTROLS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in [_CONTROLS] + [_os.path.join(_CONTROLS, _t) for _t in ('archviz', 'tile', 'material', 'effects', 'water', 'lighting', 'environment', 'regression')]:
    if _d not in _sys.path:
        _sys.path.append(_d)
import math
import bpy
import bmesh
import materials.tile.tile_mapping as tile_mapping
from tile_mapping_rig import uv_vs_world, continuity, orientation

def check_distances(fails):
    """Check planar metres and the open cylindrical seam."""
    # planar wall, rotated 37 deg about Z, 3 x 2.6 m, subdivided
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=7, y_subdivisions=5, size=1)
    w = bpy.context.object; w.scale = (3, 2.6, 1); w.rotation_euler = (math.pi/2, 0, math.radians(37))
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    n = tile_mapping.planar_uv(w)
    e = uv_vs_world(w, n, lambda a, b: (a - b).length)
    if e > 1e-4: fails.append(f"planar wall err {e:.6f}")
    # floor
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=4, y_subdivisions=4, size=4)
    f = bpy.context.object
    n = tile_mapping.planar_uv(f)
    if uv_vs_world(f, n, lambda a, b: (a - b).length) > 1e-4: fails.append("floor err")
    # cylinder R 1.8 spanning 150..250 deg (crosses +-pi), 2.6 m tall
    R, verts, faces = 1.8, [], []
    angs = [math.radians(a) for a in range(150, 251, 2)]
    for z in (0.0, 1.3, 2.6):
        verts += [(R*math.cos(t), R*math.sin(t), z) for t in angs]
    N = len(angs)
    for r in range(2):
        for i in range(N - 1):
            faces.append((r*N+i, r*N+i+1, (r+1)*N+i+1, (r+1)*N+i))
    me = bpy.data.meshes.new("cyl"); me.from_pydata(verts, [], faces)
    c = bpy.data.objects.new("cyl", me); bpy.context.scene.collection.objects.link(c)
    n = tile_mapping.cylinder_uv(c, (0.0, 0.0), R)
    arc = lambda a, b: math.hypot(R * abs(math.atan2(math.sin(math.atan2(a.y,a.x)-math.atan2(b.y,b.x)),
                                              math.cos(math.atan2(a.y,a.x)-math.atan2(b.y,b.x)))), a.z - b.z)
    if uv_vs_world(c, n, arc) > 1e-4: fails.append("cylinder arc err")
    us = [l.uv.x for l in c.data.uv_layers[n].data]
    if max(us) - min(us) > R * math.radians(100) + 1e-3: fails.append("seam: U jumps across the cut")
    return w, f, c
