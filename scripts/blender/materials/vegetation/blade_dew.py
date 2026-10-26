"""Blade dew; canonical implementation behind vegetation."""

def _dew(g, shader, D):
    """Effective-reflectance dew beads mixed over `shader`: Voronoi beads in the object's own
    space (they stay on their blade), hemispherical lens normal, up-facing surfaces, near camera."""
    tc = g.n("ShaderNodeTexCoord", (-900, -1100))
    oi = g.n("ShaderNodeObjectInfo", (-1100, -1250))                 # per-instance offset (RULES MAT_06)
    off = g.n("ShaderNodeVectorMath", (-850, -1250), operation="MULTIPLY_ADD")
    g.link(oi.outputs["Random"], off.inputs[0]); off.inputs[1].default_value = (97.0, 61.0, 43.0)
    g.link(tc.outputs["Object"], off.inputs[2])
    vor = g.n("ShaderNodeTexVoronoi", (-700, -1100)); vor.inputs["Scale"].default_value = 1.0 / D["cell"]
    g.link(off.outputs[0], vor.inputs["Vector"])
    sep = g.n("ShaderNodeSeparateColor", (-500, -1250)); g.link(vor.outputs["Color"], sep.inputs[0])
    r = g.math("ADD", g.math("MULTIPLY", sep.outputs["Red"], D["r"][1] - D["r"][0], (-350, -1250)), D["r"][0], (-200, -1250))
    d = vor.outputs["Distance"]
    bead = g.math("MULTIPLY", g.math("LESS_THAN", d, r, (-350, -1100)),
                  g.math("LESS_THAN", sep.outputs["Green"], D["cover"], (-350, -1400)), (-200, -1100))
    under = g.math("SUBTRACT", g.math("MULTIPLY", r, r, (-50, -1000)), g.math("MULTIPLY", d, d, (-50, -1100)), (100, -1050))
    cap = g.math("DIVIDE", g.math("SQRT", g.math("MAXIMUM", under, 0.0, (250, -1050)), 0.0, (400, -1050)), r, (550, -1050))
    bump = g.n("ShaderNodeBump", (700, -1100)); bump.inputs["Distance"].default_value = D["cell"] * sum(D["r"]) / 2
    g.link(g.math("MULTIPLY", cap, bead, (600, -1200)), bump.inputs["Height"])
    gl = g.n("ShaderNodeBsdfGlossy", (900, -1100))
    gl.inputs["Color"].default_value = (D["reflect"],) * 3 + (1.0,)
    gl.inputs["Roughness"].default_value = D["rough"]
    g.link(bump.outputs["Normal"], gl.inputs["Normal"])
    geo = g.n("ShaderNodeNewGeometry", (-500, -1550))
    sn = g.n("ShaderNodeSeparateXYZ", (-350, -1550)); g.link(geo.outputs["Normal"], sn.inputs[0])
    up = g.math("GREATER_THAN", sn.outputs["Z"], D["up"], (-200, -1550))
    cam = g.n("ShaderNodeCameraData", (-500, -1700))
    near = g.range(cam.outputs["View Distance"], D["fade"][0], D["fade"][1], (-200, -1700), 1.0, 0.0, label="near camera")
    fac = g.math("MULTIPLY", g.math("MULTIPLY", bead, up, (50, -1500)), near, (200, -1550))
    mix = g.n("ShaderNodeMixShader", (1100, -200), label="dew beads")
    g.link(fac, mix.inputs["Fac"]); g.link(shader, mix.inputs[1]); g.link(gl.outputs[0], mix.inputs[2])
    return mix.outputs[0]
