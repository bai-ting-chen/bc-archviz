"""Independent tile layout, glazed face, rounded shoulder and grout shading.

This module is the one import point; each job lives in its own module (RULES GOV_04):
    tile_build         tile_material: assemble one tile node tree from its parts
    tile_settings      read settings back, set_param (structural rebuilds)
    tile_displacement  bump / full / damage-only displacement
    tile_finish        finish group, feature switches (toggle)
    tile_albedo        colour, tint, dust, macro variation
    tile_specks        iron specks and pinholes
    tile_relief        height: shoulders, tilt, wave, lippage
    tile_bsdf          coated face and grout shading
    tile_maps          face image maps: find, measure, physical size
    tile_config        feature names, parameter groups, validation
    tile_glazed        procedural glazed pool tiles (separate, flat material)
"""
from materials.tile.tile_build import tile_material  # noqa: F401
from materials.tile.tile_config import FEATURES  # noqa: F401
from materials.tile.tile_displacement import use_bump, use_damage_displacement, use_displacement  # noqa: F401
from materials.tile.tile_finish import toggle  # noqa: F401
from materials.tile.tile_glazed import glazed_tiles  # noqa: F401
from materials.tile.tile_settings import read_settings as _settings  # noqa: F401
from materials.tile.tile_settings import set_param  # noqa: F401
