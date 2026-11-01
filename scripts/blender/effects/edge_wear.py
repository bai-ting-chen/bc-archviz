"""Procedural edge wear (dirty edges, shading only) and edge chips (real geometry).

This module is the one import point; each job lives in its own module (RULES GOV_04):
    edge_chips    dice, the Geometry Nodes chip modifier (edge_wear_group, add_edge_wear, set_input)
    edge_shading  weathered_concrete: dirty edges and fresh breaks
    edge_masks    mask_material: one edge-detection method as an emission view
    leak_field    leak_field_group, add_leak_field (runs first on the object)
    runoff        add_runoff: streaks, grunge and soil splash
    cracks        add_cracks: shrinkage and map cracks
    edge_cracks   add_edge_cracks: short cracks from clean outside edges
    round_edges   shared scene-radius shader or real-geometry rounding
    edge_dirt     shared independently switchable edge line and dust
    wear_nodes    shared node shorthands
"""
from effects.cracks import CRACK, add_cracks  # noqa: F401
from effects.edge_chips import add_edge_wear, dice, edge_wear_group, set_input  # noqa: F401
from effects.edge_masks import mask_material  # noqa: F401
from effects.edge_shading import weathered_concrete  # noqa: F401
from effects.edge_dirt import add_corner_dirt, edge_dirt_masks  # noqa: F401
from effects.leak_field import add_leak_field, leak_field_group  # noqa: F401
from effects.runoff import LEAK, add_runoff  # noqa: F401
from effects.edge_cracks import add_edge_cracks, edge_crack_edges  # noqa: F401
from effects.round_edges import round_shader, round_geometry, switch_rounding, set_round_radius  # noqa: F401
