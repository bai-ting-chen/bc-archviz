"""Stone material helpers; canonical implementations."""
import bpy
from .nodes import G, sock
from .pbr import _principled, albedo_material


def _ramp(g, loc, frame, stops, label=None, interp="LINEAR"):
    r = g.node("ShaderNodeValToRGB", loc, frame, label)
    cr = r.color_ramp
    cr.interpolation = interp
    while len(cr.elements) > 1:
        cr.elements.remove(cr.elements[-1])
    cr.elements[0].position, cr.elements[0].color = stops[0][0], (*stops[0][1], 1)
    for pos, col in stops[1:]:
        e = cr.elements.new(pos)
        e.color = (*col, 1)
    return r


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


def stone_tiles(name="LIMESTONE", tile=(1.2, 0.6), grout=0.002, albedo=(0.46, 0.41, 0.33),
                var=0.05, roughness=0.35, coat=0.0, coat_rough=0.08, uv="BoxUV"):
    """Large-format stone/porcelain on real-metre BoxUV: Brick Texture (offset 0) for the joints,
    per-tile tone from the brick colour pair, cloudy limestone mottling + fine specks, a soft coat
    for a honed-and-sealed floor. Grout darker and matte, joints slightly recessed (bump)."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = G(mat)
    g.frame("Tiles %.1f x %.1f m" % tile, (0.20, 0.24, 0.30))
    g.frame("Stone body", (0.26, 0.24, 0.20))
    g.frame("Finish", (0.22, 0.28, 0.22))
    F_T, F_S, F_F = list(g.frames)
    co = g.uv(uv, (-1500, 0), F_T)
    br = g.node("ShaderNodeTexBrick", (-1250, 0), F_T, Scale=1.0)
    br.offset, br.squash = 0.0, 1.0
    br.inputs["Brick Width"].default_value, br.inputs["Row Height"].default_value = tile
    br.inputs["Mortar Size"].default_value, br.inputs["Mortar Smooth"].default_value = grout, 0.2
    br.inputs["Bias"].default_value = 0.0
    br.inputs["Color1"].default_value = (1 - var, 1 - var, 1 - var, 1)
    br.inputs["Color2"].default_value = (1 + var, 1 + var, 1 + var, 1)
    br.inputs["Mortar"].default_value = (0.75, 0.75, 0.75, 1)
    g.link(co, br.inputs["Vector"])
    cloud = g.node("ShaderNodeTexNoise", (-1250, -350), F_S, label="cloudy body", Scale=2.5, Detail=8.0,
                   Roughness=0.6)
    g.link(co, cloud.inputs["Vector"])
    cr = _ramp(g, (-1000, -350), F_S, [(0.3, tuple(c * 0.90 for c in albedo)), (0.7, tuple(min(1, c * 1.08) for c in albedo))],
               "limestone tone")
    g.link(cloud.outputs["Fac"], cr.inputs["Fac"])
    speck = g.node("ShaderNodeTexVoronoi", (-1250, -650), F_S, label="fossil specks 3 mm", Scale=330.0)
    g.link(co, speck.inputs["Vector"])
    sp = g.node("ShaderNodeMapRange", (-1000, -650), F_S, label="speck mask")
    sp.inputs["From Min"].default_value, sp.inputs["From Max"].default_value = 0.0, 0.12
    sp.inputs["To Min"].default_value, sp.inputs["To Max"].default_value = 0.88, 1.0
    g.link(speck.outputs["Distance"], sp.inputs["Value"])
    m1 = g.node("ShaderNodeMix", (-750, -350), F_S, label="x specks")
    m1.data_type, m1.blend_type = "RGBA", "MULTIPLY"
    m1.inputs["Factor"].default_value = 1.0
    g.link(cr.outputs["Color"], sock(m1.inputs, "A"))
    g.link(sp.outputs["Result"], sock(m1.inputs, "B"))
    m2 = g.node("ShaderNodeMix", (-550, -150), F_S, label="x per-tile tone / grout")
    m2.data_type, m2.blend_type = "RGBA", "MULTIPLY"
    m2.inputs["Factor"].default_value = 1.0
    g.link(sock(m1.outputs, "Result"), sock(m2.inputs, "A"))
    g.link(br.outputs["Color"], sock(m2.inputs, "B"))
    rough = g.node("ShaderNodeMapRange", (-550, 250), F_F, label="grout matte")
    rough.inputs["To Min"].default_value, rough.inputs["To Max"].default_value = roughness, 0.85
    g.link(br.outputs["Fac"], rough.inputs["Value"])
    bump = g.node("ShaderNodeBump", (-550, 500), F_F, label="recessed joints", Distance=0.001)
    bump.invert = True
    g.link(br.outputs["Fac"], bump.inputs["Height"])
    b = g.node("ShaderNodeBsdfPrincipled", (-200, 0), F_F, label="stone", IOR=1.5)
    g.link(sock(m2.outputs, "Result"), b.inputs["Base Color"])
    g.link(rough.outputs["Result"], b.inputs["Roughness"])
    g.link(bump.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Coat Roughness"].default_value = coat_rough
    out = g.node("ShaderNodeOutputMaterial", (100, 0))
    g.link(b.outputs["BSDF"], out.inputs["Surface"])
    return mat


def long_pavers(tex_id, name, target, row=0.18, length=0.75, mortar=0.008, long_axis="Y", scale=0.5,
                tone=((0.95, 0.95, 0.95), (0.72, 0.72, 0.71)), mortar_color=(0.22, 0.22, 0.22)):
    """Running-bond strips over a concrete map. `long_axis` = world axis of the strips' length
    (read it from the vanishing point the long joints run to). Mortar < 8 mm vanishes at frame
    scale; joints recessed by bump."""
    m = albedo_material(tex_id, name, target, scale=scale)
    N, L = m.node_tree.nodes, m.node_tree.links
    geo = N.new("ShaderNodeNewGeometry")
    sep = N.new("ShaderNodeSeparateXYZ"); comb = N.new("ShaderNodeCombineXYZ")
    L.new(geo.outputs["Position"], sep.inputs["Vector"])
    other = "X" if long_axis.upper() == "Y" else "Y"
    L.new(sep.outputs[long_axis.upper()], comb.inputs["X"]); L.new(sep.outputs[other], comb.inputs["Y"])
    br = N.new("ShaderNodeTexBrick"); br.offset = 0.5; br.offset_frequency = 1
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Brick Width"].default_value = length
    br.inputs["Row Height"].default_value = row
    br.inputs["Mortar Size"].default_value = mortar
    br.inputs["Mortar Smooth"].default_value = 0.3
    br.inputs["Bias"].default_value = 0.0
    br.inputs["Color1"].default_value = (*tone[0], 1); br.inputs["Color2"].default_value = (*tone[1], 1)
    br.inputs["Mortar"].default_value = (*mortar_color, 1)
    L.new(comb.outputs["Vector"], br.inputs["Vector"])
    bsdf = _principled(m)
    src = bsdf.inputs["Base Color"].links[0].from_socket
    mul = N.new("ShaderNodeMix"); mul.data_type = "RGBA"; mul.blend_type = "MULTIPLY"
    mul.inputs["Factor"].default_value = 1.0
    L.new(src, sock(mul.inputs, "A")); L.new(br.outputs["Color"], sock(mul.inputs, "B"))
    L.new(sock(mul.outputs, "Result"), bsdf.inputs["Base Color"])
    bump = N.new("ShaderNodeBump"); bump.inputs["Distance"].default_value = 0.004; bump.invert = True
    L.new(br.outputs["Fac"], bump.inputs["Height"])
    if bsdf.inputs["Normal"].links:
        L.new(bsdf.inputs["Normal"].links[0].from_node.outputs["Normal"], bump.inputs["Normal"])
    L.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m
