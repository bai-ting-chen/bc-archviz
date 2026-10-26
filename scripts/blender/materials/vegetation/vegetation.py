"""Compatibility facade for vegetation; each job has one owner."""
import bpy
from materials.shared.nodes import G
from materials.shared.nodes import sock
from materials.vegetation.blade_config import BLADE, DEW_BROAD, DEW_GRASS, WET
from materials.vegetation.blade_wet import _wet
from materials.vegetation.blade_dew import _dew
from materials.vegetation.blade_build import blade_material
