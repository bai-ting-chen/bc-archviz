"""Concrete boards; canonical implementation behind concrete."""

from materials.shared.nodes import G, sock

from materials.shared.pbr_maps import _ph_maps
from materials.shared.principled import _principled
from materials.shared.map_measure import map_mean

def vertical_boards(mat, cylinder=None, strip_m=0.9, strip_tone=(0.90, 1.08), macro=(0.85, 1.10),
                    flatten=0.4):
    """Turn a board-formed map 90 deg (marks vertical) on an albedo_material.

    Flat projection fed by (z, along-wall): planar walls use x + y; `cylinder=(cx, cy, r)` uses
    arc length, so a drum gets no box-projection stretch. Adds per-strip tone (white noise per
    `strip_m` strip) x low-frequency mottling, and flattens the map's stains toward its mean by
    `flatten` (repeating marks read as tiling)."""
    N, L = mat.node_tree.nodes, mat.node_tree.links
    mapping = N["Mapping"]
    pos = mapping.inputs["Vector"].links[0].from_socket
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(pos, sep.inputs[0])
    comb = N.new("ShaderNodeCombineXYZ"); comb.label = "u = z, v = along wall"
    L.new(sep.outputs["Z"], comb.inputs["X"])
    if cylinder:
        cx, cy, r = cylinder
        dx = N.new("ShaderNodeMath"); dx.operation = "SUBTRACT"; dx.inputs[1].default_value = cx
        dy = N.new("ShaderNodeMath"); dy.operation = "SUBTRACT"; dy.inputs[1].default_value = cy
        at = N.new("ShaderNodeMath"); at.operation = "ARCTAN2"
        along = N.new("ShaderNodeMath"); along.operation = "MULTIPLY"; along.inputs[1].default_value = r
        L.new(sep.outputs["X"], dx.inputs[0]); L.new(sep.outputs["Y"], dy.inputs[0])
        L.new(dy.outputs[0], at.inputs[0]); L.new(dx.outputs[0], at.inputs[1]); L.new(at.outputs[0], along.inputs[0])
    else:
        along = N.new("ShaderNodeMath"); along.operation = "ADD"
        L.new(sep.outputs["X"], along.inputs[0]); L.new(sep.outputs["Y"], along.inputs[1])
    L.new(along.outputs[0], comb.inputs["Y"])
    L.new(comb.outputs[0], mapping.inputs["Vector"])
    for n in N:
        if n.type == "TEX_IMAGE":
            n.projection = "FLAT"

    div = N.new("ShaderNodeMath"); div.operation = "DIVIDE"; div.inputs[1].default_value = strip_m
    flo = N.new("ShaderNodeMath"); flo.operation = "FLOOR"
    wn = N.new("ShaderNodeTexWhiteNoise"); wn.noise_dimensions = "1D"
    L.new(along.outputs[0], div.inputs[0]); L.new(div.outputs[0], flo.inputs[0]); L.new(flo.outputs[0], wn.inputs["W"])
    r1 = N.new("ShaderNodeMapRange"); r1.label = "strip tone"
    r1.inputs["To Min"].default_value, r1.inputs["To Max"].default_value = strip_tone
    L.new(wn.outputs["Value"], r1.inputs["Value"])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.35; nz.inputs["Detail"].default_value = 3
    L.new(pos, nz.inputs["Vector"])
    r2 = N.new("ShaderNodeMapRange"); r2.label = "macro mottle"
    r2.inputs["From Min"].default_value, r2.inputs["From Max"].default_value = 0.35, 0.65
    r2.inputs["To Min"].default_value, r2.inputs["To Max"].default_value = macro
    L.new(nz.outputs[0], r2.inputs["Value"])
    mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    L.new(r1.outputs[0], mul.inputs[0]); L.new(r2.outputs[0], mul.inputs[1])

    bsdf = _principled(mat)
    gain = next((n for n in N if n.label == "albedo gain"), None)
    if flatten and gain is not None:
        diff = next(n for n in N if n.type == "TEX_IMAGE" and n.image.colorspace_settings.name == "sRGB")
        flat = N.new("ShaderNodeMix"); flat.data_type = "RGBA"; flat.label = "flatten stains"
        flat.inputs["Factor"].default_value = flatten
        L.new(diff.outputs["Color"], sock(flat.inputs, "A"))
        sock(flat.inputs, "B").default_value = (*mat["map_mean"], 1)
        L.new(sock(flat.outputs, "Result"), gain.inputs[0])
    src = bsdf.inputs["Base Color"].links[0].from_socket
    tone = N.new("ShaderNodeVectorMath"); tone.operation = "SCALE"; tone.label = "strip x macro"
    L.new(src, tone.inputs[0]); L.new(mul.outputs[0], tone.inputs["Scale"])
    L.new(tone.outputs[0], bsdf.inputs["Base Color"])
    return mat
