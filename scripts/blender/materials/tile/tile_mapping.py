"""Compatibility facade for tile mapping; each job has one owner."""
import math
import bpy
from mathutils import Vector
from materials.tile.tile_uv_mesh import _world_vertices, _write_uv, _face_vectors
from materials.tile.tile_uv_planar import planar_uv
from materials.tile.tile_uv_polar import _polar_angles, cylinder_uv, annulus_uv
from materials.tile.tile_uv_node import layout_vector
