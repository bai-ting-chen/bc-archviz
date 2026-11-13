"""Compatibility facade for water; each job has one owner."""
import math
import bpy
from materials.shared.node_graph import NodeGraph, active_socket
from materials.water.pool_material import pool_water
from materials.water.water_normals import smooth_flat
from materials.water.water_mesh import water_surface
