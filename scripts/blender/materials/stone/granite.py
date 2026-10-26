"""Granite; canonical implementation behind stone."""

import bpy

from materials.shared.nodes import G, sock

from materials.stone.stone_ramp import _ramp

def polished_granite(name="GRANITE_POLISHED", grain_m=0.006, roughness=0.04, ior=1.55,
                     base=((0.010, 0.008, 0.007), (0.026, 0.019, 0.015)),
                     flecks=((0.62, (0.055, 0.037, 0.026)), (0.80, (0.13, 0.12, 0.11)),
                             (0.91, (0.34, 0.28, 0.21)))):
    """Procedural speckled granite in 3-D world space (a solid texture: cut faces and edges agree).
    Crystals = Voronoi cells of ~grain_m, each coloured by its random value through a constant
    ramp (black mica / brown feldspar / grey quartz / cream feldspar); a coarse noise drifts the
    base. Polished = one smooth dielectric (no coat). No Bevel node: the pool lining is a caustic
    receiver -- round edges come from a geometric Bevel modifier instead."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = G(mat)
    g.frame("Crystals (Voronoi, world space)", (0.22, 0.20, 0.18))
    g.frame("Polish", (0.20, 0.24, 0.30))
    F_C, F_P = list(g.frames)
    pos = g.node("ShaderNodeNewGeometry", (-1500, 0), F_C).outputs["Position"]
    warp = g.node("ShaderNodeTexNoise", (-1300, -250), F_C, label="crystal shape warp",
                  Scale=1.0 / (grain_m * 2.5), Detail=2.0)
    g.link(pos, warp.inputs["Vector"])
    vadd = g.node("ShaderNodeVectorMath", (-1100, 0), F_C, label="warped position")
    vadd.operation = "MULTIPLY_ADD"
    vadd.inputs[1].default_value = (grain_m * 0.6,) * 3
    g.link(warp.outputs["Color"], vadd.inputs[0])
    g.link(pos, vadd.inputs[2])
    vor = g.node("ShaderNodeTexVoronoi", (-900, 100), F_C, label="crystals %.0f mm" % (grain_m * 1000),
                 Scale=1.0 / grain_m, Randomness=1.0)
    g.link(vadd.outputs["Vector"], vor.inputs["Vector"])
    stops = [(0.0, base[0])] + list(flecks)
    cr = _ramp(g, (-650, 150), F_C, stops, "mineral palette", interp="CONSTANT")
    sepv = g.node("ShaderNodeSeparateColor", (-780, 150), F_C)
    g.link(vor.outputs["Color"], sepv.inputs["Color"])
    g.link(sepv.outputs["Red"], cr.inputs["Fac"])
    drift = g.node("ShaderNodeTexNoise", (-900, -250), F_C, label="base drift", Scale=3.0, Detail=6.0)
    g.link(vadd.outputs["Vector"], drift.inputs["Vector"])
    dr = _ramp(g, (-650, -200), F_C, [(0.35, base[0]), (0.65, base[1])], "dark matrix")
    g.link(drift.outputs["Fac"], dr.inputs["Fac"])
    is_matrix = g.node("ShaderNodeMath", (-450, -50), F_C, label="cell is matrix")
    is_matrix.operation = "LESS_THAN"
    is_matrix.inputs[1].default_value = flecks[0][0]
    g.link(sepv.outputs["Red"], is_matrix.inputs[0])
    col = g.node("ShaderNodeMix", (-250, 100), F_C, label="matrix vs crystal")
    col.data_type = "RGBA"
    g.link(is_matrix.outputs[0], col.inputs["Factor"])
    g.link(cr.outputs["Color"], sock(col.inputs, "A"))
    g.link(dr.outputs["Color"], sock(col.inputs, "B"))
    rnoise = g.node("ShaderNodeTexNoise", (-650, -500), F_P, label="polish variation", Scale=1.5, Detail=3)
    g.link(vadd.outputs["Vector"], rnoise.inputs["Vector"])
    rr = g.node("ShaderNodeMapRange", (-400, -450), F_P, label="roughness %.2f +-0.02" % roughness)
    rr.inputs["To Min"].default_value = max(0.0, roughness - 0.02)
    rr.inputs["To Max"].default_value = roughness + 0.02
    g.link(rnoise.outputs["Fac"], rr.inputs["Value"])
    b = g.node("ShaderNodeBsdfPrincipled", (0, 0), F_P, label="polished granite", IOR=ior)
    g.link(sock(col.outputs, "Result"), b.inputs["Base Color"])
    g.link(rr.outputs["Result"], b.inputs["Roughness"])
    out = g.node("ShaderNodeOutputMaterial", (300, 0))
    g.link(b.outputs["BSDF"], out.inputs["Surface"])
    return mat
