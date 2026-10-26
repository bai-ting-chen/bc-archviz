"""Procedural edge wear (dirty edges, shading only) and edge chips (real geometry).

This module is the one import point; each job lives in its own module (RULES GOV_04):
    edge_chips    dice, the Geometry Nodes chip modifier (edge_wear_group, add_edge_wear, set_input)
    edge_shading  weathered_concrete: dirty edges and fresh breaks
    edge_masks    mask_material: one edge-detection method as an emission view
    leak_field    leak_field_group, add_leak_field (runs first on the object)
    runoff        add_runoff: streaks, grunge and soil splash
    cracks        add_cracks: shrinkage and map cracks
    wear_nodes    shared node shorthands
"""
from effects.cracks import CRACK, add_cracks  # noqa: F401
from effects.edge_chips import add_edge_wear, dice, edge_wear_group, input_socket as _input, set_input  # noqa: F401
from effects.edge_masks import mask_material  # noqa: F401
from effects.edge_shading import weathered_concrete  # noqa: F401
from effects.leak_field import add_leak_field, leak_field_group  # noqa: F401
from materials.shared.nodes import G as _G  # noqa: F401
from effects.runoff import LEAK, add_runoff  # noqa: F401
from effects.wear_nodes import attr as _attr  # noqa: F401
from effects.wear_nodes import math_ as _math  # noqa: F401
from effects.wear_nodes import noise as _noise  # noqa: F401
from effects.wear_nodes import range_ as _range  # noqa: F401


def _GN(ng):
    """Kept for existing scripts: materials.shared.nodes.G on a node group."""
    return _G(ng, clear=False)
