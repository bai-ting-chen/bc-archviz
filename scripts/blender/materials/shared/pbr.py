"""Compatibility facade for pbr; each job has one owner."""
import os
import bpy
from materials.shared.nodes import G, sock
from materials.shared.pbr_config import BUMP_DISTANCE
from materials.shared.pbr_maps import _img, _ph_maps
from materials.shared.pbr_build import pbr_material
from materials.shared.dielectric import dielectric, glass_material
from materials.shared.principled import _principled_of, _principled
from materials.shared.simple import simple_material, white_backdrop
from materials.shared.material_spec import material_from_spec
from materials.shared.map_measure import solve_levels, map_mean
from materials.shared.albedo import albedo_material
