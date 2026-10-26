"""Blender mesh objects for the water fields: closed film sheet, string tubes, drop spheroids and generic (V, F)
meshes. Geometry only: velocities live in water.motion, materials in water.shading.
"""

# Compatibility imports; each implementation has one owner (GOV_04).
from materials.water.mesh_objects import _finish, _link, from_arrays  # noqa: F401
from materials.water.mesh_sheet import _grid_quads, _border_loop, film_sheet  # noqa: F401
from materials.water.mesh_tubes import _tube_rings, tubes  # noqa: F401
from materials.water.mesh_drops import _unit_sphere, spheroids  # noqa: F401
import bpy
import numpy as np


