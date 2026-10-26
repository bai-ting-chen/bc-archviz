"""Shared set-up for the headless controls: an empty Cycles scene with a truly black world, a
white Lambert material, and the linear render read back as numpy (temp file always removed).

A new world's default 0.05 grey background adds pi*0.05 W/m2 to every surface, so the world
strength is set to 0 here; Specular IOR Level 0 + roughness 1 keeps the plane Lambertian, so
pixel = albedo * E / pi.
"""
import os
import shutil
import sys
import tempfile

import bpy
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "blender"))
import core.archviz as archviz


def black_scene(samples=256, res=64, gpu=True):
    """Empty Cycles scene, black world; on the GPU (--factory-startup alone renders on the CPU)."""
    bpy.ops.wm.read_homefile(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    if gpu:
        archviz.use_gpu()
    sc.cycles.samples, sc.cycles.use_denoising = samples, False
    sc.cycles.use_adaptive_sampling = False
    sc.render.resolution_x = sc.render.resolution_y = res
    sc.view_settings.view_transform = "Standard"
    sc.world = bpy.data.worlds.new("black")
    sc.world.use_nodes = True
    sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.0
    return sc


def white_lambert(name="white", albedo=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (albedo, albedo, albedo, 1)
    b.inputs["Roughness"].default_value = 1.0
    b.inputs["Specular IOR Level"].default_value = 0.0
    return m


def ortho_camera(z, scale, xy=(0.0, 0.0)):
    sc = bpy.context.scene
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(cam)
    cam.data.type, cam.data.ortho_scale = "ORTHO", scale
    cam.location = (*xy, z)
    sc.camera = cam
    return cam


def render_linear():
    """Render and return the linear image as (h, w, 4) float32, row 0 = bottom."""
    sc = bpy.context.scene
    bpy.ops.render.render()
    tmp = tempfile.mkdtemp(prefix="archviz_control_")
    try:
        path = os.path.join(tmp, "r.exr")
        sc.render.image_settings.file_format = "OPEN_EXR"
        bpy.data.images["Render Result"].save_render(path)
        im = bpy.data.images.load(path)
        a = np.empty(len(im.pixels), dtype=np.float32)
        im.pixels.foreach_get(a)
        w, h = im.size
        bpy.data.images.remove(im)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return a.reshape(h, w, 4)
