"""Pool material; canonical implementation behind water."""

import bpy

from materials.shared.nodes import G, sock

def pool_water(name="POOL_WATER", tint=(0.45, 0.85, 0.72), density=1.0, ripple_scale=2.0,
               ripple_m=0.0015, ior=1.333):
    """Water as a closed volume: refractive surface (IOR 1.333) + Volume Absorption, so colour
    grows with path length (shallow steps stay clear, depth turns green). Absorption coefficient
    = density * (1 - tint) per metre. Gentle ripples as bump on the surface only."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = G(mat)
    g.frame("Surface", (0.20, 0.24, 0.30))
    g.frame("Body", (0.18, 0.28, 0.26))
    F_S, F_B = list(g.frames)
    geo = g.node("ShaderNodeNewGeometry", (-900, 0), F_S)
    nz = g.node("ShaderNodeTexNoise", (-700, 0), F_S, label="ripples", Scale=ripple_scale, Detail=4.0)
    g.link(geo.outputs["Position"], nz.inputs["Vector"])
    bump = g.node("ShaderNodeBump", (-500, 0), F_S, label="ripple height %.1f mm" % (ripple_m * 1000),
                  Distance=ripple_m, Strength=1.0)
    g.link(nz.outputs["Fac"], bump.inputs["Height"])
    b = g.node("ShaderNodeBsdfPrincipled", (-250, 0), F_S, label="water surface", IOR=ior, Roughness=0.0)
    b.inputs["Transmission Weight"].default_value = 1.0
    g.link(bump.outputs["Normal"], b.inputs["Normal"])
    va = g.node("ShaderNodeVolumeAbsorption", (-250, -300), F_B, label="depth tint", Density=density)
    va.inputs["Color"].default_value = (*tint, 1)
    out = g.node("ShaderNodeOutputMaterial", (100, 0))
    g.link(b.outputs["BSDF"], out.inputs["Surface"])
    g.link(va.outputs["Volume"], out.inputs["Volume"])
    return mat
