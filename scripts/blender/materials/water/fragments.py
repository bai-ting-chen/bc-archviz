"""Strings and drops of a torn falling film (references/materials/water/water-free-falling-film.md §3.7).

A gap is never empty: hanging strings and falling drops fill torn cells (densities per m^2 of torn area, so they
scale with the curtain), and drops/ligaments shed from torn edges (per metre of lip, more lower down).
Drops are arrays (N, 5) = x, y, z, diameter, stretch along the fall; strings are (M, 4) = x, y, z, radius.
water.mesh turns both into objects.
"""

# Compatibility imports; each implementation has one owner (GOV_04).
from materials.water.fragment_config import FragmentParams  # noqa: F401
from materials.water.fragment_cells import _mid_surface, _torn_cells  # noqa: F401
from materials.water.fragment_edges import edge_drops  # noqa: F401
from materials.water.fragment_gaps import _string, gap_fill  # noqa: F401
from dataclasses import dataclass

import numpy as np


