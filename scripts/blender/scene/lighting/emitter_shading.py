"""Emitter shading; implementation for interior."""
import math
import bpy
from core.archviz import LM_PER_W
from materials.shared.nodes import G


def lens_luminance(lumens, area_m2):
    """Luminance of a Lambertian lens of area A emitting `lumens` into its half-space: L = F / (pi A)."""
    return lumens / (math.pi * area_m2)


def lit_once(objs):
    """Decorative lenses whose flux is carried by an analytic light: keep them visible to the camera
    and in reflections, but out of diffuse AND transmission paths -- a diffuse bounce that then
    passes through water continues as a transmission ray and would see the lens again."""
    for o in objs:
        o.visible_diffuse = False
        o.visible_transmission = False


def emitter(name, luminance_cd, kelvin=3000, color=None):
    """Visible light source surface (LED lens, lit panel) with a luminance in cd/m2.
    Cycles emission strength S is radiance in W/m2/sr, so S = L / 683."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = G(mat)
    em = g.node("ShaderNodeEmission", (-200, 0), label="%d cd/m2" % luminance_cd,
                Strength=luminance_cd / LM_PER_W)
    if color:
        em.inputs["Color"].default_value = (*color, 1)
    else:
        bb = g.node("ShaderNodeBlackbody", (-400, 0), label="%d K" % kelvin, Temperature=kelvin)
        g.link(bb.outputs["Color"], em.inputs["Color"])
    out = g.node("ShaderNodeOutputMaterial", (0, 0))
    g.link(em.outputs["Emission"], out.inputs["Surface"])
    return mat


def emitter_dots(name, luminance_cd, n=4, radius=0.22, kelvin=3000, housing=(0.02, 0.02, 0.02)):
    """Multi-head downlight face: n round LED lenses along the object's long (generated X) axis,
    black housing around them. Generated coords span 0..1 over the box."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = G(mat)
    tc = g.node("ShaderNodeTexCoord", (-1100, 0))
    sep = g.node("ShaderNodeSeparateXYZ", (-900, 0))
    g.link(tc.outputs["Generated"], sep.inputs["Vector"])
    cell = g.node("ShaderNodeMath", (-700, 100), label="cell x")
    cell.operation, cell.inputs[1].default_value = "MULTIPLY", float(n)
    g.link(sep.outputs["X"], cell.inputs[0])
    fr = g.node("ShaderNodeMath", (-550, 100))
    fr.operation = "FRACT"
    g.link(cell.outputs[0], fr.inputs[0])
    comb = g.node("ShaderNodeCombineXYZ", (-400, 0))
    g.link(fr.outputs[0], comb.inputs["X"])
    g.link(sep.outputs["Y"], comb.inputs["Y"])
    d = g.node("ShaderNodeVectorMath", (-250, 0), label="distance to lens centre")
    d.operation = "DISTANCE"
    d.inputs[1].default_value = (0.5, 0.5, 0.0)
    g.link(comb.outputs["Vector"], d.inputs[0])
    m = g.node("ShaderNodeMath", (-100, 0), label="lens mask")
    m.operation, m.inputs[1].default_value = "LESS_THAN", radius
    g.link(d.outputs["Value"], m.inputs[0])
    em = g.node("ShaderNodeEmission", (50, 150), label="%d cd/m2" % luminance_cd, Strength=luminance_cd / LM_PER_W)
    bb = g.node("ShaderNodeBlackbody", (-100, 250), Temperature=kelvin)
    g.link(bb.outputs["Color"], em.inputs["Color"])
    hb = g.node("ShaderNodeBsdfPrincipled", (50, -200), label="housing", Roughness=0.4)
    hb.inputs["Base Color"].default_value = (*housing, 1)
    mix = g.node("ShaderNodeMixShader", (300, 0))
    g.link(m.outputs[0], mix.inputs["Fac"])
    g.link(hb.outputs["BSDF"], mix.inputs[1])
    g.link(em.outputs["Emission"], mix.inputs[2])
    out = g.node("ShaderNodeOutputMaterial", (500, 0))
    g.link(mix.outputs["Shader"], out.inputs["Surface"])
    return mat
