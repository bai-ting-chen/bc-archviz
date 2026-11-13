"""Concrete edge shading and fresh-break material from clean distance and chip fields."""
from materials.concrete import concrete as _mat_concrete
from materials.shared.node_graph import NodeGraph
from effects.wear.dirt import (DUST_AMOUNT, DUST_WIDTH, GRIME_TINT, LINE_AMOUNT, LINE_WIDTH,
                               dust_surface, edge_dirt_masks)


def weathered_concrete(name="CONCRETE_WEATHERED", line_width=LINE_WIDTH, line_amount=LINE_AMOUNT,
                       dirt_noise_scale=9.0, tex_id="concrete_wall_009",
                       dust_width=DUST_WIDTH, dust_amount=DUST_AMOUNT, chips_amount=1.0, rounded_edges=True):
    """Layer edge line/dust and fresh-break shading over the concrete study material."""
    mat = _mat_concrete.concrete_study(name=name, tex_id=tex_id, edge_dark=False, bevel_chips=False, rounded_edges=rounded_edges)
    g = NodeGraph(mat.node_tree)                      # add to the existing tree
    nt = mat.node_tree
    mix = next(n for n in nt.nodes if n.label == "Wear Layered (BRDFLayered)")
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    clean = next(n for n in nt.nodes if n.label == "Concrete")

    g.frame("Edge field (from Geometry Nodes)", (0.22, 0.22, 0.32))
    g.frame("Dirty edges (shading only)", (0.32, 0.24, 0.16))
    g.frame("Chips (geometry cut by GN; shaded here)", (0.32, 0.18, 0.18))
    F_FLD, F_DIRT, F_CHIP = list(g.frames)
    x0, y0 = -1600, -2300
    d = g.attribute("edge_dist", (x0, y0), F_FLD)
    rest = g.attribute("rest_pos", (x0, y0 - 180), F_FLD, out="Vector")
    chip_m = g.attribute("chip", (x0, y0 - 360), F_FLD)
    chip = g.map_range(chip_m, 0.0, 0.0008, (x0 + 250, y0 - 600), frame=F_CHIP, label="chip mask (break edge)")

    chip = g.math('MULTIPLY', chip, chips_amount, (x0 + 500, y0 - 600), F_CHIP)
    chip.node.label = 'Chips strength'

    dirt, dust, vertex_join = edge_dirt_masks(g, d, line_width, dust_width, rest,
                                 line_amount, dust_amount, dirt_noise_scale,
                                 F_DIRT, (x0 + 250, y0 + 300))
    no_chip = g.math("SUBTRACT", 1.0, chip, (x0 + 820, y0 + 20), F_DIRT, clamp=True)
    vertex_line = g.math('MULTIPLY', dirt, vertex_join, (x0 + 1000, y0 - 900), F_DIRT)
    # Genuine chips remain clean away from junctions; a local line bridges both shader branches.
    line_allowed = g.math('MAXIMUM', no_chip, vertex_join, (x0 + 820, y0 + 150), F_DIRT)
    dirt = g.math("MULTIPLY", dirt, line_allowed, (x0 + 1000, y0 + 150), F_DIRT)
    dust = g.math("MULTIPLY", dust, no_chip, (x0 + 1000, y0 - 50), F_DIRT)
    dust.node.label = "dust edge mask"
    dirt.node.label = "dirty edge mask"
    # Run-off and crack halos keep their existing grime path; edge line colour is now relative.
    for l in list(mix.inputs["Fac"].links):
        nt.links.remove(l)
    g.link_or_set(mix.inputs["Fac"], 0.0)
    worn = next(n for n in nt.nodes if n.label == "Worn BRDF")
    worn.label = "Grime BRDF"
    worn.inputs["Base Color"].default_value = (*GRIME_TINT, 1)

    brk, mix2 = _fresh_break(g, clean, rest, F_CHIP, x0, y0)
    g.link(chip, mix2.inputs["Fac"])
    dusty = dust_surface(g, mix.outputs["Shader"], dust, F_DIRT,
                          (x0 + 1500, y0 + 200), line=dirt)
    g.link(dusty, mix2.inputs[1])
    joined_break = dust_surface(g, brk.outputs['BSDF'], 0.0, F_DIRT,
                                (x0 + 1500, y0 - 1000), line=vertex_line)
    g.link(joined_break, mix2.inputs[2])
    g.link(mix2.outputs["Shader"], out.inputs["Surface"])
    mat.displacement_method = "BUMP"
    mat["recipe"] = "procedural dirty edges (shading) + GN-cut chips (geometry)"
    return mat


def _fresh_break(g, clean, rest, F_CHIP, x0, y0):
    """Build the lighter fracture shader and its final chip blend."""
    brk = g.node("ShaderNodeBsdfPrincipled", (x0 + 900, y0 - 500), F_CHIP,
                 label="Fresh break (lighter, rough)", Roughness=0.95)
    tint = g.mix(clean.inputs["Base Color"].links[0].from_socket, (1.16, 1.15, 1.13, 1), 1.0,
                 (x0 + 650, y0 - 450), F_CHIP, blend="MULTIPLY", label="break: lighter paste")
    g.link(tint, brk.inputs["Base Color"])  # lighter paste, not chalk
    bump = g.node("ShaderNodeBump", (x0 + 650, y0 - 750), F_CHIP, label="fracture bump",
                  Distance=0.003)
    g.link(g.noise_texture(rest, 400.0, (x0 + 450, y0 - 750), F_CHIP, detail=6), bump.inputs["Height"])
    g.link(bump.outputs["Normal"], brk.inputs["Normal"])
    mix2 = g.node("ShaderNodeMixShader", (x0 + 1200, y0 - 300), F_CHIP, label="chips over surface")
    return brk, mix2
