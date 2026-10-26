"""Albedo; canonical implementation behind pbr."""

from materials.shared.map_measure import map_mean

from materials.shared.pbr_build import pbr_material

from materials.shared.principled import _principled

def albedo_material(tex_id, name, target, scale=1.0):
    """pbr_material whose base colour averages `target` (linear RGB)."""
    mean = map_mean(tex_id)
    m = pbr_material(tex_id, name=name, scale=scale)
    N, L = m.node_tree.nodes, m.node_tree.links
    bsdf = _principled(m)
    src = bsdf.inputs["Base Color"].links[0].from_socket
    gain = N.new("ShaderNodeVectorMath"); gain.operation = "MULTIPLY"; gain.label = "albedo gain"
    gain.location = (250, 350)
    gain.inputs[1].default_value = tuple(t / mm for t, mm in zip(target, mean))
    L.new(src, gain.inputs[0]); L.new(gain.outputs[0], bsdf.inputs["Base Color"])
    m["albedo_target"] = list(target)
    m["map_mean"] = list(mean)
    return m
