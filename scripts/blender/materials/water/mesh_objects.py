"""Mesh objects; implementation for water.mesh."""
import bpy
import numpy as np


def _finish(me, material, smooth=True):
    if material is not None:
        me.materials.append(material)
    if smooth and len(me.polygons):
        me.polygons.foreach_set('use_smooth', np.ones(len(me.polygons), dtype=bool))
    me.update()
    return me


def _link(name, me, collection):
    ob = bpy.data.objects.new(name, me)
    (collection or bpy.context.scene.collection).objects.link(ob)
    return ob


def from_arrays(name, verts, faces, material=None, collection=None, smooth=True):
    """Object from vertices (N, 3) and a face list (any polygon sizes)."""
    me = bpy.data.meshes.new(name)
    me.from_pydata(np.asarray(verts, float).tolist(), [], [list(map(int, f)) for f in faces])
    return _link(name, _finish(me, material, smooth), collection)
