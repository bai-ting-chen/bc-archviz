"""Caustic objects; implementation for gn_caustics."""
import bpy
from effects.caustics.caustic_graph import caustic_sheet_group
from effects.caustics.caustic_shading import caustic_sheet_material


def add_caustic_sheet(caster, receivers, occluders, sun_obj, ior=1.333, floor_tex=None,
                      floor_tile_m=2.0, name="CAUSTIC_SHEET", floor_albedo=(0.5, 0.5, 0.5)):
    """Create the overlay object with the GN modifier; inputs set on the modifier itself."""
    from mathutils import Vector
    import effects.edge_wear as wear
    me = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    mod = ob.modifiers.new("Wavefront Caustics", "NODES")
    mod.node_group = caustic_sheet_group()
    d = (sun_obj.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
    for k, v in (("Caster", caster), ("Receivers", receivers), ("Occluders", occluders),
                 ("Sun Direction", tuple(d)), ("Sun Irradiance", sun_obj.data.energy),
                 ("IOR Ratio", 1.0 / ior)):
        wear.set_input(mod, k, v)
    mat = caustic_sheet_material(floor_tex=floor_tex, floor_tile_m=floor_tile_m, floor_albedo=floor_albedo)
    me.materials.append(mat)
    next(n for n in mod.node_group.nodes if n.type == "SET_MATERIAL").inputs["Material"].default_value = mat
    ob.visible_shadow = False
    return ob
