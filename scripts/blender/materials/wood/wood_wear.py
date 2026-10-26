"""Compatibility facade for wood wear; each job has one owner."""
from materials.shared import nodes as _mat_nodes
from materials.wood import wood as _mat_wood
import math
import bmesh
import bpy
from materials.shared.nodes import sock
from effects.edge_wear import _GN
from effects.edge_wear import _input
from effects.edge_wear import _attr
from effects.edge_wear import _noise
from effects.edge_wear import _range
from effects.edge_wear import _math
from effects.edge_chips import edge_field as _edge_field
from effects.edge_chips import chip_field as _chip_field
from effects.edge_chips import rejoin as _rejoin
from materials.wood.wood_arrises import round_arrises
from materials.wood.wood_uv import grain_uv
from materials.wood.wood_damage import wood_wear_group
from materials.wood.wood_shading import weathered_wood
