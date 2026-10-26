"""Terrain objects; implementation for terrain."""
import bpy


def add_terrain(group, material, name="TERRAIN", collection=None):
    """An empty mesh object carrying the landform modifier (the GN group makes the geometry)."""
    from effects.edge_wear import set_input
    ob = bpy.data.objects.new(name, bpy.data.meshes.new(name))
    (collection or bpy.context.scene.collection).objects.link(ob)
    mod = ob.modifiers.new("LANDFORM", "NODES"); mod.node_group = group
    set_input(mod, "Material", material)
    return ob
