"""Compatibility facade for tile damage; each job has one owner."""
import math
import bpy
from materials.tile.tile_nodes import _TileGraph
from materials.tile.tile_nodes import _socket
from materials.tile.tile_nodes import _replace_group_users
from materials.tile.damage_contract import DAMAGE_DEFAULT_VALUES, DAMAGE_INPUT_SOCKETS, PIECE_BINS, _LAYOUT_INPUTS, _OUTPUTS, _REVISION, _VERSION
from materials.tile.damage_graph import _DamageGraph
from materials.tile.damage_fields import _rand, _voronoi, _warp, _piece_fields, _fine_fields
from materials.tile.damage_layers import _layers
from materials.tile.damage_build import _is_current, damage_group
from materials.tile.damage_shading import damage_shaders
