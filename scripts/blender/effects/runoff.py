"""Runoff: vertical streaks below drip edges, grunge patches and soil splash, all into the grime mask.

Needs the leak field (leak_field.add_leak_field) on the object. Works on a weathered_concrete material.
"""
from effects.wear_nodes import frame_for

LEAK = dict(streak_w=14.0, streak_len=0.6, max_len=(0.8, 3.2), top_band=0.2, top=0.9, amount=1.0,
            streak_band=(0.42, 0.58), presence=(0.28, 0.5), fade_pow=1.15)


def add_runoff(mat, leak=None, grunge=(0.6, 9.0, 0.56, 0.62, 0.45), splash=(0.08, 0.35, 0.7), ground_z=0.0):
    """On a weathered_concrete material: vertical runoff streaks below drip edges (needs add_leak_field), grunge patches, soil splash above ground_z (the wall foot); all into its grime mask."""
    L_ = dict(LEAK, **(leak or {}))
    g, F = frame_for(mat, "Runoff streaks, grunge, splash")
    nt = mat.node_tree
    geo = g.node("ShaderNodeNewGeometry", (-2600, -3400), F)
    sepn = g.node("ShaderNodeSeparateXYZ", (-2400, -3700), F); g.link(geo.outputs["Normal"], sepn.inputs[0])
    vert = g.range(g.math("ABSOLUTE", sepn.outputs["Z"], 0.0, (-2200, -3700), F), 0.25, 0.1, (-2000, -3700), frame=F)
    sepp = g.node("ShaderNodeSeparateXYZ", (-2400, -3950), F); g.link(geo.outputs["Position"], sepp.inputs[0])
    # metres along the wall: position . horizontal tangent (normal x Z) - any wall orientation
    tan = g.n("ShaderNodeVectorMath", (-2400, -4050), operation="CROSS_PRODUCT")
    g.link(geo.outputs["Normal"], tan.inputs[0]); tan.inputs[1].default_value = (0.0, 0.0, 1.0)
    tn = g.n("ShaderNodeVectorMath", (-2250, -4050), operation="NORMALIZE"); g.link(tan.outputs[0], tn.inputs[0])
    dot = g.n("ShaderNodeVectorMath", (-2100, -4050), operation="DOT_PRODUCT")
    g.link(geo.outputs["Position"], dot.inputs[0]); g.link(tn.outputs[0], dot.inputs[1])
    along = dot.outputs["Value"]
    sv = g.node("ShaderNodeCombineXYZ", (-2000, -4100), F)
    g.link(g.math("MULTIPLY", along, L_["streak_w"], (-2150, -4100), F), sv.inputs["X"])
    g.link(g.math("MULTIPLY", sepp.outputs["Z"], L_["streak_len"], (-2150, -4250), F), sv.inputs["Y"])
    streak = g.range(g.noise(sv.outputs[0], 1.0, (-1850, -4100), F, detail=4, rough=0.55), *L_["streak_band"],
                     (-1650, -4100), frame=F, smooth=True)
    lv = g.node("ShaderNodeCombineXYZ", (-2000, -4400), F)
    g.link(g.math("MULTIPLY", along, 2.5, (-2150, -4400), F), lv.inputs["X"])
    llen = g.range(g.noise(lv.outputs[0], 1.0, (-1850, -4400), F, detail=2), 0.35, 0.65, (-1650, -4400),
                   L_["max_len"][0], L_["max_len"][1], F)
    d = g.attr("leak_d", (-1850, -4650), F)
    ok = g.attr("leak_ok", (-1850, -4800), F)
    fade = g.math("SUBTRACT", 1.0, g.math("DIVIDE", d, llen, (-1450, -4500), F), (-1300, -4500), F, clamp=True)
    fade = g.math("POWER", fade, L_["fade_pow"], (-1150, -4500), F)
    top = g.range(d, 0.0, L_["top_band"], (-1450, -4700), L_["top"], 0.0, F, smooth=True)
    pv = g.node("ShaderNodeCombineXYZ", (-2000, -4950), F)
    g.link(g.math("MULTIPLY", along, 0.7, (-2150, -4950), F), pv.inputs["X"])
    presence = g.range(g.noise(pv.outputs[0], 1.0, (-1850, -4950), F, detail=3), *L_["presence"], (-1650, -4950), frame=F)
    leak = g.math("MAXIMUM", g.math("MULTIPLY", streak, fade, (-1000, -4300), F), top, (-850, -4400), F)
    leak = g.math("MULTIPLY", leak, presence, (-700, -4400), F)
    leak = g.math("MULTIPLY", leak, g.math("MULTIPLY", ok, vert, (-850, -4700), F), (-550, -4500), F)
    gate = g.range(d, -0.02, 0.0, (-1450, -4850), frame=F)
    leak = g.math("MULTIPLY", g.math("MULTIPLY", leak, gate, (-400, -4500), F), L_["amount"], (-250, -4500), F)
    leak.node.label = "leak streak mask"
    ps, hs, lo, hi, amt = grunge
    patch = g.math("ADD", g.noise(geo.outputs["Position"], ps, (-1850, -5200), F, detail=3),
                   g.math("MULTIPLY", g.math("SUBTRACT", g.noise(geo.outputs["Position"], hs, (-1850, -5400), F, detail=6), 0.5,
                                             (-1650, -5400), F), 0.35, (-1500, -5400), F), (-1350, -5250), F)
    grg = g.range(patch, lo, hi, (-1200, -5250), 0.0, amt, F)
    grg.node.label = "grunge patches"
    foot = g.math("ADD", g.math("SUBTRACT", sepp.outputs["Z"], ground_z, (-1500, -5750), F), g.math("MULTIPLY", g.math("SUBTRACT", g.noise(geo.outputs["Position"], 6.0, (-1850, -5650), F), 0.5,
                                                                      (-1650, -5650), F), 0.25, (-1500, -5650), F), (-1350, -5600), F)
    spl = g.math("MULTIPLY", g.range(foot, splash[0], splash[1], (-1200, -5600), splash[2], 0.0, F, smooth=True), vert, (-1050, -5600), F)
    spl.node.label = "soil splash"
    mix = next(n for n in nt.nodes if n.label == "Wear Layered (BRDFLayered)")
    old = mix.inputs["Fac"].links[0].from_socket
    m = g.math("MAXIMUM", g.math("MAXIMUM", g.math("MAXIMUM", old, leak, (-100, -4300), F), grg, (50, -4500), F), spl, (200, -4600), F)
    g.link(m, mix.inputs["Fac"])
    return mat
