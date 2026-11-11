"""Clear glass; canonical implementation behind glass."""

import bpy

from materials.shared.dielectric import dielectric
from materials.shared.principled import _principled_of


def clear_glass(name="GLASS", tint=(1.0, 1.0, 1.0), roughness=0.0, ior=1.52):
    """Build or edit clear glass in place; use tint for coloured glass and preserve added nodes."""
    mat = bpy.data.materials.get(name)
    if mat is None:
        return dielectric(name, ior, tint, roughness, label="")
    b = _principled_of(mat)
    b.inputs["Base Color"].default_value = (*tint, 1.0)
    b.inputs["Roughness"].default_value = roughness
    b.inputs["IOR"].default_value = ior
    b.inputs["Transmission Weight"].default_value = 1.0
    return mat
