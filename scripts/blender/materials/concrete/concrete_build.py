"""Concrete build; canonical implementation behind concrete."""

import bpy
from effects.round_edges import round_shader

from materials.shared.nodes import G, sock

from materials.shared.pbr_maps import _ph_maps
from materials.shared.principled import _principled
from materials.shared.map_measure import map_mean

from materials.concrete.concrete_masks import _bevel_chips, _edge_mask

def concrete_study(name="CONCRETE", tex_id="concrete_wall_009",
                   color_mult=(0.76, 0.82, 0.99), normal_strength=0.6, bump_distance=0.004,
                   rounded_edges=True, chip_spread=0.05, chip_in=(0.40, 0.90),
                   noise_scale=14.0, noise_band=(0.35, 0.60),
                   edge_dark=True, bevel_chips=True):
    """Cast concrete: tone-matched diffuse, wired roughness/normal/height, round edges
    combined with the normal map, and chipped-edge wear driving a worn BRDF."""
    maps, meta = _ph_maps(tex_id)
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = G(mat)
    g.frame("Maps (BoxUV, real-world size)", (0.20, 0.24, 0.30))
    g.frame("Surface relief: normal + height bump + round edges", (0.25, 0.22, 0.30))
    g.frame("Wear mask: chips x noise, edge line", (0.30, 0.22, 0.20))
    g.frame("BRDFs", (0.20, 0.28, 0.22))
    F_MAP, F_REL, F_WEAR, F_BRDF = list(g.frames)

    uv = g.uv("BoxUV", (-1700, 200), F_MAP)
    diff = g.img(maps["diff"], "sRGB", (-1450, 450), F_MAP, uv, "diffuse")
    arm = g.img(maps["arm"], "Non-Color", (-1450, 150), F_MAP, uv, "arm (AO/rough/metal)")
    nor = g.img(maps["nor_gl"], "Non-Color", (-1450, -150), F_MAP, uv, "normal (GL)")
    hgt = g.img(maps["disp"], "Non-Color", (-1450, -450), F_MAP, uv, "height")

    tone = g.node("ShaderNodeMix", (-1100, 450), F_MAP, label="color_mult (tone match)")
    tone.data_type, tone.blend_type = "RGBA", "MULTIPLY"
    tone.inputs["Factor"].default_value = 1.0
    sock(tone.inputs, "B").default_value = (*color_mult, 1.0)
    g.link(diff.outputs["Color"], sock(tone.inputs, "A"))
    sep = g.node("ShaderNodeSeparateColor", (-1100, 150), F_MAP)
    g.link(arm.outputs["Color"], sep.inputs["Color"])
    rough = g.node("ShaderNodeMix", (-900, 150), F_MAP, label="rough: map 0.45 over 0.72")
    rough.data_type = "FLOAT"
    rough.inputs["Factor"].default_value = 0.45
    sock(rough.inputs, "A").default_value = 0.72
    g.link(sep.outputs["Green"], sock(rough.inputs, "B"))

    nmap = g.node("ShaderNodeNormalMap", (-1050, -150), F_REL, Strength=normal_strength)
    nmap.uv_map = "BoxUV"
    g.link(nor.outputs["Color"], nmap.inputs["Color"])
    bump = g.node("ShaderNodeBump", (-850, -250), F_REL, label="height as bump",
                  Distance=bump_distance)
    g.link(hgt.outputs["Color"], bump.inputs["Height"])
    g.link(nmap.outputs["Normal"], bump.inputs["Normal"])
    relief = round_shader(g, bump.outputs['Normal'], rounded_edges=rounded_edges,
                         loc=(-650, -250), frame=F_REL)

    # Wear mask = max( chips * noise , edge line ); leak streaks come from effects.runoff
    mask = None
    if bevel_chips:
        mask = _bevel_chips(g, chip_spread, chip_in, noise_scale, noise_band, F_WEAR)

    def _union(a, b, loc):
        if a is None:
            return b
        mx = g.node("ShaderNodeMath", loc, F_WEAR, label="Lighten")
        mx.operation = "MAXIMUM"
        g.link(a, mx.inputs[0])
        g.link(b, mx.inputs[1])
        return mx.outputs["Value"]

    if edge_dark:  # thin dark edge line: spread 3 mm, remap 0.55..0.95 -> 0..0.55
        line = _edge_mask(g, 0.003, (-700, -1200), F_WEAR, "Edge Dark curvature")
        line_r = g.node("ShaderNodeMapRange", (-480, -1200), F_WEAR, label="Edge Dark Remap")
        line_r.inputs["From Min"].default_value, line_r.inputs["From Max"].default_value = 0.55, 0.95
        line_r.inputs["To Max"].default_value = 0.55
        g.link(line, line_r.inputs["Value"])
        mask = _union(mask, line_r.outputs["Result"], (-120, -950))

    clean = g.node("ShaderNodeBsdfPrincipled", (-250, 350), F_BRDF, label="Concrete",
                   IOR=1.5)
    clean.inputs["Coat Weight"].default_value = 0.03
    g.link(sock(tone.outputs, "Result"), clean.inputs["Base Color"])
    g.link(sock(rough.outputs, "Result"), clean.inputs["Roughness"])
    g.link(relief, clean.inputs["Normal"])
    worn = g.node("ShaderNodeBsdfPrincipled", (-250, -50), F_BRDF, label="Worn BRDF",
                  Roughness=0.93)
    worn.inputs["Base Color"].default_value = (0.160, 0.155, 0.145, 1)
    worn.inputs["Coat Weight"].default_value = 0.03
    g.link(relief, worn.inputs["Normal"])
    mix = g.node("ShaderNodeMixShader", (150, 200), F_BRDF, label="Wear Layered (BRDFLayered)")
    if mask is not None:
        g.link(mask, mix.inputs["Fac"])
    else:
        mix.inputs["Fac"].default_value = 0.0
    g.link(clean.outputs["BSDF"], mix.inputs[1])
    g.link(worn.outputs["BSDF"], mix.inputs[2])
    out = g.node("ShaderNodeOutputMaterial", (400, 200))
    g.link(mix.outputs["Shader"], out.inputs["Surface"])
    mat["recipe"] = "concrete_study"
    return mat
