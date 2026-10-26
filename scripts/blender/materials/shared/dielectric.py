"""Dielectric; canonical implementation behind pbr."""

import bpy

from materials.shared.principled import _principled_of

def dielectric(name, ior=1.52, tint=(1.0, 1.0, 1.0), roughness=0.0, label=None):
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
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    o.location = (300, 0)
    nt.links.new(b.outputs["BSDF"], o.inputs["Surface"])
    return mat

def glass_material(name="Glass_Clear", tint=(0.92, 0.96, 0.97), roughness=0.0):
    """Clear glass (IOR 1.52); the default tint is slightly green, for thick panes. An existing
    material is edited in place (nodes the user added stay); a new one is built by dielectric."""
    mat = bpy.data.materials.get(name)
    if mat is None:
        return dielectric(name, 1.52, tint, roughness, label="")
    b = _principled_of(mat)
    b.inputs["Base Color"].default_value = (*tint, 1.0)
    b.inputs["Roughness"].default_value = roughness
    b.inputs["IOR"].default_value = 1.52
    b.inputs["Transmission Weight"].default_value = 1.0
    return mat
