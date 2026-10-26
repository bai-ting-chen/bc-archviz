"""Weathered concrete: dirty edges in shading only (from the chip modifier's `edge_dist` field), and a
fresh-break material where the modifier cut a chip (`chip` > 0). No extra geometry.
"""
from materials.concrete import concrete as _mat_concrete
from materials.shared.nodes import G
from materials.shared.nodes import sock
from effects.wear_nodes import attr, math_, noise, range_


def weathered_concrete(name="CONCRETE_WEATHERED", dirt_band=0.035, dirt_amount=0.85,
                       dirt_noise_scale=9.0, stain=True, tex_id="concrete_wall_009"):
    """concrete_study base (tone, maps, round edges, leak stain) + procedural dirty edges from
    the GN `edge_dist` field + a fresh-break material where GN cut a chip (`chip` > 0)."""
    mat = _mat_concrete.concrete_study(name=name, tex_id=tex_id, edge_dark=False, stain=stain, bevel_chips=False)
    g = G(mat.node_tree)                      # add to the existing tree
    nt = mat.node_tree
    mix = next(n for n in nt.nodes if n.label == "Wear Layered (BRDFLayered)")
    stain_node = next((n for n in nt.nodes if n.label == "stain (vertical faces)"), None)
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    clean = next(n for n in nt.nodes if n.label == "Concrete")

    g.frame("Edge field (from Geometry Nodes)", (0.22, 0.22, 0.32))
    g.frame("Dirty edges (shading only)", (0.32, 0.24, 0.16))
    g.frame("Chips (geometry cut by GN; shaded here)", (0.32, 0.18, 0.18))
    F_FLD, F_DIRT, F_CHIP = list(g.frames)
    x0, y0 = -1600, -2300
    d = attr(g, "edge_dist", (x0, y0), F_FLD)
    rest = attr(g, "rest_pos", (x0, y0 - 180), F_FLD, out="Vector")
    chip_m = attr(g, "chip", (x0, y0 - 360), F_FLD)
    chip = range_(g, chip_m, 0.0, 0.0008, (x0 + 250, y0 - 600), F_CHIP, label="chip mask (break edge)")

    band = range_(g, d, 0.0, dirt_band, (x0 + 250, y0 + 300), F_DIRT, 1.0, 0.0,
                  label="edge band", smooth=True)
    blot = range_(g, noise(g, rest, dirt_noise_scale, (x0 + 250, y0 + 80), F_DIRT, detail=10,
                           rough=0.65, label="grime breakup"),
                  0.36, 0.60, (x0 + 450, y0 + 80), F_DIRT)
    dirt = math_(g, "MULTIPLY", band, blot, (x0 + 650, y0 + 200), F_DIRT)
    dirt = math_(g, "MULTIPLY", dirt, dirt_amount, (x0 + 820, y0 + 200), F_DIRT)
    no_chip = math_(g, "SUBTRACT", 1.0, chip, (x0 + 820, y0 + 20), F_DIRT, clamp=True)
    dirt = math_(g, "MULTIPLY", dirt, no_chip, (x0 + 1000, y0 + 150), F_DIRT)  # fresh breaks are clean
    dirt.node.label = "dirty edge mask"
    mask = dirt
    if stain_node is not None:
        mask = math_(g, "MAXIMUM", mask, stain_node.outputs[0], (x0 + 1200, y0 + 150), F_DIRT)
    for l in list(mix.inputs["Fac"].links):
        nt.links.remove(l)
    g.link(mask, mix.inputs["Fac"])
    worn = next(n for n in nt.nodes if n.label == "Worn BRDF")
    worn.label = "Grime BRDF"
    worn.inputs["Base Color"].default_value = (0.105, 0.098, 0.088, 1)

    brk = g.node("ShaderNodeBsdfPrincipled", (x0 + 900, y0 - 500), F_CHIP,
                 label="Fresh break (lighter, rough)", Roughness=0.95)
    tint = g.node("ShaderNodeMix", (x0 + 650, y0 - 450), F_CHIP, label="break: lighter paste")
    tint.data_type, tint.blend_type = "RGBA", "MULTIPLY"
    tint.inputs["Factor"].default_value = 1.0
    sock(tint.inputs, "B").default_value = (1.16, 1.15, 1.13, 1)  # lighter paste, not chalk
    g.link(clean.inputs["Base Color"].links[0].from_socket, sock(tint.inputs, "A"))
    g.link(sock(tint.outputs, "Result"), brk.inputs["Base Color"])
    bump = g.node("ShaderNodeBump", (x0 + 650, y0 - 750), F_CHIP, label="fracture bump",
                  Distance=0.003)
    g.link(noise(g, rest, 400.0, (x0 + 450, y0 - 750), F_CHIP, detail=6), bump.inputs["Height"])
    g.link(bump.outputs["Normal"], brk.inputs["Normal"])
    mix2 = g.node("ShaderNodeMixShader", (x0 + 1200, y0 - 300), F_CHIP, label="chips over surface")
    g.link(chip, mix2.inputs["Fac"])
    g.link(mix.outputs["Shader"], mix2.inputs[1])
    g.link(brk.outputs["BSDF"], mix2.inputs[2])
    g.link(mix2.outputs["Shader"], out.inputs["Surface"])
    mat.displacement_method = "BUMP"
    mat["recipe"] = "procedural dirty edges (shading) + GN-cut chips (geometry)"
    return mat
