"""Concrete tone; canonical implementation behind concrete."""

from materials.shared.node_graph import NodeGraph, active_socket

from materials.shared.pbr_maps import _ph_maps
from materials.shared.principled import _principled
from materials.shared.map_measurements import map_mean_linear_rgb

def retone(mat, target_rgb, tex_id, saturation=0.25):
    """Desaturate a concrete_study map toward its luminance, then scale its measured linear mean to `target_rgb` (a dark brown scan -> light grey concrete keeps its pits and pores)."""
    nt = mat.node_tree
    diff = next(n for n in nt.nodes if n.label == "diffuse")
    tone = next(n for n in nt.nodes if n.label == "color_mult (tone match)")
    mean = map_mean_linear_rgb(tex_id)
    # a luminance mix (RGB to BW, Mix at `saturation`) - exactly what the gain below assumes
    # (Hue/Saturation scales HSV saturation and pulls channels toward the max: ~25 % too bright)
    lum = 0.2126 * mean[0] + 0.7152 * mean[1] + 0.0722 * mean[2]
    desat = [lum * (1 - saturation) + c * saturation for c in mean]
    g = NodeGraph(nt)
    bw = g.node("ShaderNodeRGBToBW", (tone.location.x - 300, tone.location.y + 250), label="luminance")
    ds = g.node_with_props("ShaderNodeMix", (tone.location.x - 150, tone.location.y + 150), data_type="RGBA", label="desaturate")
    ds.inputs["Factor"].default_value = saturation
    for l in list(active_socket(tone.inputs, "A").links):
        nt.links.remove(l)
    g.link(diff.outputs["Color"], bw.inputs["Color"])
    g.link(bw.outputs["Val"], active_socket(ds.inputs, "A")); g.link(diff.outputs["Color"], active_socket(ds.inputs, "B"))
    g.link(active_socket(ds.outputs, "Result"), active_socket(tone.inputs, "A"))
    active_socket(tone.inputs, "B").default_value = (*[t / c for t, c in zip(target_rgb, desat)], 1.0)
    return [t / c for t, c in zip(target_rgb, desat)]
