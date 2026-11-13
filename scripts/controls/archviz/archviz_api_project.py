"""Archviz project API checks."""

import os as _os, sys as _sys
_sys.path.append(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import controls_import_paths  # noqa: E402,F401 -- every controls topic folder on sys.path
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
