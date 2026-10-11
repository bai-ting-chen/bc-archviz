"""Geometry Nodes scatter for small instances: leaf litter, climbers, shrub foliage (run in Blender).

    group = scatter_group()
    leaf = leaf_proto("PROTO_DRY_LEAF", 0.07, 0.045, 0.012, material)
    scatter(objs, leaf, density=0.35, z_max=0.5, seed=3, patch=0.42)

Points are distributed on each target's faces where Z < `z_max` AND a 0.6/m noise > `patch`
(0 = everywhere), then instanced with random rotation and 0.6-1.3 x `scale`. The patch threshold
is sensitive near 0.5: on one wall 0.42 blanketed it, 0.48 gave patches, 0.53 left nothing.
Inputs are set through wear.set_input (Blender 5.2: mod["id"] = v raises).
"""
import bpy

from wear import set_input


def scatter_group(name="SCATTER"):
    """GN group: distribute points below a height and inside a noise patch, instance with random rotation/scale."""
    ng = bpy.data.node_groups.get(name)
    if ng:
        return ng
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    it = ng.interface
    it.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    for nm, typ in (("Instance", "NodeSocketObject"), ("Density", "NodeSocketFloat"), ("Scale", "NodeSocketFloat"),
                    ("Z Max", "NodeSocketFloat"), ("Seed", "NodeSocketInt"), ("Keep Source", "NodeSocketBool"),
                    ("Patchiness", "NodeSocketFloat")):
        it.new_socket(nm, in_out="INPUT", socket_type=typ)
    it.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N, L = ng.nodes, ng.links
    gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
    pos = N.new("GeometryNodeInputPosition"); sep = N.new("ShaderNodeSeparateXYZ")
    L.new(pos.outputs[0], sep.inputs[0])
    below = N.new("FunctionNodeCompare"); below.data_type = "FLOAT"; below.operation = "LESS_THAN"
    L.new(sep.outputs["Z"], below.inputs["A"]); L.new(gi.outputs["Z Max"], below.inputs["B"])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.6
    patch = N.new("FunctionNodeCompare"); patch.data_type = "FLOAT"; patch.operation = "GREATER_THAN"
    L.new(nz.outputs[0], patch.inputs["A"]); L.new(gi.outputs["Patchiness"], patch.inputs["B"])
    both = N.new("FunctionNodeBooleanMath"); both.operation = "AND"
    L.new(below.outputs[0], both.inputs[0]); L.new(patch.outputs[0], both.inputs[1])
    dist = N.new("GeometryNodeDistributePointsOnFaces")
    L.new(gi.outputs["Geometry"], dist.inputs["Mesh"]); L.new(both.outputs[0], dist.inputs["Selection"])
    L.new(gi.outputs["Density"], dist.inputs["Density"]); L.new(gi.outputs["Seed"], dist.inputs["Seed"])
    oi = N.new("GeometryNodeObjectInfo"); oi.transform_space = "RELATIVE"
    L.new(gi.outputs["Instance"], oi.inputs["Object"])
    rot = N.new("FunctionNodeRandomValue"); rot.data_type = "FLOAT_VECTOR"
    rot.inputs["Max"].default_value = (6.2832, 6.2832, 6.2832)
    rs = N.new("FunctionNodeRandomValue"); rs.data_type = "FLOAT"
    rs.inputs["Min"].default_value = 0.6; rs.inputs["Max"].default_value = 1.3
    ms = N.new("ShaderNodeMath"); ms.operation = "MULTIPLY"
    L.new(rs.outputs["Value"], ms.inputs[0]); L.new(gi.outputs["Scale"], ms.inputs[1])
    inst = N.new("GeometryNodeInstanceOnPoints")
    L.new(dist.outputs["Points"], inst.inputs["Points"]); L.new(oi.outputs["Geometry"], inst.inputs["Instance"])
    L.new(rot.outputs["Value"], inst.inputs["Rotation"]); L.new(ms.outputs[0], inst.inputs["Scale"])
    keep = N.new("GeometryNodeSwitch"); keep.input_type = "GEOMETRY"
    L.new(gi.outputs["Keep Source"], keep.inputs["Switch"]); L.new(gi.outputs["Geometry"], keep.inputs["True"])
    join = N.new("GeometryNodeJoinGeometry")
    L.new(keep.outputs[0], join.inputs[0]); L.new(inst.outputs[0], join.inputs[0])
    L.new(join.outputs[0], go.inputs[0])
    return ng


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


def scatter(objs, instance, density, scale=1.0, z_max=1e4, seed=0, keep_source=True, patch=0.0):
    """Add (or update) the SCATTER modifier on each object."""
    ng = scatter_group()
    for o in objs:
        mod = o.modifiers.get("SCATTER") or o.modifiers.new("SCATTER", "NODES")
        mod.node_group = ng
        for k, v in (("Instance", instance), ("Density", density), ("Scale", scale), ("Z Max", z_max),
                     ("Seed", seed), ("Keep Source", keep_source), ("Patchiness", patch)):
            set_input(mod, k, v)
