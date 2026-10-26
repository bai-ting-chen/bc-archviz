"""Blade wet; canonical implementation behind vegetation."""

from materials.shared.nodes import sock

def _wet(g, p, tone, oi, W):
    """Wet film: wetness in soft patches (instance location), base -> dry^gamma, water coat."""
    nz = g.n("ShaderNodeTexNoise", (-650, -650), noise_dimensions="4D")
    nz.inputs["Scale"].default_value = W["patch_scale"]; nz.inputs["W"].default_value = 3.3
    g.link(oi.outputs["Location"], nz.inputs["Vector"])
    wet = g.range(nz.outputs[0], 0.35, 0.65, (-450, -650), W["range"][0], W["range"][1], label="wetness")
    gm = g.n("ShaderNodeGamma", (100, 400)); gm.inputs["Gamma"].default_value = W["gamma"]
    g.link(tone, gm.inputs["Color"])
    mx = g.n("ShaderNodeMix", (250, 300), data_type="RGBA")
    g.link(wet, mx.inputs["Factor"]); g.link(tone, sock(mx.inputs, "A")); g.link(gm.outputs[0], sock(mx.inputs, "B"))
    g.link(sock(mx.outputs, "Result"), p.inputs["Base Color"])
    g.link(g.math("MULTIPLY", wet, W["coat"], (100, -650)), p.inputs["Coat Weight"])
    p.inputs["Coat IOR"].default_value = 1.33
    p.inputs["Coat Roughness"].default_value = W["coat_rough"]
    return sock(mx.outputs, "Result")
