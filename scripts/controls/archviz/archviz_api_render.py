"""Archviz render API checks."""

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

def check_render_setup():
    """Cycles settings written by render_setup."""
    archviz.render_setup(width=1280, height=720, samples=64, exposure=0.5)
    sc = bpy.context.scene
    return {"engine": sc.render.engine, "samples": sc.cycles.samples, "adaptive": sc.cycles.use_adaptive_sampling,
            "threshold": rounded(sc.cycles.adaptive_threshold), "denoiser": sc.cycles.denoiser,
            "bounces": sc.cycles.max_bounces, "transparent": sc.cycles.transparent_max_bounces,
            "res": [sc.render.resolution_x, sc.render.resolution_y], "look": sc.view_settings.look,
            "exposure": rounded(sc.view_settings.exposure), "units": sc.unit_settings.system}

def check_gpu():
    """Device chosen by use_gpu."""
    archviz.use_gpu()
    return {"device": bpy.context.scene.cycles.device}
