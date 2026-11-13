"""Compatibility facade for stone; each job has one owner."""
import bpy
from materials.shared.node_graph import NodeGraph, active_socket
from materials.shared.pbr import _principled, albedo_material
from materials.stone.granite import polished_granite
from materials.stone.stone_tiles import stone_tiles
from materials.stone.pavers import long_pavers
