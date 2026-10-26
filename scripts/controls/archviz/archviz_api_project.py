"""Archviz project API checks."""

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

def check_project():
    """The project folder name and the HDRI library path relative to it."""
    root = archviz.project_root()
    return {"library_rel": os.path.relpath(archviz.library("polyhaven", "hdris"), root).replace("\\", "/"),
            "root_name": os.path.basename(root)}

def check_meta():
    """Keys and source of one HDRI meta.json, read only."""
    folder = archviz.library("polyhaven", "hdris", HDRI)
    meta = archviz.read_meta(folder)
    return {"keys": sorted(meta.keys()), "file": meta.get("file"), "source": meta.get("source")}
