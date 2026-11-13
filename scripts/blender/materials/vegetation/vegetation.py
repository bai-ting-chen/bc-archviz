"""Compatibility facade for vegetation; each job has one owner."""
import bpy
from materials.shared.node_graph import NodeGraph
from materials.shared.node_graph import active_socket
from materials.vegetation.blade_config import BLADE, WET
from materials.vegetation.blade_wet import _wet
from materials.vegetation.blade_build import blade_material
