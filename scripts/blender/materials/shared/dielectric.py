"""Dielectric; canonical implementation behind pbr."""

import bpy

from effects.anisotropy import anisotropy as set_anisotropy

def dielectric(name, ior=1.52, tint=(1.0, 1.0, 1.0), roughness=0.0, label=None,
               *, anisotropy=None, rotation=0.0, tangent=None):
    """The one clear-dielectric builder (glass, water, glass-to-water interfaces): Principled,
    transmission 1. `tint` multiplies every crossing, so keep it within a few % of white."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.label = "%s (IOR %.3f)" % (name, ior) if label is None else label
    b.inputs["Base Color"].default_value = (*tint, 1)
    b.inputs["Roughness"].default_value = roughness
    b.inputs["IOR"].default_value = ior
    b.inputs["Transmission Weight"].default_value = 1.0
    if anisotropy is not None:
        set_anisotropy(b, anisotropy, rotation, tangent)
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    o.location = (300, 0)
    nt.links.new(b.outputs["BSDF"], o.inputs["Surface"])
    return mat
