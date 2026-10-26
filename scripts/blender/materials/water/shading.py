"""Materials and images for the water geometry (references/materials/water/water-ripple.md §4.2, water-splash.md §4.2).

- thin_wall_copy: water for open shells (crowns, bubbles): glints and rims, straight transmission.
- save_height_exr / install_bump / readback_mm: a ripple height field as a bump on the pool's own material.
  The height goes to a float EXR in millimetres and is loaded from that file (a generated image is lost on reload);
  world positions map to the field through the lip's axes, so any wall orientation works.
"""

# Compatibility imports; each implementation has one owner (GOV_04).
from materials.water.thin_wall import thin_wall_copy  # noqa: F401
from materials.water.height_image import save_height_exr, readback_mm  # noqa: F401
from materials.water.ripple_bump import install_bump  # noqa: F401
import bpy
import numpy as np


