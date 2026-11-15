"""Visible emitter luminance and ray visibility.

See references/scene/lighting/artificial-light.md.
"""
import math
import bpy
from core.archviz import LM_PER_W
from materials.shared.node_graph import NodeGraph


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
    g = NodeGraph(mat)
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
