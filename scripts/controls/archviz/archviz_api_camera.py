"""Archviz camera API checks."""

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

def check_camera():
    """Camera set-up: lens, physical exposure, DOF and lens shift."""
    cam_data = bpy.data.cameras.new("ApiCam")
    cam = bpy.data.objects.new("ApiCam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (0.0, -6.0, 1.6)
    cam.rotation_euler = (math.radians(74.0), 0.0, math.radians(12.0))
    bpy.context.view_layer.update()
    use = archviz.use_camera("ApiCam", lens=28)
    sheet = archviz.physical_camera(cam, iso=400, fstop=5.6, shutter_s=1 / 125, focal_mm=24,
                                    focus_distance=6.5, dof=True)
    shift = archviz.straighten_verticals(cam)
    return {"use": use.name, "lens": rounded(cam.data.lens), "sensor": rounded(cam.data.sensor_width),
            "physical": rounded(sheet), "fstop": rounded(cam.data.dof.aperture_fstop),
            "focus": rounded(cam.data.dof.focus_distance), "shift": rounded(shift),
            "rot": rounded(tuple(cam.rotation_euler)), "shift_y": rounded(cam.data.shift_y)}
