# Rerun after a Blender upgrade: blender -b --factory-startup --python scripts/controls/light_units.py
# Control: how Cycles 5.2 scales light power. Irradiance on a white Lambert plane read from the
# linear render (pixel = albedo * E / pi). World must be truly black: a new world's 0.05 grey
# background adds pi*0.05 = 0.157 W/m2 (first seen as a mysterious +8 %).
import math
import os
import tempfile

import bpy
import numpy as np

D = 2.0          # light height above the plane, m
P = 100.0        # Blender W


def scene(kind, **kw):
    bpy.ops.wm.read_homefile(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples, sc.cycles.use_denoising = 256, False
    sc.cycles.use_adaptive_sampling = False
    sc.render.resolution_x = sc.render.resolution_y = 64
    sc.view_settings.view_transform = "Standard"
    sc.world = bpy.data.worlds.new("black")
    sc.world.use_nodes = True
    sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.0
    bpy.ops.mesh.primitive_plane_add(size=0.2)
    m = bpy.data.materials.new("white"); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (1, 1, 1, 1); b.inputs["Roughness"].default_value = 1
    b.inputs["Specular IOR Level"].default_value = 0.0
    bpy.context.object.data.materials.append(m)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam)
    cam.data.type = "ORTHO"; cam.data.ortho_scale = 0.1
    cam.location = (0, 0, 0.5); sc.camera = cam
    ld = bpy.data.lights.new("L", kind); ld.energy = P
    for k, v in kw.items():
        setattr(ld, k, v)
    lo = bpy.data.objects.new("L", ld); sc.collection.objects.link(lo)
    lo.location = (0, 0, D)
    bpy.ops.render.render()
    img = bpy.data.images["Render Result"]
    tmp = os.path.join(tempfile.gettempdir(), "light_units_control.exr")
    sc.render.image_settings.file_format = "OPEN_EXR"
    img.save_render(tmp)
    im = bpy.data.images.load(tmp)
    a = np.empty(len(im.pixels), dtype=np.float32); im.pixels.foreach_get(a)
    px = a.reshape(-1, 4)[:, 0].mean()
    os.remove(tmp)
    return px * math.pi        # E in Blender W/m2 (albedo 1)


E_point = P / (4 * math.pi * D * D)
rows = [("POINT r=0", scene("POINT", shadow_soft_size=0.0)),
        ("SPOT 60deg r=0", scene("SPOT", spot_size=math.radians(60), spot_blend=0.0, shadow_soft_size=0.0)),
        ("SPOT 30deg r=0", scene("SPOT", spot_size=math.radians(30), spot_blend=0.0, shadow_soft_size=0.0)),
        ("AREA 0.1 sq spread180", scene("AREA", size=0.1)),
        ("AREA 0.1 sq spread60", scene("AREA", size=0.1, spread=math.radians(60))),
        ("AREA 1.0x0.02 rect", scene("AREA", shape="RECTANGLE", size=1.0, size_y=0.02))]
print("E if point-equivalent P/(4 pi d2) =", round(E_point, 4))
print("E if Lambert emitter P/(pi d2)    =", round(P / (math.pi * D * D), 4))
for n, e in rows:
    print(f"{n:26s} E = {e:.4f}")
