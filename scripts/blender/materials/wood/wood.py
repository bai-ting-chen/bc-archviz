"""Wood material helpers; canonical implementations."""
import bpy
from materials.shared.nodes import G, sock
from materials.shared.pbr import _ph_maps, solve_levels


def coated_wood(name="COATED_PINE", tex_id="coated_pine", coat=0.2, coat_rough=0.04,
                rough_toward_matte=0.35, albedo_rgb=(0.52, 0.33, 0.17), levels_gamma=0.5,
                round_edge=0.002, normal_strength=1.0):
    """Coated pine: every map wired; levels solved to a natural pine albedo; satin
    varnish = LOW coat amount with TIGHT gloss (the coat trap); base roughness spread toward
    matte instead of cheating Fresnel; round edges combined with the normal map."""
    maps, meta = _ph_maps(tex_id)
    gain = solve_levels(maps["diff"], albedo_rgb, levels_gamma)
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = G(mat)
    g.frame("Maps (BoxUV)", (0.20, 0.24, 0.30))
    g.frame("Relief + round edges", (0.25, 0.22, 0.30))
    F_MAP, F_REL = list(g.frames)
    uv = g.uv("BoxUV", (-1300, 0), F_MAP)
    diff = g.img(maps["diff"], "sRGB", (-1050, 300), F_MAP, uv, "diffuse")
    arm = g.img(maps["arm"], "Non-Color", (-1050, 0), F_MAP, uv, "arm")
    nor = g.img(maps["nor_gl"], "Non-Color", (-1050, -300), F_MAP, uv, "normal (GL)")
    gam = g.node("ShaderNodeGamma", (-780, 400), F_MAP, label="levels: gamma", Gamma=levels_gamma)
    g.link(diff.outputs["Color"], gam.inputs["Color"])
    lv = g.node("ShaderNodeMix", (-600, 400), F_MAP, label="levels: gain (solved)")
    lv.data_type, lv.blend_type = "RGBA", "MULTIPLY"
    lv.inputs["Factor"].default_value = 1.0
    sock(lv.inputs, "B").default_value = (*gain, 1.0)
    g.link(gam.outputs["Color"], sock(lv.inputs, "A"))
    sep = g.node("ShaderNodeSeparateColor", (-750, 0), F_MAP)
    g.link(arm.outputs["Color"], sep.inputs["Color"])
    rmix = g.node("ShaderNodeMix", (-580, 0), F_MAP, label="roughness toward matte")
    rmix.data_type = "FLOAT"
    rmix.inputs["Factor"].default_value = rough_toward_matte
    sock(rmix.inputs, "B").default_value = 1.0
    g.link(sep.outputs["Green"], sock(rmix.inputs, "A"))
    nmap = g.node("ShaderNodeNormalMap", (-750, -300), F_REL, Strength=normal_strength)
    nmap.uv_map = "BoxUV"
    g.link(nor.outputs["Color"], nmap.inputs["Color"])
    relief = nmap.outputs["Normal"]
    if round_edge:  # Bevel node is invalid on MNEE caustic casters/receivers -- pass 0 there
        rnd = g.node("ShaderNodeBevel", (-550, -300), F_REL, label="Round edges", Radius=round_edge)
        g.link(nmap.outputs["Normal"], rnd.inputs["Normal"])
        relief = rnd.outputs["Normal"]
    bsdf = g.node("ShaderNodeBsdfPrincipled", (-250, 200), label="Pine + satin varnish coat")
    g.link(sock(lv.outputs, "Result"), bsdf.inputs["Base Color"])
    g.link(sock(rmix.outputs, "Result"), bsdf.inputs["Roughness"])
    g.link(relief, bsdf.inputs["Normal"])
    bsdf.inputs["Coat Weight"].default_value = coat
    bsdf.inputs["Coat Roughness"].default_value = coat_rough
    bsdf.inputs["Coat IOR"].default_value = 1.5
    out = g.node("ShaderNodeOutputMaterial", (100, 200))
    g.link(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat
