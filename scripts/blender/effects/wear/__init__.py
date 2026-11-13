"""Wear family assembly API; mechanism implementations live in the named modules."""
from effects.wear.cracks import CRACK, add_cracks  # noqa: F401
from effects.wear.chipping import add_edge_wear, dice, edge_wear_group, set_input  # noqa: F401
from effects.wear.mask_views import mask_material  # noqa: F401
from effects.wear.concrete_shading import weathered_concrete  # noqa: F401
from effects.wear.dirt import add_corner_dirt, edge_dirt_masks  # noqa: F401
from effects.wear.leak_field import add_leak_field, leak_field_group  # noqa: F401
from effects.wear.water_marks import LEAK, add_runoff  # noqa: F401
from effects.wear.edge_cracks import add_edge_cracks, edge_crack_edges  # noqa: F401
from effects.wear.wear_locations import round_shader, round_geometry, switch_rounding, set_round_radius  # noqa: F401

from effects.wear.wear import (WearLayer, WearExtent, HybridSource, MaskSource, StampSource,
                             LAYERS, wear_factor, apply_surface_wear, image_mask, grunge)
