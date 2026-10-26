"""Simple; canonical implementation behind pbr."""

import bpy

from materials.shared.nodes import G, sock

from materials.shared.principled import _principled_of

def simple_material(name, color, roughness=0.5, metallic=0.0):
    """Principled with a flat colour, roughness and metallic -- placeholders and controls."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    b = _principled_of(mat)
    b.inputs["Base Color"].default_value = (*color, 1.0)
    b.inputs["Roughness"].default_value = roughness
    b.inputs["Metallic"].default_value = metallic
    return mat

def white_backdrop(name="WHITE_BACKDROP", albedo=0.85):
    """Matte white backdrop of a measured albedo (product/studio shots)."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = G(mat)
    b = g.node("ShaderNodeBsdfPrincipled", (-300, 0), Roughness=0.9)
    b.inputs["Base Color"].default_value = (albedo, albedo, albedo, 1)
    out = g.node("ShaderNodeOutputMaterial", (0, 0))
    g.link(b.outputs["BSDF"], out.inputs["Surface"])
    return mat
