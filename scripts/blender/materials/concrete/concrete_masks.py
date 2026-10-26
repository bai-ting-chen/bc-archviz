"""Concrete masks; canonical implementation behind concrete."""

def _edge_mask(g, radius, loc, frame, label):
    """Convexity mask from the Bevel node: 1 - dot(bevelled normal, true normal), normalised so
    a 90-degree arris reads 1.0. Convex-edge mask with
    sample_spread ~= radius."""
    geo = g.node("ShaderNodeNewGeometry", (loc[0] - 400, loc[1] - 120), frame)
    bev = g.node("ShaderNodeBevel", (loc[0] - 400, loc[1]), frame, label=label, Radius=radius)
    bev.samples = 16
    dot = g.node("ShaderNodeVectorMath", (loc[0] - 200, loc[1]), frame)
    dot.operation = "DOT_PRODUCT"
    g.link(bev.outputs["Normal"], dot.inputs[0])
    g.link(geo.outputs["Normal"], dot.inputs[1])  # shading normal: smooth cylinders stay clean
    inv = g.node("ShaderNodeMapRange", (loc[0], loc[1]), frame, label=label + " (0..1)")
    inv.inputs["From Min"].default_value, inv.inputs["From Max"].default_value = 1.0, 0.7071
    g.link(dot.outputs["Value"], inv.inputs["Value"])
    return inv.outputs["Result"]

def _bevel_chips(g, chip_spread, chip_in, noise_scale, noise_band, F_WEAR):
    """Chip mask: Bevel convexity -> remap -> x noise (shading only)."""
    chip = _edge_mask(g, chip_spread, (-700, -700), F_WEAR, "Chip curvature")
    chip_r = g.node("ShaderNodeMapRange", (-480, -700), F_WEAR, label="Chip Remap (TexRemap)")
    chip_r.inputs["From Min"].default_value, chip_r.inputs["From Max"].default_value = chip_in
    g.link(chip, chip_r.inputs["Value"])
    noise = g.node("ShaderNodeTexNoise", (-700, -950), F_WEAR, label="Wear Noise",
                   Scale=noise_scale, Detail=6.0)
    noise_r = g.node("ShaderNodeMapRange", (-480, -950), F_WEAR, label="noise band")
    noise_r.inputs["From Min"].default_value, noise_r.inputs["From Max"].default_value = noise_band
    g.link(noise.outputs[0], noise_r.inputs["Value"])
    chips = g.node("ShaderNodeMath", (-280, -800), F_WEAR, label="chips x noise")
    chips.operation = "MULTIPLY"
    g.link(chip_r.outputs["Result"], chips.inputs[0])
    g.link(noise_r.outputs["Result"], chips.inputs[1])
    return chips.outputs["Value"]
