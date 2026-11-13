"""Concrete masks; canonical implementation behind concrete."""

def _edge_mask(graph, radius, location, frame, label):
    """Convexity mask from the Bevel node: 1 - dot(bevelled normal, true normal), normalised so
    a 90-degree arris reads 1.0. Convex-edge mask with
    sample_spread ~= radius."""
    geo = graph.node("ShaderNodeNewGeometry", (location[0] - 400, location[1] - 120), frame)
    bev = graph.node("ShaderNodeBevel", (location[0] - 400, location[1]), frame, label=label, Radius=radius)
    bev.samples = 16
    dot = graph.node("ShaderNodeVectorMath", (location[0] - 200, location[1]), frame)
    dot.operation = "DOT_PRODUCT"
    graph.link(bev.outputs["Normal"], dot.inputs[0])
    graph.link(geo.outputs["Normal"], dot.inputs[1])  # shading normal: smooth cylinders stay clean
    inv = graph.node("ShaderNodeMapRange", (location[0], location[1]), frame, label=label + " (0..1)")
    inv.inputs["From Min"].default_value, inv.inputs["From Max"].default_value = 1.0, 0.7071
    graph.link(dot.outputs["Value"], inv.inputs["Value"])
    return inv.outputs["Result"]

def _bevel_chips(graph, chip_spread, chip_in, noise_scale, noise_band, F_WEAR):
    """Chip mask: Bevel convexity -> remap -> x noise (shading only)."""
    chip = _edge_mask(graph, chip_spread, (-700, -700), F_WEAR, "Chip curvature")
    chip_r = graph.node("ShaderNodeMapRange", (-480, -700), F_WEAR, label="Chip Remap (TexRemap)")
    chip_r.inputs["From Min"].default_value, chip_r.inputs["From Max"].default_value = chip_in
    graph.link(chip, chip_r.inputs["Value"])
    noise = graph.node("ShaderNodeTexNoise", (-700, -950), F_WEAR, label="Wear Noise",
                   Scale=noise_scale, Detail=6.0)
    noise_r = graph.node("ShaderNodeMapRange", (-480, -950), F_WEAR, label="noise band")
    noise_r.inputs["From Min"].default_value, noise_r.inputs["From Max"].default_value = noise_band
    graph.link(noise.outputs[0], noise_r.inputs["Value"])
    chips = graph.node("ShaderNodeMath", (-280, -800), F_WEAR, label="chips x noise")
    chips.operation = "MULTIPLY"
    graph.link(chip_r.outputs["Result"], chips.inputs[0])
    graph.link(noise_r.outputs["Result"], chips.inputs[1])
    return chips.outputs["Value"]
