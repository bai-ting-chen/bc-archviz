# Rerun after a Blender upgrade: blender -b --factory-startup --python scripts/controls/light_units.py
# Control: how Cycles 5.2 scales light power. Irradiance on a white Lambert plane read from the
# linear render (pixel = albedo * E / pi). World must be truly black: a new world's 0.05 grey
# background adds pi*0.05 = 0.157 W/m2 (first seen as a mysterious +8 %).
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _scene import black_scene, ortho_camera, render_linear, white_lambert  # noqa: E402

D = 2.0          # light height above the plane, m
P = 100.0        # Blender W


def scene(kind, **kw):
    sc = black_scene(256, 64)
    bpy.ops.mesh.primitive_plane_add(size=0.2)
    bpy.context.object.data.materials.append(white_lambert())
    ortho_camera(0.5, 0.1)
    ld = bpy.data.lights.new("L", kind); ld.energy = P
    for k, v in kw.items():
        setattr(ld, k, v)
    lo = bpy.data.objects.new("L", ld); sc.collection.objects.link(lo)
    lo.location = (0, 0, D)
    return render_linear()[:, :, 0].mean() * math.pi       # E in Blender W/m2 (albedo 1)


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
