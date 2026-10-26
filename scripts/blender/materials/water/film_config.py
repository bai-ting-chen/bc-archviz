"""Film config; implementation for water.film."""
from dataclasses import dataclass
import numpy as np


@dataclass
class FilmParams:
    """Layer strengths and scales (metres unless noted); starting values from one courtyard-scale view."""
    # fall-time stretch (§3.3)
    stretch_k: float = .5          # exponent: 1 = physical, lower = less stretched
    stretch_ref: float = .15       # m top band left unstretched
    # fine ribbons (§3.4)
    ribbon_spacing: float = .036   # m between ribbon centres
    ribbon_wander: float = .025    # m sideways wander of each ribbon
    ribbon_varicose: float = .40   # +- width fraction
    ribbon_twist: float = 1.25     # rad
    ribbons: float = .40           # relief strength (aim slope p99 <~ 0.3 rad at full zone strength)
    zone_min: float = .40          # calm/busy zones span [zone_min, 1]
    swell: float = .003            # m sinuous swell amplitude
    swell_varicose: float = .40    # +- thickness fraction
    waves: float = .0006           # m roll-wave arc height
    wave_len: float = .035         # m short train (the long train is 2.3x)
    wave_cover_rate: float = .22   # extra arc cover per m of drop
    wave_grow: float = 1.0         # extra arc amplitude per m of drop
    # meander and tears (§3.5-3.6)
    meander: float = .014          # m sideways meander amplitude
    tear_start: float = None       # m below the lip; None = 0.38 x drop
    tear_rate: float = .30         # threshold fall per m^tear_power below tear_start
    tear_power: float = 1.4
    tear_stretch: float = 2.2      # tear where 1 + d(meander)/ds exceeds this
    slit_lo: float = .010          # m slit width range across the flow
    slit_hi: float = .035
    tear_edge: float = .10         # field units over which thickness tapers to 0
    rim: float = .002              # m bead of swept water on torn edges
    # free side edges (§3.8)
    edge_retreat: float = .06      # m x d^1.3 inward pull
    edge_band: float = .20         # m band of extra tearing beside each free edge
    edge_tear: float = .8
    free_edges: tuple = (True, True)   # (s = 0 end, s = length end); False where the sheet meets a wall
    seed: int = 2100


@dataclass
class FilmFields:
    """Result of film_surfaces: grids are (nd, ns) or (nd, ns, 3), rows = drop."""
    front: np.ndarray       # world points of the front skin
    back: np.ndarray        # world points of the back skin
    keep: np.ndarray        # True where there is water
    gap: np.ndarray         # tear field: > 0 water, < 0 torn
    normal: np.ndarray      # carrier normals, away from the wall
    S: np.ndarray           # along-lip coordinate
    D: np.ndarray           # drop
    V: np.ndarray           # stretched depth
    tear_start: float       # m below the lip
    folded: float           # share of water quads folded over by the meander
