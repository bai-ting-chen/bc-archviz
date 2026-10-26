"""Gravel; canonical implementation behind ground."""

import bpy

from materials.shared.nodes import G, sock

from materials.shared.pbr_maps import _ph_maps

def displaced_ground(name="GRAVEL", tex_id="gray_rocks", relief_m=0.12, shift_m=-0.049):
    """Gravel ground with true displacement.
    Displacement: Scale = relief_m, Midlevel = -shift_m / relief_m."""
    maps, meta = _ph_maps(tex_id)
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = G(mat)
    g.frame("Maps (BoxUV)", (0.20, 0.24, 0.30))
    g.frame("Displacement (GeomDisplacedMesh, 2D)", (0.30, 0.25, 0.18))
    F_MAP, F_DISP = list(g.frames)
    uv = g.uv("BoxUV", (-1300, 0), F_MAP)
    diff = g.img(maps["diff"], "sRGB", (-1050, 300), F_MAP, uv, "diffuse")
    arm = g.img(maps["arm"], "Non-Color", (-1050, 0), F_MAP, uv, "arm")
    nor = g.img(maps["nor_gl"], "Non-Color", (-1050, -300), F_MAP, uv, "normal (GL)")
    hgt = g.img(maps["disp"], "Non-Color", (-1050, -600), F_DISP, uv, "height")
    sep = g.node("ShaderNodeSeparateColor", (-750, 0), F_MAP)
    g.link(arm.outputs["Color"], sep.inputs["Color"])
    nmap = g.node("ShaderNodeNormalMap", (-750, -300), F_MAP)
    nmap.uv_map = "BoxUV"
    g.link(nor.outputs["Color"], nmap.inputs["Color"])
    bsdf = g.node("ShaderNodeBsdfPrincipled", (-400, 200))
    g.link(diff.outputs["Color"], bsdf.inputs["Base Color"])
    g.link(sep.outputs["Green"], bsdf.inputs["Roughness"])
    g.link(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    disp = g.node("ShaderNodeDisplacement", (-700, -600), F_DISP,
                  Midlevel=-shift_m / relief_m, Scale=relief_m)
    g.link(hgt.outputs["Color"], disp.inputs["Height"])
    out = g.node("ShaderNodeOutputMaterial", (0, 0))
    g.link(bsdf.outputs["BSDF"], out.inputs["Surface"])
    g.link(disp.outputs["Displacement"], out.inputs["Displacement"])
    mat.displacement_method = "BOTH"  # true displacement + bump for sub-dice detail
    return mat
