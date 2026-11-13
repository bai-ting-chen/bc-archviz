"""Leak field: per point, how far below the first surface straight above it (a raycast up from just
inside the wall) -> `leak_d` and `leak_ok`. Runoff streaks read these to hang drips under drip edges.

Rays go world-up; inset, reach and leak_d are world metres, so an unapplied rotation or uniform scale is fine. A closed wall's
ray hits its own top face from inside. A wall with no thickness (a single-face plane, a mesh open at the
top) hits nothing; with Top Fallback on, its leak_d is measured from the object's highest point, one top
per object (a stepped sheet needs one object per height, or thickness).

It must be the FIRST modifier on an object: after the chips, rays slip through the chip-band seam and
a wrong leak_d spreads over a whole coarse triangle (light triangles under an arris).
"""
import bpy

from materials.shared.node_graph import NodeGraph


def leak_field_group(name="LEAK FIELD", inset=0.02, reach=6.0):
    """GN: per point, metres below the first surface straight above it (raycast up from `inset` inside the wall) -> `leak_d`, `leak_ok`; a miss falls back to the object's top (Top Fallback). Reused if it exists (other objects' modifiers point at it)."""
    ng = bpy.data.node_groups.get(name)
    if ng:
        return ng
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.is_modifier = True
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    fallback = ng.interface.new_socket("Top Fallback", in_out="INPUT", socket_type="NodeSocketBool")
    fallback.default_value = True  # a miss (no thickness) measures leak_d from the object's top
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    b = NodeGraph(ng, clear=True)
    gi = b.node_with_props("NodeGroupInput", (-1000, 0)); go = b.node_with_props("NodeGroupOutput", (1100, 0))
    pos = b.node_with_props("GeometryNodeInputPosition", (-1000, -300)).outputs[0]
    nrm = b.node_with_props("GeometryNodeInputNormal", (-1000, -450)).outputs[0]
    # gravity is world -Z: the object's world matrix and its inverse (an unapplied rotation stays correct)
    me = b.node_with_props("GeometryNodeSelfObject", (-1000, -800))
    info = b.node_with_props("GeometryNodeObjectInfo", (-800, -800), transform_space="ORIGINAL")
    b.link(me.outputs[0], info.inputs["Object"])
    to_world = info.outputs["Transform"]
    inv = b.node_with_props("FunctionNodeInvertMatrix", (-600, -800)); b.link(to_world, inv.inputs[0])
    up = b.node_with_props("FunctionNodeTransformDirection", (-450, -700)); b.link(inv.outputs[0], up.inputs[1])
    up.inputs[0].default_value = (0, 0, 1)
    up_n = b.node_with_props("ShaderNodeVectorMath", (-300, -700), operation="NORMALIZE"); b.link(up.outputs[0], up_n.inputs[0])
    # object units per world metre: inset and reach are given in metres
    per_m = b.node_with_props("ShaderNodeVectorMath", (-300, -900), operation="LENGTH"); b.link(up.outputs[0], per_m.inputs[0])
    ins = b.node_with_props("ShaderNodeVectorMath", (-800, -400), operation="SCALE")
    b.link(nrm, ins.inputs[0]); b.link(b.math("MULTIPLY", per_m.outputs["Value"], -inset, (-950, -550)), ins.inputs["Scale"])
    src = b.node_with_props("ShaderNodeVectorMath", (-650, -350), operation="ADD")
    b.link(pos, src.inputs[0]); b.link(ins.outputs[0], src.inputs[1])
    ray = b.node_with_props("GeometryNodeRaycast", (-250, -250), data_type="FLOAT")
    b.link(gi.outputs[0], ray.inputs["Target Geometry"]); b.link(src.outputs[0], ray.inputs["Source Position"])
    b.link(up_n.outputs[0], ray.inputs["Ray Direction"])
    b.link(b.math("MULTIPLY", per_m.outputs["Value"], reach, (-450, -950)), ray.inputs["Ray Length"])

    def world_z(vec, location):
        """World Z (m) of an object-space point."""
        wp = b.node_with_props("FunctionNodeTransformPoint", location); b.link(vec, wp.inputs[0]); b.link(to_world, wp.inputs[1])
        sz = b.node_with_props("ShaderNodeSeparateXYZ", (location[0] + 150, location[1])); b.link(wp.outputs[0], sz.inputs[0])
        return sz.outputs["Z"]

    hit_z = world_z(ray.outputs["Hit Position"], (-50, -300))
    point_z = world_z(pos, (-50, -450))
    # a miss: the object's highest point (world Z) stands in for the drip edge
    top = b.node_with_props("GeometryNodeAttributeStatistic", (150, -650), data_type="FLOAT", domain="POINT")
    b.link(gi.outputs[0], top.inputs["Geometry"]); b.link(point_z, top.inputs["Attribute"])
    edge_z = b.node_with_props("GeometryNodeSwitch", (350, -300), input_type="FLOAT")
    b.link(ray.outputs["Is Hit"], edge_z.inputs["Switch"])
    b.link(top.outputs["Max"], edge_z.inputs["False"]); b.link(hit_z, edge_z.inputs["True"])
    d = b.math("SUBTRACT", edge_z.outputs[0], point_z, (550, -350))
    ok = b.node_with_props("FunctionNodeBooleanMath", (550, -550), operation="OR")
    b.link(ray.outputs["Is Hit"], ok.inputs[0]); b.link(gi.outputs["Top Fallback"], ok.inputs[1])
    geo = b.store_attribute(gi.outputs[0], "leak_d", "FLOAT", d, (750, 0))
    geo = b.store_attribute(geo, "leak_ok", "FLOAT", ok.outputs[0], (950, 0))
    b.link(geo, go.inputs[0])
    return ng


def add_leak_field(obj):
    """Add LEAK FIELD as the FIRST modifier: run after chips, rays slip through the chip-band seam and a wrong leak_d spreads over whole coarse triangles (light triangles under an arris)."""
    mod = obj.modifiers.new("LEAK FIELD", "NODES")
    mod.node_group = leak_field_group()
    obj.modifiers.move(obj.modifiers.find(mod.name), 0)
    return mod
