"""Mapping precondition and requested-map checks."""

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

def check_contract(slab, f, fails):
    """Reject shared meshes, missing maps and a ninth UV layer."""
    me = slab.data
    # Shared geometry and missing requested maps must fail before mutation.
    shared = bpy.data.objects.new("shared_slab", me)
    bpy.context.scene.collection.objects.link(shared)
    for mapper in (lambda: tile_mapping.planar_uv(slab),
                   lambda: tile_mapping.cylinder_uv(slab, (0, 0), 1.0)):
        try:
            mapper()
        except ValueError:
            pass
        else:
            fails.append("shared mesh accepted")
    tree = bpy.data.node_groups.new("mapping_control", "ShaderNodeTree")
    try:
        tile_mapping.layout_vector(tree, name="missing", obj=f)
    except ValueError:
        pass
    else:
        fails.append("missing UV layer accepted")
    socket = tile_mapping.layout_vector(tree, obj=f)
    if socket.node.uv_map != "TileUV":
        fails.append("layout_vector map err")

    bpy.ops.mesh.primitive_plane_add()
    limited = bpy.context.object
    for i in range(8):
        if len(limited.data.uv_layers) < 8:
            limited.data.uv_layers.new(name=f"occupied_{i}")
    try:
        tile_mapping.planar_uv(limited, name="ninth_map")
    except ValueError:
        pass
    else:
        fails.append("UV layer limit accepted")
