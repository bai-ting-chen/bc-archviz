"""HDRI world and sun: the natural light of a scene, scaled in physical units.

The HDRI world is the sole natural light when one is used (RULES LGT_02); the sun helper is for
scenes without an HDRI (tests, controls).
"""
import math
import os

import bpy

from core.assets import library, read_meta
from scene.lighting.photometry import LM_PER_W


def world_hdri(hdri_id, strength=1.0, rotation_deg=0.0, res=None):
    """World = equirect HDRI from library/polyhaven/hdris/<id>, Z-rotated; strength is raw (use world_hdri_lux for lux)."""
    folder = library("polyhaven", "hdris", hdri_id)
    meta = read_meta(folder)
    path = os.path.join(folder, meta["file"] if res is None else "{}_{}.hdr".format(hdri_id, res))
    world = bpy.data.worlds.get("HDRI_" + hdri_id) or bpy.data.worlds.new("HDRI_" + hdri_id)
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    coord = nt.nodes.new("ShaderNodeTexCoord"); coord.location = (-800, 0)
    mapping = nt.nodes.new("ShaderNodeMapping"); mapping.location = (-600, 0)
    mapping.inputs["Rotation"].default_value[2] = math.radians(rotation_deg)
    env = nt.nodes.new("ShaderNodeTexEnvironment"); env.location = (-350, 0)
    env.image = bpy.data.images.load(path, check_existing=True)
    bg = nt.nodes.new("ShaderNodeBackground"); bg.location = (-50, 0)
    bg.inputs["Strength"].default_value = strength
    out = nt.nodes.new("ShaderNodeOutputWorld"); out.location = (200, 0)
    nt.links.new(coord.outputs["Generated"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], env.inputs["Vector"])
    nt.links.new(env.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    world["source"] = meta["source"]
    bpy.context.scene.world = world
    return world


def hdri_analyse(hdri_id, rotation_deg=0.0):
    """Horizontal illuminance (lux at strength 1) and direction to the brightest region of an
    equirect HDRI, in Blender world space after a Z rotation. The sun direction is the
    luminance centroid of the top 0.05 % texels."""
    import numpy as np
    folder = library("polyhaven", "hdris", hdri_id)
    meta = read_meta(folder)
    img = bpy.data.images.load(os.path.join(folder, meta["file"]), check_existing=True)
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(h, w, 4)  # row 0 = bottom (elevation -90 deg)
    lum = 0.2126 * px[..., 0] + 0.7152 * px[..., 1] + 0.0722 * px[..., 2]
    elev = ((np.arange(h) + 0.5) / h - 0.5) * np.pi
    # Cycles equirect (direction_to_equirectangular): u = 0.5 - atan2(y, x) / 2pi
    phi = (0.5 - (np.arange(w) + 0.5) / w) * 2 * np.pi
    d_omega = (2 * np.pi / w) * (np.pi / h) * np.cos(elev)
    up = elev > 0
    E = float((lum[up] * (np.sin(elev[up]) * d_omega[up])[:, None]).sum()) * LM_PER_W
    thr = np.quantile(lum, 0.9995)
    ys, xs = np.nonzero(lum >= thr)
    wts = lum[ys, xs]
    el, ph = elev[ys], phi[xs]
    dx, dy, dz = np.cos(el) * np.cos(ph), np.cos(el) * np.sin(ph), np.sin(el)
    v = np.array([(dx * wts).sum(), (dy * wts).sum(), (dz * wts).sum()])
    v /= np.linalg.norm(v)
    # The world Mapping node rotates the lookup (s = Rz . d), so the world direction is Rz^T . s
    r = math.radians(rotation_deg)
    v = np.array([math.cos(r) * v[0] + math.sin(r) * v[1], -math.sin(r) * v[0] + math.cos(r) * v[1], v[2]])
    return {"lux_at_strength_1": E, "sun_dir": v.tolist(),
            "sun_elev_deg": math.degrees(math.asin(v[2])),
            "sun_az_deg": math.degrees(math.atan2(v[1], v[0]))}


def world_hdri_lux(hdri_id, target_lux, rotation_deg=0.0, visible=True):
    """HDRI world scaled so the upper hemisphere delivers `target_lux` on a horizontal plane."""
    info = hdri_analyse(hdri_id, rotation_deg)
    strength = target_lux / info["lux_at_strength_1"]
    world = world_hdri(hdri_id, strength=strength, rotation_deg=rotation_deg)
    world.cycles_visibility.camera = visible
    info["strength"] = strength
    return info


def sun_from_direction(direction, strength_lux, angle_deg=0.53, name="Sun_matched"):
    """Sun lamp pointing along -direction (direction = towards the sun). Strength in lux.
    Only for scenes WITHOUT an HDRI (tests, controls): with an HDRI sky the map is the sole
    natural light and its own sun does this job (RULES LGT_02)."""
    from mathutils import Vector
    d = Vector(direction).normalized()
    lamp = bpy.data.lights.get(name) or bpy.data.lights.new(name, "SUN")
    lamp.energy = strength_lux / LM_PER_W  # Blender sun strength is irradiance, W/m2
    lamp.angle = math.radians(angle_deg)
    ob = bpy.data.objects.get(name) or bpy.data.objects.new(name, lamp)
    if ob.name not in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(ob)
    ob.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    return ob
