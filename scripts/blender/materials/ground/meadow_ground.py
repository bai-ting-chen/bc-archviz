"""Meadow ground; canonical implementation behind ground."""

import bpy

from materials.shared.nodes import G, sock

from scene.environment.terrain import BARE, BARE_W, _noise4

def ground_material(thatch_tex, soil_tex, name="GROUND", bare=BARE, wet_gamma=None, wet_rough=0.6):
    """Ground under a meadow: a dead-grass/thatch texture, soil only where the bare-soil noise
    (same 4D noise and W as scatter.meadow_layer_group) opens the sward. wet_gamma (e.g. 1.4):
    wet ground = dry^gamma (darker, more saturated) and roughness x wet_rough."""
    from materials.shared.pbr_maps import _ph_maps
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = G(mat)
    out = g.n("ShaderNodeOutputMaterial", (1300, 0))
    bsdf = g.n("ShaderNodeBsdfPrincipled", (1000, 0)); g.link(bsdf.outputs[0], out.inputs[0])
    geo = g.n("ShaderNodeNewGeometry", (-1200, 0))
    bn = _noise4(g, geo.outputs["Position"], bare[0], BARE_W, (-900, 600), 4.0, 0.5)
    bm = g.range(bn, bare[1], bare[2], (-700, 600), smooth=True, label="bare soil")
    sets = []
    for i, tex in enumerate((thatch_tex, soil_tex)):
        maps, meta = _ph_maps(tex)
        mp = g.n("ShaderNodeMapping", (-900, -400 * i))
        mp.inputs["Scale"].default_value = (1000 / meta["dimensions_mm"][0],) * 3
        g.link(geo.outputs["Position"], mp.inputs["Vector"])
        d = g.img(maps["diff"], "sRGB", (-600, -400 * i), None, mp.outputs[0])
        a = g.img(maps["arm"], "Non-Color", (-600, -400 * i - 200), None, mp.outputs[0])
        for n in (d, a):
            n.projection, n.projection_blend = "BOX", 0.2   # world-space box mapping, no UVs
        sep = g.n("ShaderNodeSeparateColor", (-300, -400 * i - 200)); g.link(a.outputs["Color"], sep.inputs[0])
        sets.append((d.outputs["Color"], sep.outputs["Green"]))
    mc = g.n("ShaderNodeMix", (300, 200), data_type="RGBA")
    g.link(bm, mc.inputs["Factor"]); g.link(sets[0][0], sock(mc.inputs, "A")); g.link(sets[1][0], sock(mc.inputs, "B"))
    mr = g.n("ShaderNodeMix", (300, -100), data_type="FLOAT")
    g.link(bm, mr.inputs["Factor"]); g.link(sets[0][1], sock(mr.inputs, "A")); g.link(sets[1][1], sock(mr.inputs, "B"))
    col, rough = sock(mc.outputs, "Result"), sock(mr.outputs, "Result")
    if wet_gamma:
        gm = g.n("ShaderNodeGamma", (600, 200)); gm.inputs["Gamma"].default_value = wet_gamma
        g.link(col, gm.inputs["Color"]); col = gm.outputs[0]
        rough = g.math("MULTIPLY", rough, wet_rough, (600, -100))
    g.link(col, bsdf.inputs["Base Color"]); g.link(rough, bsdf.inputs["Roughness"])
    return mat
