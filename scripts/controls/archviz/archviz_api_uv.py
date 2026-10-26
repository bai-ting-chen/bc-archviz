"""Archviz uv API checks."""

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

def check_uv():
    """Directional, box and span UV tables of a cube."""
    out = {}
    a = cube("UV_directional")
    out["directional_axis"] = archviz.directional_uv(a, size=0.5, name="DirUV", axis="Z", along="V")
    out["directional"] = uv_table(a, "DirUV")
    b = cube("UV_box")
    archviz.box_uv(b, size=0.8, name="BoxUV")
    out["box"] = uv_table(b, "BoxUV")
    c = cube("UV_span")
    c.data.uv_layers.new(name="SpanUV")
    archviz.height_span_uv(c, u_size=3.0, v_repeat=2.0, name="SpanUV")
    out["span"] = uv_table(c, "SpanUV")
    return out
