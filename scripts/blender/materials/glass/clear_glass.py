"""Clear glass; canonical implementation behind glass."""

from materials.shared.dielectric import dielectric
from materials.shared.principled import _principled

def clear_glass(name="GLASS", ior=1.52):
    """Soda-lime glass via materials.shared.pbr.dielectric (white, IOR 1.52 by default)."""
    return dielectric(name, ior, label="Soda-lime glass")
