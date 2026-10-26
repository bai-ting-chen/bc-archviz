"""Rhino import: a .3dm brings geometry only. Layers, blocks and named views become collections,
instances and cameras; any material that rides along is discarded (materials are built in Blender).
"""
import os

import bpy


def import_rhino(path, collection_name=None):
    """Import a .3dm as geometry only. Layers -> nested collections, blocks -> instances,
    named views -> cameras. Any material that rides along is discarded."""
    before = set(bpy.data.materials)
    bpy.ops.import_3dm.some_data(
        filepath=path, import_layers_as_empties=False, import_instances=True,
        import_named_views=True, import_views=False, import_hidden_objects=False,
        import_hidden_layers=False, merge_by_distance=True)
    for m in set(bpy.data.materials) - before:
        bpy.data.materials.remove(m)
    root = bpy.data.collections.get(collection_name or os.path.splitext(os.path.basename(path))[0])
    for ob in root.all_objects if root else ():
        if ob.type == "MESH":
            ob.data.materials.clear()
    return root
