"""Archviz materials API checks."""

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
from archviz_api_rig import HDRI, rounded, cube, uv_table

def check_material_map():
    """Material assignment report from apply_material_map."""
    cube_ob = cube("MapCube")
    coll = bpy.data.collections.new("MapRoot")
    bpy.context.scene.collection.children.link(coll)
    bpy.context.scene.collection.objects.unlink(cube_ob)
    coll.objects.link(cube_ob)
    report = archviz.apply_material_map(coll, {"MapRoot": {"type": "simple", "name": "ApiMat", "color": [0.5, 0.4, 0.3], "roughness": 0.6}})
    return {"report": rounded(report)}
