"""Closed-cylinder seams and visible-side orientation checks."""

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

def check_rings(fails):
    """Check both concave and convex full rings."""
    arc = lambda a, b: math.hypot(R * abs(math.atan2(math.sin(math.atan2(a.y,a.x)-math.atan2(b.y,b.x)),
                                              math.cos(math.atan2(a.y,a.x)-math.atan2(b.y,b.x)))), a.z - b.z)
    # Full rings share vertices at the cut, with deliberately opposed normal directions.
    for R, concave in ((2.6, True), (1.8, False)):
        count, seam = 180, 0.37
        verts = [(R*math.cos(seam+i*math.tau/count), R*math.sin(seam+i*math.tau/count), z)
                 for z in (0.0, 2.6) for i in range(count)]
        faces = [(i, (i+1) % count, count+(i+1) % count, count+i) for i in range(count)]
        if concave:
            faces = [tuple(reversed(face)) for face in faces]
        me = bpy.data.meshes.new("ring_mesh")
        me.from_pydata(verts, [], faces)
        ring = bpy.data.objects.new("concave_ring" if concave else "convex_ring", me)
        bpy.context.scene.collection.objects.link(ring)
        n = tile_mapping.cylinder_uv(ring, (0, 0), R, seam_angle=seam)
        if uv_vs_world(ring, n, arc) > 1e-4:
            fails.append(f"{ring.name}: arc err")
        continuity(ring, n, {0, count}, fails=fails)
        # Z cross the surface normal is rightward from its visible side.
        for poly in me.polygons:
            li = list(poly.loop_indices)
            for a, b in zip(li, li[1:]+li[:1]):
                pa = me.vertices[me.loops[a].vertex_index].co
                pb = me.vertices[me.loops[b].vertex_index].co
                angle_delta = math.atan2(math.sin(math.atan2(pb.y,pb.x)-math.atan2(pa.y,pa.x)),
                                         math.cos(math.atan2(pb.y,pb.x)-math.atan2(pa.y,pa.x)))
                delta = me.uv_layers[n].data[b].uv - me.uv_layers[n].data[a].uv
                if abs(delta.x - (-1 if concave else 1)*R*angle_delta) > 1e-4 or abs(delta.y-(pb.z-pa.z)) > 1e-5:
                    fails.append(f"{ring.name}: rightward orientation err")
                    break
