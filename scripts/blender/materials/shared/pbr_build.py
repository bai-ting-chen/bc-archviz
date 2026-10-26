"""Pbr build; canonical implementation behind pbr."""

import os

import bpy

from materials.shared.nodes import G, sock

from materials.shared.pbr_config import BUMP_DISTANCE

from materials.shared.pbr_maps import _img

def pbr_material(tex_id, name=None, scale=1.0, tint=None):
    """Material from a Poly Haven texture folder, box-mapped in world space at real-world size.

    scale: multiplies the texture's real-world size (2.0 = twice as large).
    tint: optional (r, g, b) multiplied into the base color.
    """
    import core.archviz as archviz
    from core.archviz import library, read_meta
    folder = library("polyhaven", "textures", tex_id)
    meta = read_meta(folder)
    maps = {k: os.path.join(folder, v) for k, v in meta["maps"].items()}
    w_mm, h_mm = meta.get("dimensions_mm", [1000, 1000])

    mat = bpy.data.materials.get(name or tex_id) or bpy.data.materials.new(name or tex_id)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    N, L = nt.nodes, nt.links
    out = N.new("ShaderNodeOutputMaterial"); out.location = (900, 0)
    bsdf = N.new("ShaderNodeBsdfPrincipled"); bsdf.location = (550, 0)
    L.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    geo = N.new("ShaderNodeNewGeometry"); geo.location = (-900, 0)
    mapping = N.new("ShaderNodeMapping"); mapping.location = (-700, 0)
    mapping.inputs["Scale"].default_value = (1000 / (w_mm * scale), 1000 / (h_mm * scale), 1000 / (w_mm * scale))
    L.new(geo.outputs["Position"], mapping.inputs["Vector"])

    diff = _img(N, maps["diff"], "sRGB", (-400, 300))
    L.new(mapping.outputs["Vector"], diff.inputs["Vector"])
    if tint:
        mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        sock(mix.inputs, "B").default_value = (*tint, 1.0)
        mix.location = (100, 300)
        L.new(diff.outputs["Color"], sock(mix.inputs, "A"))
        L.new(sock(mix.outputs, "Result"), bsdf.inputs["Base Color"])
    else:
        L.new(diff.outputs["Color"], bsdf.inputs["Base Color"])

    if "arm" in maps:  # R = AO (unused, Cycles computes it), G = roughness, B = metallic
        arm = _img(N, maps["arm"], "Non-Color", (-400, 0))
        L.new(mapping.outputs["Vector"], arm.inputs["Vector"])
        sep = N.new("ShaderNodeSeparateColor"); sep.location = (100, 0)
        L.new(arm.outputs["Color"], sep.inputs["Color"])
        L.new(sep.outputs["Green"], bsdf.inputs["Roughness"])
        L.new(sep.outputs["Blue"], bsdf.inputs["Metallic"])

    # Height map as bump: correct with box mapping, unlike tangent-space normal maps.
    if "disp" in maps:
        disp = _img(N, maps["disp"], "Non-Color", (-400, -300))
        L.new(mapping.outputs["Vector"], disp.inputs["Vector"])
        bump = N.new("ShaderNodeBump"); bump.location = (100, -300)
        bump.inputs["Distance"].default_value = BUMP_DISTANCE * scale
        L.new(disp.outputs["Color"], bump.inputs["Height"])
        L.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    mat["source"] = meta["source"]
    return mat
