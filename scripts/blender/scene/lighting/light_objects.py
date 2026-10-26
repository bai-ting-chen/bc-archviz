"""Light objects; implementation for interior."""
import bpy


def _light_obj(name, kind, loc, rot=(0.0, 0.0, 0.0), coll=None):
    ob = bpy.data.objects.get(name)
    if ob is not None and ob.type != "LIGHT":
        raise ValueError(f"'{name}' is a {ob.type} object (e.g. imported from Rhino): give the light another name")
    ld = ob.data if ob is not None else (bpy.data.lights.get(name) or bpy.data.lights.new(name, kind))
    if ld.type != kind:
        ld.type = kind                        # re-run with another kind: switch, keep the datablock
        ld = bpy.data.lights[ld.name]         # re-fetch: the old handle keeps the old subclass
    ob = ob or bpy.data.objects.new(name, ld)
    coll = coll or bpy.context.scene.collection
    if ob.name not in coll.objects:
        coll.objects.link(ob)
    ob.location, ob.rotation_euler = loc, rot
    return ob, ld


def _warm(ld, kelvin):
    ld.color = (1.0, 1.0, 1.0)
    ld.use_temperature, ld.temperature = True, kelvin
