"""Lux textured; canonical implementation behind luxcore."""

import os, json

import bpy

import core.archviz as archviz

from renderer.luxcore.dust_config import DUST_TINT

def lux_textured(name, folder, me, dust_png=None, uv_tex="BoxUV", uv_dust="DustUV", randomized=True, specular=0.5):
    """Native LuxCore Disney from a generated/scanned map folder; `me` = the mesh it goes on
    (its UV layer indices are baked into the tree, so one material per mesh layout)."""
    meta = archviz.read_meta(folder)
    i_tex = me.uv_layers.find(uv_tex); i_dust = me.uv_layers.find(uv_dust)
    if i_tex < 0 or (dust_png and i_dust < 0):
        raise RuntimeError("%s lacks UV layer %s / %s" % (me.name, uv_tex, uv_dust))
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
        mix = N("LuxCoreNodeTexColorMix"); mix.mode = "mix"
        mix.inputs["Color 1"].default_value = (1, 1, 1); mix.inputs["Color 2"].default_value = DUST_TINT
        L(dust.outputs["Color"], mix.inputs["Fac"])
        mul = N("LuxCoreNodeTexColorMix"); mul.mode = "scale"
        L(col, mul.inputs["Color 1"]); L(mix.outputs["Color"], mul.inputs["Color 2"]); col = mul.outputs["Color"]
    L(col, dis.inputs["Base Color"]); L(dis.outputs["Material"], out.inputs["Material"])
    m["texture_size_m"] = meta["dimensions_mm"][0] / 1000.0
    return m
