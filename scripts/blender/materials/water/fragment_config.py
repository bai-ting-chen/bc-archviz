"""Fragment config; implementation for water.fragments."""
from dataclasses import dataclass


@dataclass
class FragmentParams:
    """Densities and sizes of gap strings, gap drops and edge drops (starting values; size from the shot)."""
    edge_drops_per_m: float = 570.     # per m of lip
    edge_drop_d: float = .0035         # m median diameter
    edge_drop_max: float = .008
    ligament_share: float = .30        # share of edge drops that are stretched ligaments
    gap_strings_per_m2: float = 900.   # per m^2 of torn area
    gap_drops_per_m2: float = 5000.
    string_len: float = .09            # m median length (lognormal sigma 0.6, clipped 0.02-0.40)
    seed: int = 2200
