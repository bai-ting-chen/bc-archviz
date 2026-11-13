"""Blade wet; canonical implementation behind vegetation."""

from materials.shared.node_graph import active_socket

def _wet(g, p, tone, oi, W):
    """Wet film: wetness in soft patches (instance location), base -> dry^gamma, water coat."""
    nz = g.node_with_props("ShaderNodeTexNoise", (-650, -650), noise_dimensions="4D")
    nz.inputs["Scale"].default_value = W["patch_scale"]; nz.inputs["W"].default_value = 3.3
    g.link(oi.outputs["Location"], nz.inputs["Vector"])
    wet = g.map_range(nz.outputs[0], 0.35, 0.65, (-450, -650), W["range"][0], W["range"][1], label="wetness")
    gm = g.node_with_props("ShaderNodeGamma", (100, 400)); gm.inputs["Gamma"].default_value = W["gamma"]
    g.link(tone, gm.inputs["Color"])
    mx = g.node_with_props("ShaderNodeMix", (250, 300), data_type="RGBA")
    g.link(wet, mx.inputs["Factor"]); g.link(tone, active_socket(mx.inputs, "A")); g.link(gm.outputs[0], active_socket(mx.inputs, "B"))
    g.link(active_socket(mx.outputs, "Result"), p.inputs["Base Color"])
    g.link(g.math("MULTIPLY", wet, W["coat"], (100, -650)), p.inputs["Coat Weight"])
    p.inputs["Coat IOR"].default_value = 1.33
    p.inputs["Coat Roughness"].default_value = W["coat_rough"]
    return active_socket(mx.outputs, "Result")
