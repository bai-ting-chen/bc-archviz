
import os as _os
import sys as _sys
_CONTROLS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in [_CONTROLS] + [_os.path.join(_CONTROLS, _t) for _t in ('archviz', 'tile', 'material', 'effects', 'water', 'lighting', 'environment', 'regression')]:
    if _d not in _sys.path:
        _sys.path.append(_d)
# Rerun after a Blender upgrade: blender -b --factory-startup --python scripts/controls/water/mnee_water.py
# Control: does light from a lamp above reach a submerged receiver (pool floor) through flat water?
# Camera views the floor obliquely (no specular image of the lamp in frame); a "no water" case gives
# the expected irradiance. Result on Blender 5.2.2: box 0, one flat quad 0, diced 40x40 plane lit.
import math
import os
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "blender"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import materials.water.water as _mat_water
from _scene import black_scene, render_linear, white_lambert  # noqa: E402


def box(name, x0, y0, z0, x1, y1, z1, top_only=False, cuts=0):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x, v.co.y, v.co.z = (x0 if v.co.x < 0 else x1), (y0 if v.co.y < 0 else y1), (z0 if v.co.z < 0 else z1)
    if top_only:
        bm.normal_update()
        if cuts:
            bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)
            bm.normal_update()
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z < 0.5], context="FACES")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def run(kind="SPOT", water="plane", mnee=True, volume=False, caustics=True, samples=512, blur=0.0, smooth=True, cuts=0):
    sc = black_scene(samples, 64)
    import importlib
    importlib.reload(_mat_water)
    sc.cycles.blur_glossy = blur
    sc.cycles.caustics_refractive = caustics
    floor = box("floor", -2, -2, -1.3, 2, 2, -1.2)          # pool floor (receiver), Lambert 0.8
    floor.data.materials.append(white_lambert(albedo=0.8))
    floor.cycles.is_caustics_receiver = mnee
    if water != "none":
        w = box("water", -2, -2, -1.2 + 0.0005, 2, 2, 0.0, top_only=(water == "plane"), cuts=cuts)
        wm = _mat_water.pool_water("W", density=1.0, ripple_m=0.0)
        if not volume:
            for l in list(wm.node_tree.links):
                if l.to_socket.name == "Volume":
                    wm.node_tree.links.remove(l)
        w.data.materials.append(wm)
        if smooth:
            _mat_water.smooth_flat(w)
        w.cycles.is_caustics_caster = mnee
    ld = bpy.data.lights.new("L", kind)
    ld.energy = 100.0
    if kind == "SPOT":
        ld.spot_size, ld.shadow_soft_size = math.radians(60), 0.03
    elif kind == "POINT":
        ld.shadow_soft_size = 0.03
    elif kind == "SUN":
        ld.energy, ld.angle = 5.0, math.radians(1.0)
    else:
        ld.size = 0.1
    ld.cycles.is_caustics_light = mnee
    lo = bpy.data.objects.new("L", ld); sc.collection.objects.link(lo)
    lo.location = (0, 0, 2.0)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam)
    cam.data.lens = 50
    cam.location = (0.0, -3.0, 1.0)
    cam.rotation_euler = (math.radians(90 - math.degrees(math.atan2(2.2, 3.0))), 0, 0)   # aim at floor centre
    sc.camera = cam
    px = render_linear()[:, :, :3]
    c = px[26:38, 26:38].reshape(-1, 3)
    return tuple(c.mean(0).round(4)), round(float(c.mean(1).std() / max(c.mean(), 1e-6)), 3)


cases = [dict(water="none", kind="SPOT"), dict(water="box", kind="SPOT"), dict(water="plane", kind="SPOT"),
         dict(water="plane", kind="SPOT", cuts=40), dict(water="plane", kind="SUN", cuts=40),
         dict(water="plane", kind="SPOT", cuts=40, volume=True)]
for kw in cases:
    print("MNEE-TEST", kw, "floor centre rgb, rel. noise:", run(**kw))
