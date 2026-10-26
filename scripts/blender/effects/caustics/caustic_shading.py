"""Caustic shading; implementation for gn_caustics."""
import math
import bpy
from materials.shared.nodes import G
from materials.shared.nodes import sock


def caustic_sheet_material(name="CAUSTIC_SHEET", floor_tex=None, floor_tile_m=2.0,
                           wall_albedo=(0.60, 0.79, 0.83), floor_albedo=(0.5, 0.5, 0.5)):
    """Transparent + Emission(albedo * E / pi). Floor albedo from the same world-box-mapped texture
    the floor uses (or `floor_albedo` without one -- set it to the floor's real albedo); walls a
    constant glaze colour."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    N = G(nt, clear=False).n
    at = N("ShaderNodeAttribute", (-900, 200)); at.attribute_name = "E"
    fl = N("ShaderNodeAttribute", (-900, -100)); fl.attribute_name = "onfloor"
    pi = N("ShaderNodeMath", (-700, 200)); pi.operation = "DIVIDE"; pi.inputs[1].default_value = math.pi
    nt.links.new(at.outputs["Fac"], pi.inputs[0])
    albedo = N("ShaderNodeMix", (-450, -50)); albedo.data_type = "RGBA"
    sock(albedo.inputs, "A").default_value = (*wall_albedo, 1)
    nt.links.new(fl.outputs["Fac"], albedo.inputs["Factor"])
    sock(albedo.inputs, "B").default_value = (*floor_albedo, 1)
    if floor_tex:
        geo = N("ShaderNodeNewGeometry", (-1100, -300))
        mp = N("ShaderNodeMapping", (-900, -300)); mp.inputs["Scale"].default_value = (1 / floor_tile_m,) * 3
        nt.links.new(geo.outputs["Position"], mp.inputs["Vector"])
        tx = N("ShaderNodeTexImage", (-700, -300))
        tx.image = bpy.data.images.load(floor_tex, check_existing=True)
        tx.projection, tx.projection_blend = "BOX", 0.2
        nt.links.new(mp.outputs["Vector"], tx.inputs["Vector"])
        nt.links.new(tx.outputs["Color"], sock(albedo.inputs, "B"))
    em = N("ShaderNodeEmission", (-200, 0))
    nt.links.new(sock(albedo.outputs, "Result"), em.inputs["Color"])
    nt.links.new(pi.outputs[0], em.inputs["Strength"])
    tr = N("ShaderNodeBsdfTransparent", (-200, 200))
    add = N("ShaderNodeAddShader", (0, 100))
    nt.links.new(tr.outputs[0], add.inputs[0]); nt.links.new(em.outputs[0], add.inputs[1])
    out = N("ShaderNodeOutputMaterial", (200, 100))
    nt.links.new(add.outputs[0], out.inputs["Surface"])
    return mat
