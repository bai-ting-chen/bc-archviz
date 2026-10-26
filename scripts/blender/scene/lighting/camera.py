"""Camera: which camera is active, its lens and sensor, real-world exposure, and architectural framing.

A physical camera (ISO, f-stop, shutter) drives both exposure and depth of field, so brightness and
DOF stay in sync. straighten_verticals keeps verticals parallel with a lens shift instead of tilt.
"""
import math

import bpy

from scene.lighting.photometry import LM_PER_W, ev100


def use_camera(name, lens=None):
    """Make the named camera active, optionally setting its focal length (mm)."""
    cam = bpy.data.objects[name]
    if lens:
        cam.data.lens = lens
    cam.data.sensor_width = 36
    bpy.context.scene.camera = cam
    return cam


def physical_camera(cam_obj, iso, fstop, shutter_s, focal_mm, sensor_mm=36.0,
                    focus_distance=None, dof=True):
    """Real camera triple -> Blender. Exposure follows the saturation-based sensor model
    (pixel = L / (1.2 * 2^EV100), L in cd/m2): stops = log2(683 / 1.2) - EV100.
    The same f-stop drives depth of field, so brightness and DOF stay in sync."""
    ev = ev100(iso, fstop, shutter_s)
    cam = cam_obj.data
    cam.lens, cam.sensor_width, cam.sensor_fit = focal_mm, sensor_mm, "HORIZONTAL"
    cam.dof.use_dof = dof
    cam.dof.aperture_fstop = fstop
    if focus_distance:
        cam.dof.focus_distance = focus_distance
    sc = bpy.context.scene
    sc.camera = cam_obj
    sc.view_settings.exposure = math.log2(LM_PER_W / 1.2) - ev
    return {"ev100": ev, "exposure_stops": sc.view_settings.exposure}


def straighten_verticals(cam_obj):
    """Architectural shift lens: level the camera (pitch 90 deg) and recover the framing
    with vertical lens shift, so verticals stay parallel."""
    from mathutils import Vector
    cam = cam_obj.data
    bpy.context.view_layer.update()       # matrix_world is stale right after a scripted rotation
    fwd = cam_obj.matrix_world.to_3x3() @ Vector((0, 0, -1))
    pitch = math.asin(max(-1, min(1, fwd.z)))
    e = cam_obj.rotation_euler.copy()
    cam_obj.rotation_mode = "XYZ"
    yaw = math.atan2(fwd.y, fwd.x) - math.pi / 2
    cam_obj.rotation_euler = (math.pi / 2, 0.0, yaw)
    # Blender shift is a fraction of the sensor's larger side (sensor_fit HORIZONTAL, width).
    cam.shift_y = cam.lens * math.tan(pitch) / cam.sensor_width
    return {"pitch_deg": math.degrees(pitch), "shift_y": cam.shift_y, "was": tuple(e)}
