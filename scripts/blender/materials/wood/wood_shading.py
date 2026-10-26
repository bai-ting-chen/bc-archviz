"""Wood shading; canonical implementation behind wood_wear."""

from materials.shared import nodes as _mat_nodes

from materials.wood import wood as _mat_wood

from materials.shared.nodes import sock

from effects.wear_nodes import attr as _attr

from effects.wear_nodes import noise as _noise

from effects.wear_nodes import range_ as _range

from effects.wear_nodes import math_ as _math

def weathered_wood(name="PINE_WEATHERED", wear_band=0.012, wear_amount=0.9,
                   inner_tint=(0.80, 0.60, 0.36), inner_mix=0.30, inner_gain=1.7):
    """coated_wood base (levels, satin coat trap) + worn varnish/grime at arrises + inner wood."""
    mat = _mat_wood.coated_wood(name=name, round_edge=0)
    g = _mat_nodes.G(mat.node_tree)                   # add to the existing tree
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
    d = _attr(g, "edge_dist", (x0, y0), F_FLD)
    rest = _attr(g, "rest_pos", (x0, y0 - 180), F_FLD, out="Vector")
    chip = _range(g, _attr(g, "chip", (x0, y0 - 360), F_FLD), 0.0, 0.0003, (x0 + 250, y0 - 360),
                  F_FLD, label="chip mask")
    brk = _range(g, _attr(g, "break", (x0, y0 - 540), F_FLD), 0.0, 0.00015, (x0 + 250, y0 - 540),
                 F_FLD, label="break mask")
    exposed = _math(g, "MAXIMUM", chip, brk, (x0 + 450, y0 - 450), F_FLD)
    exposed.node.label = "exposed inner wood"

    band = _range(g, d, 0.0, wear_band, (x0 + 250, y0 + 250), F_WEAR, 1.0, 0.0,
                  label="edge band", smooth=True)
    blot = _range(g, _noise(g, rest, 28.0, (x0 + 250, y0 + 50), F_WEAR, detail=10, rough=0.65,
                            label="wear breakup"), 0.38, 0.62, (x0 + 450, y0 + 50), F_WEAR)
    wear_m = _math(g, "MULTIPLY", _math(g, "MULTIPLY", band, blot, (x0 + 650, y0 + 150), F_WEAR),
                   wear_amount, (x0 + 800, y0 + 150), F_WEAR)
    wear_m = _math(g, "MULTIPLY", wear_m, _math(g, "SUBTRACT", 1.0, exposed, (x0 + 800, y0 - 20),
                                                F_WEAR, clamp=True), (x0 + 950, y0 + 100), F_WEAR)
    wear_m.node.label = "worn edge mask"
    grime = g.node("ShaderNodeMix", (x0 + 950, y0 + 350), F_WEAR, label="hand grime (darker)")
    grime.data_type, grime.blend_type = "RGBA", "MULTIPLY"
    grime.inputs["Factor"].default_value = 1.0
    sock(grime.inputs, "B").default_value = (0.55, 0.50, 0.44, 1)
    g.link(col_src, sock(grime.inputs, "A"))
    worn = g.node("ShaderNodeBsdfPrincipled", (x0 + 1150, y0 + 300), F_WEAR,
                  label="Worn edge: no varnish, grimy", Roughness=0.62)
    g.link(sock(grime.outputs, "Result"), worn.inputs["Base Color"])
    g.link(nrm_src, worn.inputs["Normal"])

    # Raw pine under the varnish: same grain, much lighter, slightly yellower -- not a flat tint
    lift = g.node("ShaderNodeMix", (x0 + 450, y0 - 800), F_IN, label="inner wood: lighter (no amber varnish)")
    lift.data_type, lift.blend_type = "RGBA", "MULTIPLY"
    lift.inputs["Factor"].default_value = 1.0
    sock(lift.inputs, "B").default_value = (inner_gain, inner_gain * 1.02, inner_gain * 1.08, 1)
    g.link(col_src, sock(lift.inputs, "A"))
    pale = g.node("ShaderNodeMix", (x0 + 650, y0 - 800), F_IN, label="inner wood: toward raw pine")
    pale.data_type = "RGBA"
    pale.inputs["Factor"].default_value = inner_mix
    sock(pale.inputs, "B").default_value = (*inner_tint, 1)
    g.link(sock(lift.outputs, "Result"), sock(pale.inputs, "A"))
    fib = g.node("ShaderNodeMapping", (x0 + 250, y0 - 1000), F_IN, label="fibres along grain (UV U)")
    fib.inputs["Scale"].default_value = (20.0, 900.0, 1.0)
    uvn = g.uv("BoxUV", (x0 + 50, y0 - 1000), F_IN)
    g.link(uvn, fib.inputs["Vector"])
    fbump = g.node("ShaderNodeBump", (x0 + 650, y0 - 1050), F_IN, label="torn fibres", Distance=0.0012)
    g.link(_noise(g, fib.outputs["Vector"], 1.0, (x0 + 450, y0 - 1050), F_IN, detail=4),
           fbump.inputs["Height"])
    g.link(nrm_src, fbump.inputs["Normal"])
    inner = g.node("ShaderNodeBsdfPrincipled", (x0 + 900, y0 - 850), F_IN,
                   label="Inner wood (raw)", Roughness=0.85)
    g.link(sock(pale.outputs, "Result"), inner.inputs["Base Color"])
    g.link(fbump.outputs["Normal"], inner.inputs["Normal"])

    m1 = g.node("ShaderNodeMixShader", (300, 100), label="worn edges over varnish")
    g.link(wear_m, m1.inputs["Fac"])
    g.link(coated.outputs["BSDF"], m1.inputs[1])
    g.link(worn.outputs["BSDF"], m1.inputs[2])
    m2 = g.node("ShaderNodeMixShader", (500, 0), label="inner wood where broken")
    g.link(exposed, m2.inputs["Fac"])
    g.link(m1.outputs["Shader"], m2.inputs[1])
    g.link(inner.outputs["BSDF"], m2.inputs[2])
    out.location = (700, 0)
    g.link(m2.outputs["Shader"], out.inputs["Surface"])
    mat["recipe"] = "weathered varnished pine: worn edges (shading) + GN dents/breaks (geometry)"
    return mat
