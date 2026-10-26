"""Motion blur for still water: a per-vertex `velocity` attribute (m/s) read by Cycles deformation motion blur
(references/materials/water/water-free-falling-film.md §3.9). The mesh does not move; the streak length is
speed x shutter / fps (blender-api-traps › Render).
"""
import bpy
import numpy as np

G = 9.81


def fall_speed(v0, lip_z, z):
    """Free-fall speed U = sqrt(v0^2 + 2 g (lip_z - z)), m/s."""
    return np.sqrt(v0 ** 2 + 2 * G * np.clip(lip_z - np.asarray(z), 0, None))


def set_velocity(ob, velocity):
    """Store a per-vertex `velocity` (m/s) and enable deformation motion blur on the object."""
    me = ob.data
    attr = me.attributes.get('velocity') or me.attributes.new('velocity', 'FLOAT_VECTOR', 'POINT')
    attr.data.foreach_set('vector', np.ascontiguousarray(velocity, dtype=np.float32).ravel())
    ob.cycles.use_motion_blur = True
    ob.cycles.use_deform_motion = True


def film_velocity(front, back, lip_z, v0):
    """Velocity in water.mesh.film_sheet's vertex order: fall speed along each skin's local fall direction."""
    out = []
    for skin in (front, back):
        direction = np.gradient(skin, axis=0)
        direction /= np.linalg.norm(direction, axis=-1, keepdims=True) + 1e-12
        out.append((direction * fall_speed(v0, lip_z, skin[..., 2])[..., None]).reshape(-1, 3))
    return np.r_[out[0], out[1]]


def falling_velocity(ob, lip_z, v0):
    """Straight-down velocity at the local fall speed for every vertex of an object (strings, drops)."""
    co = np.empty(len(ob.data.vertices) * 3, np.float32)
    ob.data.vertices.foreach_get('co', co)
    speed = fall_speed(v0, lip_z, co.reshape(-1, 3)[:, 2])
    set_velocity(ob, np.c_[np.zeros_like(speed), np.zeros_like(speed), -speed])


def enable(scene, shutter_frames):
    """Turn on scene motion blur with the shutter in frames."""
    scene.render.use_motion_blur = True
    scene.render.motion_blur_shutter = shutter_frames
