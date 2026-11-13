"""Stone tiles; canonical implementation behind stone."""

import bpy

from materials.shared.node_graph import NodeGraph


def stone_tiles(name="LIMESTONE", tile=(1.2, 0.6), grout=0.002, albedo=(0.46, 0.41, 0.33),
                var=0.05, roughness=0.35, coat=0.0, coat_rough=0.08, uv="BoxUV"):
    """Large-format stone/porcelain on real-metre BoxUV: Brick Texture (offset 0) for the joints,
    per-tile tone from the brick colour pair, cloudy limestone mottling + fine specks, a soft coat
    for a honed-and-sealed floor. Grout darker and matte, joints slightly recessed (bump)."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = NodeGraph(mat)
    g.frame("Tiles %.1f x %.1f m" % tile, (0.20, 0.24, 0.30))
    g.frame("Stone body", (0.26, 0.24, 0.20))
    g.frame("Finish", (0.22, 0.28, 0.22))
    F_T, F_S, F_F = list(g.frames)
    co = g.uv_map(uv, (-1500, 0), F_T)
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
    cr = g.color_ramp((-1000, -350), F_S, [(0.3, tuple(c * 0.90 for c in albedo)), (0.7, tuple(min(1, c * 1.08) for c in albedo))],
               "limestone tone")
    g.link(cloud.outputs["Fac"], cr.inputs["Fac"])
    speck = g.node("ShaderNodeTexVoronoi", (-1250, -650), F_S, label="fossil specks 3 mm", Scale=330.0)
    g.link(co, speck.inputs["Vector"])
    sp = g.node("ShaderNodeMapRange", (-1000, -650), F_S, label="speck mask")
    sp.inputs["From Min"].default_value, sp.inputs["From Max"].default_value = 0.0, 0.12
    sp.inputs["To Min"].default_value, sp.inputs["To Max"].default_value = 0.88, 1.0
    g.link(speck.outputs["Distance"], sp.inputs["Value"])
    m1 = g.mix(cr.outputs["Color"], sp.outputs["Result"], 1.0, (-750, -350), F_S, blend="MULTIPLY",
               label="x specks")
    m2 = g.mix(m1, br.outputs["Color"], 1.0, (-550, -150), F_S, blend="MULTIPLY",
               label="x per-tile tone / grout")
    rough = g.node("ShaderNodeMapRange", (-550, 250), F_F, label="grout matte")
    rough.inputs["To Min"].default_value, rough.inputs["To Max"].default_value = roughness, 0.85
    g.link(br.outputs["Fac"], rough.inputs["Value"])
    bump = g.node("ShaderNodeBump", (-550, 500), F_F, label="recessed joints", Distance=0.001)
    bump.invert = True
    g.link(br.outputs["Fac"], bump.inputs["Height"])
    b = g.node("ShaderNodeBsdfPrincipled", (-200, 0), F_F, label="stone", IOR=1.5)
    g.link(m2, b.inputs["Base Color"])
    g.link(rough.outputs["Result"], b.inputs["Roughness"])
    g.link(bump.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Coat Roughness"].default_value = coat_rough
    out = g.node("ShaderNodeOutputMaterial", (100, 0))
    g.link(b.outputs["BSDF"], out.inputs["Surface"])
    return mat
