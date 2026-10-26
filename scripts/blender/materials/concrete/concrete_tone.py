"""Concrete tone; canonical implementation behind concrete."""

from materials.shared.nodes import G, sock

from materials.shared.pbr_maps import _ph_maps
from materials.shared.principled import _principled
from materials.shared.map_measure import map_mean

def retone(mat, target_rgb, tex_id, saturation=0.25):
    """Desaturate a concrete_study map toward its luminance, then scale its measured linear mean to `target_rgb` (a dark brown scan -> light grey concrete keeps its pits and pores)."""
    nt = mat.node_tree
    diff = next(n for n in nt.nodes if n.label == "diffuse")
    tone = next(n for n in nt.nodes if n.label == "color_mult (tone match)")
    mean = map_mean(tex_id)
    # a luminance mix (RGB to BW, Mix at `saturation`) - exactly what the gain below assumes
    # (Hue/Saturation scales HSV saturation and pulls channels toward the max: ~25 % too bright)
    lum = 0.2126 * mean[0] + 0.7152 * mean[1] + 0.0722 * mean[2]
    desat = [lum * (1 - saturation) + c * saturation for c in mean]
    g = G(nt)
    bw = g.node("ShaderNodeRGBToBW", (tone.location.x - 300, tone.location.y + 250), label="luminance")
    ds = g.n("ShaderNodeMix", (tone.location.x - 150, tone.location.y + 150), data_type="RGBA", label="desaturate")
    ds.inputs["Factor"].default_value = saturation
    for l in list(sock(tone.inputs, "A").links):
        nt.links.remove(l)
    g.link(diff.outputs["Color"], bw.inputs["Color"])
    g.link(bw.outputs["Val"], sock(ds.inputs, "A")); g.link(diff.outputs["Color"], sock(ds.inputs, "B"))
    g.link(sock(ds.outputs, "Result"), sock(tone.inputs, "A"))
    sock(tone.inputs, "B").default_value = (*[t / c for t, c in zip(target_rgb, desat)], 1.0)
    return [t / c for t, c in zip(target_rgb, desat)]
