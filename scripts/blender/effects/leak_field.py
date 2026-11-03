"""Leak field: per point, how far below the first surface straight above it (a raycast up from just
inside the wall) -> `leak_d` and `leak_ok`. Runoff streaks read these to hang drips under drip edges.

A closed wall's ray hits its own top face from inside. A wall with no thickness (a single-face plane, a
mesh open at the top) hits nothing; with Top Fallback on, its leak_d is measured from the object's top.

It must be the FIRST modifier on an object: after the chips, rays slip through the chip-band seam and
a wrong leak_d spreads over a whole coarse triangle (light triangles under an arris).
"""
import bpy

from materials.shared.nodes import G


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
    b = G(ng, clear=True)
    gi = b.n("NodeGroupInput", (-800, 0)); go = b.n("NodeGroupOutput", (1100, 0))
    pos = b.n("GeometryNodeInputPosition", (-800, -300)).outputs[0]
    nrm = b.n("GeometryNodeInputNormal", (-800, -450)).outputs[0]
    ins = b.n("ShaderNodeVectorMath", (-600, -400), operation="SCALE")
    b.L(nrm, ins.inputs[0]); ins.inputs["Scale"].default_value = -inset
    src = b.n("ShaderNodeVectorMath", (-450, -350), operation="ADD")
    b.L(pos, src.inputs[0]); b.L(ins.outputs[0], src.inputs[1])
    ray = b.n("GeometryNodeRaycast", (-250, -250), data_type="FLOAT")
    b.L(gi.outputs[0], ray.inputs["Target Geometry"]); b.L(src.outputs[0], ray.inputs["Source Position"])
    ray.inputs["Ray Direction"].default_value = (0, 0, 1)
    ray.inputs["Ray Length"].default_value = reach
    hz = b.n("ShaderNodeSeparateXYZ", (-50, -300)); b.L(ray.outputs["Hit Position"], hz.inputs[0])
    pz = b.n("ShaderNodeSeparateXYZ", (-50, -450)); b.L(pos, pz.inputs[0])
    # a miss: the object's highest point stands in for the drip edge
    box = b.n("GeometryNodeBoundBox", (-250, -650)); b.L(gi.outputs[0], box.inputs["Geometry"])
    bz = b.n("ShaderNodeSeparateXYZ", (-50, -650)); b.L(box.outputs["Max"], bz.inputs[0])
    edge_z = b.n("GeometryNodeSwitch", (150, -300), input_type="FLOAT")
    b.L(ray.outputs["Is Hit"], edge_z.inputs["Switch"])
    b.L(bz.outputs["Z"], edge_z.inputs["False"]); b.L(hz.outputs["Z"], edge_z.inputs["True"])
    d = b.math("SUBTRACT", edge_z.outputs[0], pz.outputs["Z"], (350, -350))
    ok = b.n("FunctionNodeBooleanMath", (350, -550), operation="OR")
    b.L(ray.outputs["Is Hit"], ok.inputs[0]); b.L(gi.outputs["Top Fallback"], ok.inputs[1])
    geo = b.store(gi.outputs[0], "leak_d", "FLOAT", d, (550, 0))
    geo = b.store(geo, "leak_ok", "FLOAT", ok.outputs[0], (800, 0))
    b.L(geo, go.inputs[0])
    return ng


def add_leak_field(obj):
    """Add LEAK FIELD as the FIRST modifier: run after chips, rays slip through the chip-band seam and a wrong leak_d spreads over whole coarse triangles (light triangles under an arris)."""
    mod = obj.modifiers.new("LEAK FIELD", "NODES")
    mod.node_group = leak_field_group()
    obj.modifiers.move(obj.modifiers.find(mod.name), 0)
    return mod
