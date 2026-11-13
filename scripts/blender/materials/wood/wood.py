"""Wood: base and coat (coated_wood), raw-wood under-layer, chip preset and weathered assembly."""
import bpy
from effects.wear.chipping import GrainBreaks
from effects.wear.wear_locations import round_shader
from materials.shared.node_graph import NodeGraph
from materials.shared.pbr import _ph_maps, solve_levels
from materials.shared.pbr_maps import box_maps

# Wood-sized settings for effects.wear.edge_wear_group: small dents, grain-wise breaks on top.
WOOD_CHIPS = dict(name="Wood Wear + Breaks", band=0.02, chip_reach=0.006, chip_depth=0.0025,
                  chipped_share=0.30, segment_scale=6.0, bite_scale=70.0, chip_soft=0.0006,
                  profile_end=0.4, fracture=0.0, breaks=GrainBreaks())


def coated_wood(name="COATED_PINE", tex_id="coated_pine", coat=0.2, coat_rough=0.04,
                rough_toward_matte=0.35, albedo_rgb=(0.52, 0.33, 0.17), levels_gamma=0.5,
                rounded_edges=True, normal_strength=1.0):
    """Coated pine: every map wired; levels solved to a natural pine albedo; satin
    varnish = LOW coat amount with TIGHT gloss (the coat trap); base roughness spread toward
    matte instead of cheating Fresnel; round edges combined with the normal map."""
    maps, meta = _ph_maps(tex_id)
    gain = solve_levels(maps["diff"], albedo_rgb, levels_gamma)
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = NodeGraph(mat)
    g.frame("Maps (BoxUV)", (0.20, 0.24, 0.30))
    g.frame("Relief + round edges", (0.25, 0.22, 0.30))
    F_MAP, F_REL = list(g.frames)
    m = box_maps(g, maps, F_MAP, (-1300, 0), normal_frame=F_REL, normal_strength=normal_strength)
    diff, sep, nmap = m["diff"], m["sep"], m["nmap"]
    gam = g.node("ShaderNodeGamma", (-780, 400), F_MAP, label="levels: gamma", Gamma=levels_gamma)
    g.link(diff.outputs["Color"], gam.inputs["Color"])
    lv = g.mix(gam.outputs["Color"], (*gain, 1.0), 1.0, (-600, 400), F_MAP, blend="MULTIPLY",
               label="levels: gain (solved)")
    rmix = g.mix(sep.outputs["Green"], 1.0, rough_toward_matte, (-580, 0), F_MAP, data_type="FLOAT",
                 label="roughness toward matte")
    relief = round_shader(g, nmap.outputs['Normal'], rounded_edges=rounded_edges,
                         location=(-550, -300), frame=F_REL, label='Round edges', samples=4)
    bsdf = g.node("ShaderNodeBsdfPrincipled", (-250, 200), label="Pine + satin varnish coat")
    g.link(lv, bsdf.inputs["Base Color"])
    g.link(rmix, bsdf.inputs["Roughness"])
    g.link(relief, bsdf.inputs["Normal"])
    bsdf.inputs["Coat Weight"].default_value = coat
    bsdf.inputs["Coat Roughness"].default_value = coat_rough
    bsdf.inputs["Coat IOR"].default_value = 1.5
    out = g.node("ShaderNodeOutputMaterial", (100, 200))
    g.link(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def raw_wood_under(graph, color, normal, frame=None, location=(-1050, -1500), tint=(0.80, 0.60, 0.36),
                   mix=0.30, gain=1.7):
    """Under-layer for solid wood: the base grain lighter and toward a raw tint, rough, with torn
    fibres along the grain (UV U). Returns the BSDF output socket."""
    x0, y0 = location
    lift = graph.mix(color, (gain, gain * 1.02, gain * 1.08, 1), 1.0, (x0, y0), frame, blend="MULTIPLY",
                 label="inner wood: lighter (no amber varnish)")
    pale = graph.mix(lift, (*tint, 1), mix, (x0 + 200, y0), frame, label="inner wood: toward raw pine")
    fib = graph.node("ShaderNodeMapping", (x0 - 200, y0 - 200), frame, label="fibres along grain (UV U)")
    fib.inputs["Scale"].default_value = (20.0, 900.0, 1.0)
    graph.link(graph.uv_map("BoxUV", (x0 - 400, y0 - 200), frame), fib.inputs["Vector"])
    fbump = graph.node("ShaderNodeBump", (x0 + 200, y0 - 250), frame, label="torn fibres", Distance=0.0012)
    graph.link(graph.noise_texture(fib.outputs["Vector"], 1.0, (x0, y0 - 250), frame, detail=4), fbump.inputs["Height"])
    graph.link(normal, fbump.inputs["Normal"])
    inner = graph.node("ShaderNodeBsdfPrincipled", (x0 + 450, y0 - 50), frame,
                   label="Inner wood (raw)", Roughness=0.85)
    graph.link(pale, inner.inputs["Base Color"])
    graph.link(fbump.outputs["Normal"], inner.inputs["Normal"])
    return inner.outputs["BSDF"]


def weathered_wood(name="PINE_WEATHERED", wear_band=0.012, wear_amount=0.9, **under):
    """coated_wood + worn varnish and grime along the arrises + raw_wood_under where the
    edge_wear_group(**WOOD_CHIPS) chips and breaks cut the skin. under: raw_wood_under settings."""
    mat = coated_wood(name=name, rounded_edges=False)
    g = NodeGraph(mat.node_tree)                   # add to the existing tree
    nt = mat.node_tree
    coated = next(n for n in nt.nodes if n.label == "Pine + satin varnish coat")
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    col_src = coated.inputs["Base Color"].links[0].from_socket
    nrm_src = coated.inputs["Normal"].links[0].from_socket

    g.frame("Edge field + damage attributes (from GN)", (0.22, 0.22, 0.32))
    g.frame("Worn edges: varnish gone + hand grime (shading)", (0.32, 0.24, 0.16))
    g.frame("Inner wood where the skin broke (geometry from GN)", (0.30, 0.26, 0.16))
    F_FLD, F_WEAR, F_IN = list(g.frames)
    x0, y0 = -1500, -700
    d = g.attribute("edge_dist", (x0, y0), F_FLD)
    rest = g.attribute("rest_pos", (x0, y0 - 180), F_FLD, output_name="Vector")
    chip = g.map_range(g.attribute("chip", (x0, y0 - 360), F_FLD), 0.0, 0.0003, (x0 + 250, y0 - 360),
                   frame=F_FLD, label="chip mask")
    brk = g.map_range(g.attribute("break", (x0, y0 - 540), F_FLD), 0.0, 0.00015, (x0 + 250, y0 - 540),
                  frame=F_FLD, label="break mask")
    exposed = g.math("MAXIMUM", chip, brk, (x0 + 450, y0 - 450), F_FLD)
    exposed.node.label = "exposed inner wood"

    band = g.map_range(d, 0.0, wear_band, (x0 + 250, y0 + 250), 1.0, 0.0, frame=F_WEAR,
                   label="edge band", smooth=True)
    blot = g.map_range(g.noise_texture(rest, 28.0, (x0 + 250, y0 + 50), F_WEAR, detail=10, roughness=0.65,
                           label="wear breakup"), 0.38, 0.62, (x0 + 450, y0 + 50), frame=F_WEAR)
    wear_m = g.math("MULTIPLY", g.math("MULTIPLY", band, blot, (x0 + 650, y0 + 150), F_WEAR),
                    wear_amount, (x0 + 800, y0 + 150), F_WEAR)
    wear_m = g.math("MULTIPLY", wear_m, g.math("SUBTRACT", 1.0, exposed, (x0 + 800, y0 - 20),
                                               F_WEAR, clamp=True), (x0 + 950, y0 + 100), F_WEAR)
    wear_m.node.label = "worn edge mask"
    grime = g.mix(col_src, (0.55, 0.50, 0.44, 1), 1.0, (x0 + 950, y0 + 350), F_WEAR, blend="MULTIPLY",
                  label="hand grime (darker)")
    worn = g.node("ShaderNodeBsdfPrincipled", (x0 + 1150, y0 + 300), F_WEAR,
                  label="Worn edge: no varnish, grimy", Roughness=0.62)
    g.link(grime, worn.inputs["Base Color"])
    g.link(nrm_src, worn.inputs["Normal"])
    inner = raw_wood_under(g, col_src, nrm_src, F_IN, (x0 + 450, y0 - 800), **under)

    m1 = g.node("ShaderNodeMixShader", (300, 100), label="worn edges over varnish")
    g.link(wear_m, m1.inputs["Fac"])
    g.link(coated.outputs["BSDF"], m1.inputs[1])
    g.link(worn.outputs["BSDF"], m1.inputs[2])
    m2 = g.node("ShaderNodeMixShader", (500, 0), label="inner wood where broken")
    g.link(exposed, m2.inputs["Fac"])
    g.link(m1.outputs["Shader"], m2.inputs[1])
    g.link(inner, m2.inputs[2])
    out.location = (700, 0)
    g.link(m2.outputs["Shader"], out.inputs["Surface"])
    mat["recipe"] = "weathered varnished pine: worn edges (shading) + GN dents/breaks (geometry)"
    return mat
