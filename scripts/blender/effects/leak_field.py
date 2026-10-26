"""Leak field: per point, how far below the first surface straight above it (a raycast up from just
inside the wall) -> `leak_d` and `leak_ok`. Runoff streaks read these to hang drips under drip edges.

It must be the FIRST modifier on an object: after the chips, rays slip through the chip-band seam and
a wrong leak_d spreads over a whole coarse triangle (light triangles under an arris).
"""
import bpy

from materials.shared.nodes import G


def leak_field_group(name="LEAK FIELD", inset=0.02, reach=6.0):
    """GN: per point, metres below the first surface straight above it (raycast up from `inset` inside the wall) -> `leak_d`, `leak_ok`. Reused if it exists (other objects' modifiers point at it)."""
    ng = bpy.data.node_groups.get(name)
    if ng:
        return ng
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.is_modifier = True
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    b = G(ng, clear=True)
    gi = b.n("NodeGroupInput", (-800, 0)); go = b.n("NodeGroupOutput", (900, 0))
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
    d = b.math("SUBTRACT", hz.outputs["Z"], pz.outputs["Z"], (150, -350))
    geo = b.store(gi.outputs[0], "leak_d", "FLOAT", d, (350, 0))
    geo = b.store(geo, "leak_ok", "FLOAT", ray.outputs["Is Hit"], (600, 0))
    b.L(geo, go.inputs[0])
    return ng


def add_leak_field(obj):
    """Add LEAK FIELD as the FIRST modifier: run after chips, rays slip through the chip-band seam and a wrong leak_d spreads over whole coarse triangles (light triangles under an arris)."""
    mod = obj.modifiers.new("LEAK FIELD", "NODES")
    mod.node_group = leak_field_group()
    obj.modifiers.move(obj.modifiers.find(mod.name), 0)
    return mod
