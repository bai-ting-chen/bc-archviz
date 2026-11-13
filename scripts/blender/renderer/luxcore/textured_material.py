"""Lux textured; canonical implementation behind luxcore."""

import os

import bpy

import core.archviz as archviz

from renderer.luxcore.dust_config import DUST_GAIN, DUST_SATURATION, LINE_GAIN, RGB_LUMINANCE

def textured_material(name, folder, mesh, dust_png=None, uv_tex="BoxUV", uv_dust="DustUV", randomized=True, specular=0.5):
    """Native LuxCore Disney from a generated/scanned map folder; `mesh` = the mesh it goes on
    (its UV layer indices are baked into the tree, so one material per mesh layout)."""
    meta = archviz.read_meta(folder)
    i_tex = mesh.uv_layers.find(uv_tex); i_dust = mesh.uv_layers.find(uv_dust)
    if i_tex < 0 or (dust_png and i_dust < 0):
        raise RuntimeError("%s lacks UV layer %s / %s" % (mesh.name, uv_tex, uv_dust))
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    tree = bpy.data.node_groups.new(name + "_lux", "luxcore_material_nodes")
    m.luxcore.node_tree = tree; m.luxcore.use_cycles_nodes = False
    N, L = tree.nodes.new, tree.links.new
    out = N("LuxCoreNodeMatOutput"); dis = N("LuxCoreNodeMatDisney")
    dis.inputs["Specular"].default_value = specular
    def image(path, gamma, idx, rnd):
        mp = N("LuxCoreNodeTexMapping2D"); mp.mapping_type = "uvmapping2d"; mp.uvindex = idx
        t = N("LuxCoreNodeTexImagemap"); t.image = bpy.data.images.load(path, check_existing=True)
        t.gamma = gamma; t.wrap = "repeat"; t.randomized_tiling = rnd
        L(mp.outputs["2D Mapping"], t.inputs["2D Mapping"]); return t
    diff = image(os.path.join(folder, meta["maps"]["diff"]), 2.2, i_tex, randomized)
    rough = image(os.path.join(folder, meta["maps"]["rough"]), 1.0, i_tex, randomized)
    split = N("LuxCoreNodeTexSplitFloat3"); L(rough.outputs["Color"], split.inputs["Color"])
    L(split.outputs["R"], dis.inputs["Roughness"])
    col = diff.outputs["Color"]
    if dust_png:
        dust = image(dust_png, 1.0, i_dust, False); dust.wrap = "clamp"
        masks = N("LuxCoreNodeTexSplitFloat3")
        L(dust.outputs["Color"], masks.inputs["Color"])
        rough_mix = N("LuxCoreNodeTexColorMix")
        rough_mix.mode = "mix"
        L(split.outputs["R"], rough_mix.inputs["Color 1"])
        rough_mix.inputs["Color 2"].default_value = (0.93,) * 3
        L(masks.outputs["R"], rough_mix.inputs["Fac"])
        L(rough_mix.outputs["Color"], dis.inputs["Roughness"])
        col = _relative_edge_color(N, L, col, masks)
    L(col, dis.inputs["Base Color"]); L(dis.outputs["Material"], out.inputs["Material"])
    m["texture_size_m"] = meta["dimensions_mm"][0] / 1000.0
    return m


def _relative_edge_color(N, L, col, masks):
    """Apply relative dust to the texture, then give the relative line target priority."""
    luma = N("LuxCoreNodeTexDotProduct")
    L(col, luma.inputs["Vector 1"])
    luma.inputs["Vector 2"].default_value = RGB_LUMINANCE
    desat = N("LuxCoreNodeTexColorMix")
    desat.mode = "mix"
    desat.inputs["Fac"].default_value = 1.0 - DUST_SATURATION
    L(col, desat.inputs["Color 1"])
    L(luma.outputs["Value"], desat.inputs["Color 2"])
    gain = N("LuxCoreNodeTexColorMix")
    gain.mode = "scale"
    L(desat.outputs["Color"], gain.inputs["Color 1"])
    gain.inputs["Color 2"].default_value = DUST_GAIN
    relative = N("LuxCoreNodeTexColorMix")
    relative.mode = "mix"
    L(col, relative.inputs["Color 1"])
    L(gain.outputs["Color"], relative.inputs["Color 2"])
    L(masks.outputs["G"], relative.inputs["Fac"])
    # Line takes priority over dust; both targets derive from the original texture.
    line_gain = N("LuxCoreNodeTexColorMix")
    line_gain.mode = "scale"
    L(col, line_gain.inputs["Color 1"])
    line_gain.inputs["Color 2"].default_value = (LINE_GAIN,) * 3
    line_mix = N("LuxCoreNodeTexColorMix")
    line_mix.mode = "mix"
    L(relative.outputs["Color"], line_mix.inputs["Color 1"])
    L(line_gain.outputs["Color"], line_mix.inputs["Color 2"])
    L(masks.outputs["R"], line_mix.inputs["Fac"])
    return line_mix.outputs["Color"]
