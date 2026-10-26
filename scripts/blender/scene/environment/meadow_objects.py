"""Meadow objects; implementation for scatter."""
import bpy
from effects.edge_wear import set_input


def frustum_tangents(cam, res, margin=1.15):
    """Half-tangents (x, y) of a camera's view incl. vertical lens shift, for the meadow frustum mask."""
    cd = cam.data
    tx = cd.sensor_width / 2 / cd.lens * margin
    ty = tx * res[1] / res[0] + abs(cd.shift_y) * cd.sensor_width / cd.lens + 0.1
    return tx, ty


def meadow_layer(name, group, terrain, collection, camera, target_collection=None, **inputs):
    """One meadow layer object (empty mesh + MEADOW_LAYER modifier); inputs by name, '_' for spaces."""
    ob = bpy.data.objects.new(name, bpy.data.meshes.new(name))
    (target_collection or bpy.context.scene.collection).objects.link(ob)
    mod = ob.modifiers.new("MEADOW", "NODES")
    mod.node_group = group
    for k, v in dict(Terrain=terrain, Collection=collection, Camera=camera, **inputs).items():
        set_input(mod, k.replace("_", " "), v)
    return ob
