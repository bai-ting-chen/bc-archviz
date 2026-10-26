"""Blade build; canonical implementation behind vegetation."""

import bpy

from materials.shared.nodes import G

from materials.shared.nodes import sock

from materials.vegetation.blade_config import BLADE

from materials.vegetation.blade_dew import _dew

from materials.vegetation.blade_wet import _wet

def blade_material(name, tex=None, colour=(0.12, 0.15, 0.05), wet=None, dew=None, dry_patch=0.55):
    """Thin blade: Principled + Translucent (Add); per-instance value 0.8-1.15 and a patchy straw mix; optional wet film / dew."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = G(mat)
    out = g.n("ShaderNodeOutputMaterial", (1300, 0))
    if tex:
        t = g.n("ShaderNodeTexImage", (-900, 200)); t.image = bpy.data.images.load(tex, check_existing=True)
        col = t.outputs["Color"]
    else:
        rgb = g.n("ShaderNodeRGB", (-900, 200)); rgb.outputs[0].default_value = (*colour, 1.0)
        col = rgb.outputs[0]
    # per-instance variation (RULES MAT_06) and dryness patches across the field (MAT_05)
    oi = g.n("ShaderNodeObjectInfo", (-900, -200))
    val = g.range(oi.outputs["Random"], 0.0, 1.0, (-650, -100), 0.8, 1.15)
    nz = g.n("ShaderNodeTexNoise", (-650, -350)); nz.inputs["Scale"].default_value = 0.08; nz.inputs["Detail"].default_value = 3.0
    g.link(oi.outputs["Location"], nz.inputs["Vector"])
    dry = g.range(nz.outputs[0], 0.5, 0.75, (-450, -350), 0.0, dry_patch)
    straw = g.n("ShaderNodeHueSaturation", (-450, 150))
    straw.inputs["Hue"].default_value = 0.455; straw.inputs["Saturation"].default_value = 0.75
    straw.inputs["Value"].default_value = 1.35
    g.link(col, straw.inputs["Color"])
    mix = g.n("ShaderNodeMix", (-200, 200), data_type="RGBA")
    g.link(dry, mix.inputs["Factor"]); g.link(col, sock(mix.inputs, "A")); g.link(straw.outputs[0], sock(mix.inputs, "B"))
    cmb = g.n("ShaderNodeCombineColor", (-200, -100))
    for i in range(3):
        g.link(val, cmb.inputs[i])
    tone = g.n("ShaderNodeMix", (0, 200), data_type="RGBA", blend_type="MULTIPLY")
    tone.inputs["Factor"].default_value = 1.0
    g.link(sock(mix.outputs, "Result"), sock(tone.inputs, "A")); g.link(cmb.outputs[0], sock(tone.inputs, "B"))
    p = g.n("ShaderNodeBsdfPrincipled", (500, 250))
    p.inputs["Roughness"].default_value = BLADE["rough"]; p.inputs["IOR"].default_value = BLADE["ior"]
    base = sock(tone.outputs, "Result")
    g.link(base, p.inputs["Base Color"])
    if wet:
        base = _wet(g, p, base, oi, wet)
    tg = g.n("ShaderNodeMix", (500, -150), data_type="RGBA", blend_type="MULTIPLY")
    tg.inputs["Factor"].default_value = 1.0; sock(tg.inputs, "B").default_value = (BLADE["trans_gain"],) * 3 + (1.0,)
    g.link(base, sock(tg.inputs, "A"))
    tl = g.n("ShaderNodeBsdfTranslucent", (750, -150)); g.link(sock(tg.outputs, "Result"), tl.inputs["Color"])
    add = g.n("ShaderNodeAddShader", (950, 0))
    g.link(p.outputs[0], add.inputs[0]); g.link(tl.outputs[0], add.inputs[1])
    shader = _dew(g, add.outputs[0], dew) if dew else add.outputs[0]
    g.link(shader, out.inputs[0])
    return mat
