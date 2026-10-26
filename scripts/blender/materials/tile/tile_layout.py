"""Compatibility facade for tile layout; each job has one owner."""
import numpy as np
from materials.tile.tile_nodes import _replace_group_users
from materials.tile.layout_config import _INPUTS, _JITTER_SEEDS, _VERSION
from materials.tile.layout_reference import _white_noise, _jitter_transform, reference
from materials.tile.layout_build import _interface_signature, layout_group
from materials.tile.layout_instance import add_layout
