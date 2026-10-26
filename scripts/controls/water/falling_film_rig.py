"""Rotated wall, pool, proxy and water-film integration rig."""

import os as _os
import sys as _sys
_CONTROLS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in [_CONTROLS] + [_os.path.join(_CONTROLS, _t) for _t in ('archviz', 'tile', 'material', 'effects', 'water', 'lighting', 'environment', 'regression')]:
    if _d not in _sys.path:
        _sys.path.append(_d)
import math
import bpy
import numpy as np
import _scene
from materials.water import water as water_mat
from materials.water import build, curtain

def scene(OUT, RES, SAMPLES):
    """Build the same film integration scene."""
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
    proxy.location = (.7, -.4, .3); proxy.rotation_euler = (0, 0, .5)   # transformed on purpose
    sc.render.image_settings.media_type = 'MULTI_LAYER_IMAGE'          # as a finals scene may leave it

    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.lens = 28
    target = origin + along * (L * .55) + out * .3 + np.array([0, 0, -H * .55])
    cam.location = origin + along * (L * .5) + out * 5.0 + np.array([0, 0, -1.2]) - along * 1.5
    d = target - cam.location; cam.rotation_euler = (math.atan2(math.hypot(d[0], d[1]), -d[2]), 0, math.atan2(d[1], d[0]) - math.pi / 2)

    lip = curtain.Lip(origin=origin, along=along, out=out, length=L, drop=H)
    setup = build.Setup(cell=.004)
    objs, stats = build.falling_film(lip, POOL_Z, film_mat, foam_mat, pool_mat, OUT / 'falling_film_ripple.exr', proxy, setup)

    return sc, objs, stats, proxy, lip, setup, H
