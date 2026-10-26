"""Pavers; canonical implementation behind stone."""

from materials.shared.nodes import G, sock

from materials.shared.principled import _principled
from materials.shared.albedo import albedo_material

def long_pavers(tex_id, name, target, row=0.18, length=0.75, mortar=0.008, long_axis="Y", scale=0.5,
                tone=((0.95, 0.95, 0.95), (0.72, 0.72, 0.71)), mortar_color=(0.22, 0.22, 0.22)):
    """Running-bond strips over a concrete map. `long_axis` = world axis of the strips' length
    (read it from the vanishing point the long joints run to). Mortar < 8 mm vanishes at frame
    scale; joints recessed by bump."""
    m = albedo_material(tex_id, name, target, scale=scale)
    N, L = m.node_tree.nodes, m.node_tree.links
    geo = N.new("ShaderNodeNewGeometry")
    sep = N.new("ShaderNodeSeparateXYZ"); comb = N.new("ShaderNodeCombineXYZ")
    L.new(geo.outputs["Position"], sep.inputs["Vector"])
    other = "X" if long_axis.upper() == "Y" else "Y"
    L.new(sep.outputs[long_axis.upper()], comb.inputs["X"]); L.new(sep.outputs[other], comb.inputs["Y"])
    br = N.new("ShaderNodeTexBrick"); br.offset = 0.5; br.offset_frequency = 1
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Brick Width"].default_value = length
    br.inputs["Row Height"].default_value = row
    br.inputs["Mortar Size"].default_value = mortar
    br.inputs["Mortar Smooth"].default_value = 0.3
    br.inputs["Bias"].default_value = 0.0
    br.inputs["Color1"].default_value = (*tone[0], 1); br.inputs["Color2"].default_value = (*tone[1], 1)
    br.inputs["Mortar"].default_value = (*mortar_color, 1)
    L.new(comb.outputs["Vector"], br.inputs["Vector"])
    bsdf = _principled(m)
    src = bsdf.inputs["Base Color"].links[0].from_socket
    mul = N.new("ShaderNodeMix"); mul.data_type = "RGBA"; mul.blend_type = "MULTIPLY"
    mul.inputs["Factor"].default_value = 1.0
    L.new(src, sock(mul.inputs, "A")); L.new(br.outputs["Color"], sock(mul.inputs, "B"))
    L.new(sock(mul.outputs, "Result"), bsdf.inputs["Base Color"])
    bump = N.new("ShaderNodeBump"); bump.inputs["Distance"].default_value = 0.004; bump.invert = True
    L.new(br.outputs["Fac"], bump.inputs["Height"])
    if bsdf.inputs["Normal"].links:
        L.new(bsdf.inputs["Normal"].links[0].from_node.outputs["Normal"], bump.inputs["Normal"])
    L.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m
