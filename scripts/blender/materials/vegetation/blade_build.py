"""Blade build; canonical implementation behind vegetation."""

import bpy

from materials.shared.node_graph import NodeGraph

from materials.shared.node_graph import active_socket

from materials.vegetation.blade_config import BLADE_DEFAULTS

from materials.vegetation.blade_wet import _wet

def blade_material(name, tex=None, colour=(0.12, 0.15, 0.05), wet=None, dry_patch=0.55):
    """Thin blade: Principled + Translucent (Add); per-instance value 0.8-1.15 and a patchy straw mix; optional wet film."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = NodeGraph(mat)
    out = g.node_with_props("ShaderNodeOutputMaterial", (1300, 0))
    if tex:
        t = g.node_with_props("ShaderNodeTexImage", (-900, 200)); t.image = bpy.data.images.load(tex, check_existing=True)
        col = t.outputs["Color"]
    else:
        rgb = g.node_with_props("ShaderNodeRGB", (-900, 200)); rgb.outputs[0].default_value = (*colour, 1.0)
        col = rgb.outputs[0]
    # per-instance variation (RULES MAT_06) and dryness patches across the field (MAT_05)
    oi = g.node_with_props("ShaderNodeObjectInfo", (-900, -200))
    val = g.map_range(oi.outputs["Random"], 0.0, 1.0, (-650, -100), 0.8, 1.15)
    nz = g.node_with_props("ShaderNodeTexNoise", (-650, -350)); nz.inputs["Scale"].default_value = 0.08; nz.inputs["Detail"].default_value = 3.0
    g.link(oi.outputs["Location"], nz.inputs["Vector"])
    dry = g.map_range(nz.outputs[0], 0.5, 0.75, (-450, -350), 0.0, dry_patch)
    straw = g.node_with_props("ShaderNodeHueSaturation", (-450, 150))
    straw.inputs["Hue"].default_value = 0.455; straw.inputs["Saturation"].default_value = 0.75
    straw.inputs["Value"].default_value = 1.35
    g.link(col, straw.inputs["Color"])
    mix = g.node_with_props("ShaderNodeMix", (-200, 200), data_type="RGBA")
    g.link(dry, mix.inputs["Factor"]); g.link(col, active_socket(mix.inputs, "A")); g.link(straw.outputs[0], active_socket(mix.inputs, "B"))
    cmb = g.node_with_props("ShaderNodeCombineColor", (-200, -100))
    for i in range(3):
        g.link(val, cmb.inputs[i])
    tone = g.node_with_props("ShaderNodeMix", (0, 200), data_type="RGBA", blend_type="MULTIPLY")
    tone.inputs["Factor"].default_value = 1.0
    g.link(active_socket(mix.outputs, "Result"), active_socket(tone.inputs, "A")); g.link(cmb.outputs[0], active_socket(tone.inputs, "B"))
    p = g.node_with_props("ShaderNodeBsdfPrincipled", (500, 250))
    p.inputs["Roughness"].default_value = BLADE_DEFAULTS["rough"]; p.inputs["IOR"].default_value = BLADE_DEFAULTS["ior"]
    base = active_socket(tone.outputs, "Result")
    g.link(base, p.inputs["Base Color"])
    if wet:
        base = _wet(g, p, base, oi, wet)
    tg = g.node_with_props("ShaderNodeMix", (500, -150), data_type="RGBA", blend_type="MULTIPLY")
    tg.inputs["Factor"].default_value = 1.0; active_socket(tg.inputs, "B").default_value = (BLADE_DEFAULTS["trans_gain"],) * 3 + (1.0,)
    g.link(base, active_socket(tg.inputs, "A"))
    tl = g.node_with_props("ShaderNodeBsdfTranslucent", (750, -150)); g.link(active_socket(tg.outputs, "Result"), tl.inputs["Color"])
    add = g.node_with_props("ShaderNodeAddShader", (950, 0))
    g.link(p.outputs[0], add.inputs[0]); g.link(tl.outputs[0], add.inputs[1])
    g.link(add.outputs[0], out.inputs[0])
    return mat
