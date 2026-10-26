"""Geometry Nodes scatter for small instances: leaf litter, climbers, shrub foliage (run in Blender).

    group = scatter_group()
    leaf = leaf_proto("PROTO_DRY_LEAF", 0.07, 0.045, 0.012, material)
    scatter(objs, leaf, density=0.35, z_max=0.5, seed=3, patch=0.42)

Points are distributed on each target's faces where Z < `z_max` AND a 0.6/m noise > `patch`
(0 = everywhere), then instanced with random rotation and 0.6-1.3 x `scale`. The patch threshold
is sensitive near 0.5: on one wall 0.42 blanketed it, 0.48 gave patches, 0.53 left nothing.
Inputs are set through effects.edge_wear.set_input (Blender 5.2: mod["id"] = v raises).

Meadow / grass on terrain (references/materials/vegetation/vegetation.md):
    sos = load_scatter_on_surface()                   # Blender's own essentials group
    grp = meadow_layer_group(sos)
    tx, ty = frustum_tangents(cam, (w, h))
    meadow_layer("MEADOW_01", grp, terrain, grass_collection, cam, Density=220, Tan_X=tx, Tan_Y=ty)
One object per species; masks: species patches (noise), shared bare-soil noise (terrain.BARE_W),
clearance from the pad (`pad_d` from terrain.landform_group), camera frustum + distance. Grass
stays upright (Align Rotation off) and picks random variants of the collection.
"""

# Compatibility imports; each implementation has one owner (GOV_04).
from scene.environment.scatter_graph import scatter_group  # noqa: F401
from scene.environment.leaf_geometry import leaf_proto  # noqa: F401
from scene.environment.scatter_objects import scatter  # noqa: F401
from scene.environment.scatter_asset import load_scatter_on_surface  # noqa: F401
from scene.environment.meadow_graph import meadow_layer_group  # noqa: F401
from scene.environment.meadow_objects import frustum_tangents, meadow_layer  # noqa: F401
import math
import os

import bpy

from effects.edge_wear import set_input


# --- meadow --------------------------------------------------------------------------------


