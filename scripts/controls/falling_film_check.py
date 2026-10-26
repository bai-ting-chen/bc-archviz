"""Control: build a free-falling water film with the `water` package on a scene it was not written for, check it.

Scene: a 4 m wall turned 30 deg off the world axes, a 2.4 m drop into a pool, a camera looking along the wall.
Checks (printed as JSON, non-zero exit on failure): finite geometry, torn and folded fractions in range, strings and
drops present, film velocity up to sqrt(v0^2 + 2 g H), pool ripple field read back non-zero from its EXR, wet proxy
lying on the wall face, and a rendered thumbnail that is not empty.

Usage: blender -b --factory-startup --python-exit-code 1 --python falling_film_check.py -- <out_dir> [res=640] [samples=32]
Writes <out_dir>/falling_film_check.png, falling_film_ripple.exr, falling_film_check.json.
"""
import json
import math
import os
import sys
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "blender"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _scene
from materials import water as water_mat
from water import build, curtain

argv = sys.argv[sys.argv.index('--') + 1:]
OUT = Path(argv[0]); OUT.mkdir(parents=True, exist_ok=True)
opt = dict(a.split('=') for a in argv[1:])
RES = int(opt.get('res', 640)); SAMPLES = int(opt.get('samples', 32))

sc = _scene.black_scene(samples=SAMPLES, res=RES)
sc.render.resolution_y = int(RES * .75)
bg = sc.world.node_tree.nodes['Background']; bg.inputs['Color'].default_value = (.75, .78, .82, 1); bg.inputs['Strength'].default_value = 1.0
sc.view_settings.view_transform = 'AgX'

ang = math.radians(30); along = np.array([math.cos(ang), math.sin(ang), 0.]); out = np.array([math.sin(ang), -math.cos(ang), 0.])
L, H, Z_LIP, POOL_Z = 4.0, 2.4, 2.35, -.05
origin = np.array([1.0, 2.0, Z_LIP])

concrete = _scene.white_lambert('wall', .45)
bpy.ops.mesh.primitive_cube_add(size=1)
wall = bpy.context.object; wall.name = 'wall'
wall.scale = (L + 2, .3, Z_LIP + .6); wall.rotation_euler = (0, 0, ang)
wall.location = origin + along * (L / 2) - out * .15 + np.array([0, 0, -(Z_LIP + .6) / 2 + .0])
wall.data.materials.append(concrete)
pool_mat = water_mat.pool_water('control pool water')
bpy.ops.mesh.primitive_plane_add(size=1)
pool = bpy.context.object; pool.name = 'pool'
pool.scale = (L + 3, 4, 1); pool.rotation_euler = (0, 0, ang)
pool.location = origin + along * (L / 2) + out * 2 + np.array([0, 0, POOL_Z - Z_LIP])
pool.data.materials.append(pool_mat)
film_mat = bpy.data.materials.new('control film water'); film_mat.use_nodes = True
b = film_mat.node_tree.nodes['Principled BSDF']; b.inputs['Transmission Weight'].default_value = 1.0
b.inputs['IOR'].default_value = 1.333; b.inputs['Roughness'].default_value = 0.0
foam_mat = _scene.white_lambert('foam', .7)
proxy = bpy.data.objects.new('wet proxy', bpy.data.meshes.new('wet proxy')); sc.collection.objects.link(proxy)
proxy.hide_render = True

cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 28
target = origin + along * (L * .55) + out * .3 + np.array([0, 0, -H * .55])
cam.location = origin + along * (L * .5) + out * 5.0 + np.array([0, 0, -1.2]) - along * 1.5
d = target - cam.location; cam.rotation_euler = (math.atan2(math.hypot(d[0], d[1]), -d[2]), 0, math.atan2(d[1], d[0]) - math.pi / 2)

lip = curtain.Lip(origin=origin, along=along, out=out, length=L, drop=H)
setup = build.Setup(cell=.004)
objs, stats = build.falling_film(lip, POOL_Z, film_mat, foam_mat, pool_mat, OUT / 'falling_film_ripple.exr', proxy, setup)

checks = {}
co = np.empty(len(objs['film'].data.vertices) * 3, np.float32); objs['film'].data.vertices.foreach_get('co', co)
checks['film finite'] = bool(np.isfinite(co).all())
checks['torn fraction 0.03-0.40'] = .03 <= stats['torn'] <= .40
checks['folded fraction < 0.30'] = stats['folded'] < .30
checks['strings and drops present'] = stats['strings'] > 0 and stats['drops'] > 0
vel = np.empty(len(objs['film'].data.vertices) * 3, np.float32)
objs['film'].data.attributes['velocity'].data.foreach_get('vector', vel)
vmax = float(np.linalg.norm(vel.reshape(-1, 3), axis=1).max()); expect = math.sqrt(.35 ** 2 + 2 * 9.81 * H)
checks['velocity max ~ sqrt(v0^2+2gH)'] = abs(vmax - expect) < .1 * expect
lo, hi = stats.get('ripple_mm', (0, 0)); checks['ripple read back non-zero'] = lo < 0 < hi
pv = np.empty(len(proxy.data.vertices) * 3, np.float32); proxy.data.vertices.foreach_get('co', pv)
_, o = lip.local(pv.reshape(-1, 3)); checks['wet proxy on the wall face'] = bool(len(o)) and float(np.abs(o - setup.wet.gap).max()) < 1e-4
sc.render.filepath = str(OUT / 'falling_film_check.png'); bpy.ops.render.render(write_still=True)
img = bpy.data.images.load(str(OUT / 'falling_film_check.png')); px = np.empty(img.size[0] * img.size[1] * 4, np.float32); img.pixels.foreach_get(px)
checks['render not empty'] = float(px[0::4].std()) > .02
stats.update(velocity_max=vmax, velocity_expected=expect)
(OUT / 'falling_film_check.json').write_text(json.dumps(dict(checks=checks, stats=stats), indent=1, default=float))
print(json.dumps(dict(checks=checks, stats=stats), default=float))
if not all(checks.values()):
    raise SystemExit('falling_film_check FAILED: ' + ', '.join(k for k, v in checks.items() if not v))
