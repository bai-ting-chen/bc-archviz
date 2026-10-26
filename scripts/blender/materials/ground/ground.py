"""Compatibility facade for ground; each job has one owner."""
import bpy
from materials.shared.nodes import G, sock
from materials.shared.pbr import _ph_maps
from scene.environment.terrain import BARE, BARE_W, _noise4
from materials.ground.gravel import displaced_ground
from materials.ground.meadow_ground import ground_material
