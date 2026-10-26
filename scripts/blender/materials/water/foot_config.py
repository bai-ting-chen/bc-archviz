"""Foot config; implementation for water.foot."""
from dataclasses import dataclass
import numpy as np


EMPTY_MESH = (np.zeros((0, 3)), [])


@dataclass
class FootParams:
    """Impact spacing, crowns, foam, floating bubbles and splash (starting values; size from the shot)."""
    impact_spacing: float = .02     # m of landing line per stream impact
    crowns: float = .35             # share of impacts (the strongest) with a standing crown
    foam_per_m: float = 350.        # per m of landing line
    foam_size: float = .010         # m median (flecks under ~1 px at the final view vanish)
    foam_max: float = .04
    foam_focus: float = .4          # parent weight = strength ** focus
    foam_reach: float = .18         # m mean distance travelled from the impact
    foam_spread: float = .03        # m sideways scatter at the impact
    drift: float = .5               # extra sideways scatter per m travelled (carries past both ends)
    bubbles_per_m: float = 600.
    bubble_d: float = .006          # m median diameter
    bubble_reach: float = .5        # m mean distance travelled (+5 cm)
    raft_share: float = .15         # share of bubble spawns that are rafts of 3-11
    splash_per_m: float = 40.
    max_out: float = 1.5            # m from the wall; nothing placed beyond (keeps it on the pool)
    seed: int = 2300
