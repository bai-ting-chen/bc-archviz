"""Compatibility facade for pbr; each job has one owner."""
import os
import bpy
from materials.shared.node_graph import NodeGraph, active_socket
from materials.shared.pbr_config import BUMP_DISTANCE_M
from materials.shared.pbr_maps import _img, _ph_maps
from materials.shared.pbr_build import pbr_material
from materials.shared.dielectric import dielectric
from materials.shared.principled import _principled_of, _principled
from materials.shared.flat_color_materials import flat_color_material, white_backdrop
from materials.shared.material_specification import material_from_spec
from materials.shared.map_measurements import solve_levels, map_mean_linear_rgb
from materials.shared.albedo import albedo_material
