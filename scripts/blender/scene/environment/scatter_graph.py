"""Scatter graph; implementation for scatter."""
import bpy


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
