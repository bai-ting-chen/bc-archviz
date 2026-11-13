"""Motion blur for still water: a per-vertex `velocity` attribute (m/s) read by Cycles deformation motion blur
(references/materials/water/water-free-falling-film.md §3.9). The mesh does not move; the streak length is
speed x shutter / fps (blender-api-traps › Render).
"""
import bpy
import numpy as np

from materials.water.ballistic_sheet import GRAVITY_M_S2


def fall_speed(launch_speed_m_s, lip_height_m, z):
    """Free-fall speed U = sqrt(launch_speed_m_s^2 + 2 g (lip_height_m - z)), m/s."""
    return np.sqrt(launch_speed_m_s ** 2 + 2 * GRAVITY_M_S2 * np.clip(lip_height_m - np.asarray(z), 0, None))


def set_velocity(obj, velocity):
    """Store a per-vertex `velocity` (m/s) and enable deformation motion blur on the object."""
    me = obj.data
    attr = me.attributes.get('velocity') or me.attributes.new('velocity', 'FLOAT_VECTOR', 'POINT')
    attr.data.foreach_set('vector', np.ascontiguousarray(velocity, dtype=np.float32).ravel())
    obj.cycles.use_motion_blur = True
    obj.cycles.use_deform_motion = True


def film_velocity(front, back, lip_height_m, launch_speed_m_s):
    """Velocity in water.mesh_builders.film_sheet's vertex order: fall speed along each skin's local fall direction."""
    out = []
    for skin in (front, back):
        direction = np.gradient(skin, axis=0)
        direction /= np.linalg.norm(direction, axis=-1, keepdims=True) + 1e-12
        out.append((direction * fall_speed(launch_speed_m_s, lip_height_m, skin[..., 2])[..., None]).reshape(-1, 3))
    return np.r_[out[0], out[1]]


def falling_velocity(obj, lip_height_m, launch_speed_m_s):
    """Straight-down velocity at the local fall speed for every vertex of an object (strings, drops)."""
    co = np.empty(len(obj.data.vertices) * 3, np.float32)
    obj.data.vertices.foreach_get('co', co)
    speed = fall_speed(launch_speed_m_s, lip_height_m, co.reshape(-1, 3)[:, 2])
    set_velocity(obj, np.c_[np.zeros_like(speed), np.zeros_like(speed), -speed])


def enable_motion_blur(scene, shutter_frames):
    """Turn on scene motion blur with the shutter in frames."""
    scene.render.use_motion_blur = True
    scene.render.motion_blur_shutter = shutter_frames
