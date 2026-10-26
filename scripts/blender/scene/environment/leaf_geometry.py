"""Leaf geometry; implementation for scatter."""
import bpy


def leaf_proto(name, length, width, curl, material):
    """A small curled elliptical leaf (10-gon) in a hidden PROTOS collection; reused if present."""
    ob = bpy.data.objects.get(name)
    if ob:
        return ob
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, segments=10, radius=1.0)
    for v in bm.verts:
        x, y = v.co.x * length / 2, v.co.y * width / 2
        v.co = (x, y, curl * (x / length * 2) ** 2)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.materials.append(material)
    ob = bpy.data.objects.new(name, me)
    sc = bpy.context.scene
    pc = bpy.data.collections.get("PROTOS") or bpy.data.collections.new("PROTOS")
    if pc.name not in sc.collection.children:
        sc.collection.children.link(pc)
    pc.objects.link(ob)
    pc.hide_render = True
    return ob
