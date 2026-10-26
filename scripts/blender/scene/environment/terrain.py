"""Topography around a building pad, and the ground under a meadow (run in Blender).

    import scene.environment.terrain as terrain
    topo = terrain.landform_group(centre=(25, 25), pad_half=(3.5, 4), fall=6, run=40)
    ter = terrain.add_terrain(topo, materials.ground.ground.ground_material("grass_ground", "forest_ground_05"))
    terrain.height(x, y, centre=..., pad_half=..., fall=..., run=...)   # no-noise twin (camera placing)

Landform grading (references/materials/index.md › Terrain): a flat pad just under the slab, an apron, then a fall
of `fall` m over `run` m as a smoothstep in the noise-warped distance from the pad - a rounded
crest *and* a rounded toe, contours that wander instead of a cone - plus a broad roll beyond and
pasture hummocks. Steepest slope = 1.5 * fall / run (keep < 0.25 = 4:1 for a gentle, mowable
hill). The group stores `pad_d` (signed plan distance to the pad, m) for scatter masks.
"""

# Compatibility imports; each implementation has one owner (GOV_04).
from scene.environment.terrain_graph import BARE_W, BARE, _sock, _noise4, _centred, pad_distance, landform_group  # noqa: F401
from scene.environment.terrain_height import height  # noqa: F401
from scene.environment.terrain_objects import add_terrain  # noqa: F401
import math

import bpy

from materials.shared.nodes import G
from materials.shared.nodes import sock


