"""Planar facing, unapplied transform and slab checks."""

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

def check_planar(w, f, c, fails):
    """Check the visible-side basis and unapplied transform."""
    from mathutils import Vector
    room_normal = Vector((math.sin(math.radians(37)), -math.cos(math.radians(37)), 0))
    wall_u = Vector((0, 0, 1)).cross(room_normal)
    n = tile_mapping.planar_uv(w, facing=room_normal)
    continuity(w, n, fails=fails)
    orientation(w, n, wall_u, (0, 0, 1), fails=fails)
    camera = bpy.data.objects.new("facing_camera", bpy.data.cameras.new("facing_camera"))
    bpy.context.scene.collection.objects.link(camera)
    camera.location = room_normal * 5
    n = tile_mapping.planar_uv(w, facing=camera)
    orientation(w, n, wall_u, (0, 0, 1), fails=fails)
    n = tile_mapping.planar_uv(f)
    continuity(f, n, fails=fails)
    orientation(f, n, (1, 0, 0), (0, 1, 0), fails=fails)
    continuity(c, c.data.uv_layers.active.name, fails=fails)

    # An unapplied transform must produce world-metre distances, including translation.
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=7, y_subdivisions=5, size=1)
    transformed = bpy.context.object
    transformed.name = "unapplied_wall"
    transformed.scale = (3, 2.6, 0.7)
    transformed.rotation_euler = (math.pi/2, 0, math.radians(37))
    transformed.location = (4.2, -3.1, 0.8)
    n = tile_mapping.planar_uv(transformed, facing=room_normal)
    if uv_vs_world(transformed, n, lambda a, b: (a-b).length) > 1e-4:
        fails.append("unapplied world lengths err")
    continuity(transformed, n, fails=fails)
    orientation(transformed, n, wall_u, (0, 0, 1), fails=fails)

def check_slab(fails):
    """Check the weighted slab normal."""
    # A slab's subdivided front must outweigh its individually larger top face.
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    bm.normal_update()
    for vertex in bm.verts:
        vertex.co.x *= 3
        vertex.co.y *= 0.2
        vertex.co.z *= 2.6
    front = next(face for face in bm.faces if face.normal.y < -0.9)
    bmesh.ops.subdivide_edges(bm, edges=list(front.edges), cuts=15, use_grid_fill=True)
    me = bpy.data.meshes.new("slab_mesh")
    bm.to_mesh(me)
    bm.free()
    slab = bpy.data.objects.new("subdivided_slab", me)
    bpy.context.scene.collection.objects.link(slab)
    n = tile_mapping.planar_uv(slab, facing=(0, -1, 0))
    continuity(slab, n, fails=fails)
    orientation(slab, n, (1, 0, 0), (0, 0, 1), fails=fails)
    return slab
