"""Native wavefront caustics (Evan Wallace's mesh method) in Geometry Nodes, rendered by Cycles.

The refracting surface's mesh is the light wavefront: every vertex refracts the sun (Vector Math
Refract) and is raycast onto the receivers; every face carries the sun power that crossed it
(E_perp * T * face area * |n . sun|) and lands on a new area. Irradiance on the receiver =
power / landed area -> focused faces get bright, spread faces dim, energy is conserved.
A transparent emissive overlay at the landing points adds the reflected radiance
(albedo * E / pi) to the receivers in Cycles. No MNEE, no add-ons, no baking.
Simplifications: one refraction (exact for a pool), constant Fresnel T, sun disc treated as a
point direction (slightly too crisp), matte receivers only.
"""

# Compatibility imports; each implementation has one owner (GOV_04).
from effects.caustics.caustic_graph import caustic_sheet_group  # noqa: F401
from effects.caustics.caustic_shading import caustic_sheet_material  # noqa: F401
from effects.caustics.caustic_objects import add_caustic_sheet  # noqa: F401
import math

import bpy

from effects.edge_wear import _GN
from effects.edge_wear import _input
from materials.shared.nodes import G
from materials.shared.nodes import sock


