"""Shared archviz API result rounding and unit-cube fixtures."""

import os as _os
import sys as _sys
_CONTROLS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in [_CONTROLS] + [_os.path.join(_CONTROLS, _t) for _t in ('archviz', 'tile', 'material', 'effects', 'water', 'lighting', 'environment', 'regression')]:
    if _d not in _sys.path:
        _sys.path.append(_d)
import math
import os
import bpy
import bmesh
from mathutils import Vector
import core.archviz as archviz

HDRI = "abandoned_hall_01"

def rounded(x):
    """Floats to 6 places, recursively, so JSON compares exactly across runs."""
    if isinstance(x, float):
        return round(x, 6)
    if isinstance(x, (list, tuple, Vector)):
        return [rounded(v) for v in x]
    if isinstance(x, dict):
        return {str(k): rounded(v) for k, v in x.items()}
    return x

def cube(name):
    """A unit cube, offset so the UV projections see non-zero coordinates."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = (0.3, -0.7, 1.1)
    ob.scale = (1.5, 0.8, 2.2)
    bpy.context.view_layer.update()
    return ob

def uv_table(ob, uv_name):
    """Every loop's UV for one UV layer, in mesh order."""
    layer = ob.data.uv_layers[uv_name]
    return [rounded(d.uv) for d in layer.data]
