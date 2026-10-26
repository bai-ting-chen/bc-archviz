"""Volumes material helpers; canonical implementations."""
import bpy
from materials.shared.nodes import G
from materials.stone.stone import _ramp


def steam(name="STEAM", density=0.6, z0=0.4, height=0.9, scale=3.0):
    """Wisps over a hot tub: Principled Volume, density = noise ramp x fade with height above z0."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = G(mat)
    geo = g.node("ShaderNodeNewGeometry", (-1100, 0))
    stretch = g.node("ShaderNodeVectorMath", (-900, 0))
    stretch.operation = "MULTIPLY"
    stretch.inputs[1].default_value = (1.0, 1.0, 0.45)              # wisps elongate upward
    g.link(geo.outputs["Position"], stretch.inputs[0])
    nz = g.node("ShaderNodeTexNoise", (-700, 0), label="wisps", Scale=scale, Detail=6.0, Roughness=0.6)
    g.link(stretch.outputs["Vector"], nz.inputs["Vector"])
    cr = _ramp(g, (-500, 0), None, [(0.52, (0, 0, 0)), (0.72, (1, 1, 1))], "wisp threshold")
    g.link(nz.outputs["Fac"], cr.inputs["Fac"])
    sep = g.node("ShaderNodeSeparateXYZ", (-700, -300))
    g.link(geo.outputs["Position"], sep.inputs["Vector"])
    fade = g.node("ShaderNodeMapRange", (-500, -300), label="fade with height")
    fade.inputs["From Min"].default_value, fade.inputs["From Max"].default_value = z0, z0 + height
    fade.inputs["To Min"].default_value, fade.inputs["To Max"].default_value = 1.0, 0.0
    g.link(sep.outputs["Z"], fade.inputs["Value"])
    mul = g.node("ShaderNodeMath", (-300, -100))
    mul.operation = "MULTIPLY"
    g.link(cr.outputs["Color"], mul.inputs[0])
    g.link(fade.outputs["Result"], mul.inputs[1])
    dens = g.node("ShaderNodeMath", (-150, -100), label="density %.2f" % density)
    dens.operation = "MULTIPLY"
    dens.inputs[1].default_value = density
    g.link(mul.outputs[0], dens.inputs[0])
    pv = g.node("ShaderNodeVolumePrincipled", (50, 0), label="steam", Anisotropy=0.5)
    pv.inputs["Color"].default_value = (0.95, 0.95, 0.95, 1)
    g.link(dens.outputs[0], pv.inputs["Density"])
    out = g.node("ShaderNodeOutputMaterial", (300, 0))
    g.link(pv.outputs["Volume"], out.inputs["Volume"])
    return mat
