"""Glass of water built for correct refraction in Cycles (no nested-IOR priority there).

Three interfaces, each its own surface, normals defining which medium is in front:
  GLASS      air  -> glass   IOR 1.52    outer wall, rounded rim, inner wall ABOVE the water
  INTERFACE  water | glass   IOR 1.52/1.33 = 1.143 (front = water side, back = glass side)
                             inner wall BELOW the water + curved inner floor
  WATER_TOP  air  -> water   IOR 1.33    free surface with a capillary meniscus
GLASS + INTERFACE enclose the glass solid; INTERFACE + WATER_TOP enclose the water.
"""

# Compatibility imports; each implementation has one owner (GOV_03).
from materials.glass.tumbler_profiles import tumbler_profiles  # noqa: F401
from materials.glass.lathe_geometry import lathe  # noqa: F401
from materials.glass.glass_assembly import glass_of_water, glass_of_water_mnee  # noqa: F401
