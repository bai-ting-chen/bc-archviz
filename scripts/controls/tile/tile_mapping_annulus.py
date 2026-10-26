"""Annular soffit radial and cylindrical-joint checks."""

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

def check_annulus(fails):
    """Check the well bottom continues its wall joints."""
    # The concave well's bottom cut pieces must continue its vertical joints.
    R, count, seam = 2.6, 180, 0.37
    angles = [seam + i * math.tau / count for i in range(count)]
    wall_verts = [(R*math.cos(a), R*math.sin(a), z) for z in (2.6, 4.0) for a in angles]
    wall_faces = [(count+i, count+(i+1) % count, (i+1) % count, i) for i in range(count)]
    me = bpy.data.meshes.new("well_wall_mesh")
    me.from_pydata(wall_verts, [], wall_faces)
    wall = bpy.data.objects.new("well_wall", me)
    bpy.context.scene.collection.objects.link(wall)
    wall_map = tile_mapping.cylinder_uv(wall, (0, 0), R, seam_angle=seam)
    if wall["tile_uv_sign"] != -1 or abs(wall["tile_uv_seam"] - seam) > 1e-12:
        fails.append("well wall sign/seam metadata err")
    continuity(wall, wall_map, {0, count}, fails=fails)
    ring_verts = [(r*math.cos(a), r*math.sin(a), 2.6) for r in (R, 2.65) for a in angles]
    # Clockwise from above: exposed bottom face has -Z normal.
    ring_faces = [(i, (i+1) % count, count+(i+1) % count, count+i) for i in range(count)]
    me = bpy.data.meshes.new("well_bottom_mesh")
    me.from_pydata(ring_verts, [], ring_faces)
    bottom = bpy.data.objects.new("well_bottom", me)
    bpy.context.scene.collection.objects.link(bottom)
    bottom_map = tile_mapping.annulus_uv(bottom, (0, 0), R, like=wall)
    continuity(bottom, bottom_map, {0, count}, fails=fails)
    wall_uv = wall.data.uv_layers[wall_map].data
    bottom_uv = me.uv_layers[bottom_map].data
    for wall_face, ring_face in zip(wall.data.polygons, me.polygons):
        # Compare corresponding faces so the two sheets of the seam stay distinct.
        wall_u = {wall.data.loops[i].vertex_index: wall_uv[i].uv.x
                  for i in wall_face.loop_indices if wall.data.loops[i].vertex_index < count}
        face_uv = {me.loops[i].vertex_index: bottom_uv[i].uv.copy() for i in ring_face.loop_indices}
        for vertex, uv in face_uv.items():
            p = bottom.matrix_world @ me.vertices[vertex].co
            expected_v = math.hypot(p.x, p.y) - R
            if abs(uv.y - expected_v) > 1e-6:
                fails.append("annulus radial V err")
            if vertex < count:
                outer = face_uv[vertex + count]
                if abs(uv.x - wall_u[vertex]) > 1e-6:
                    fails.append("annulus/wall joint continuation err")
                if abs(outer.x - uv.x) > 1e-6:
                    fails.append("annulus radial U err")
                if outer.y <= uv.y:
                    fails.append("annulus V does not increase outward")
