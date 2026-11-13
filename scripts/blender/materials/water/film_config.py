"""Film config; implementation for water.falling_film."""
from dataclasses import dataclass
import numpy as np


@dataclass
class FilmParams:
    """Layer strengths and scales (metres unless noted); starting values from one courtyard-scale view."""
    # fall-time stretch (§3.3)
    stretch_exponent: float = .5          # exponent: 1 = physical, lower = less stretched
    stretch_reference_m: float = .15       # m top band left unstretched
    # fine ribbons (§3.4)
    ribbon_spacing_m: float = .036   # m between ribbon centres
    ribbon_wander_m: float = .025    # m sideways wander of each ribbon
    ribbon_width_variation: float = .40   # +- width fraction
    ribbon_twist_rad: float = 1.25     # rad
    ribbon_relief_strength: float = .40           # relief strength (aim slope p99 <~ 0.3 rad at full zone strength)
    zone_min: float = .40          # calm/busy zones span [zone_min, 1]
    swell_amplitude_m: float = .003            # m sinuous swell amplitude
    swell_thickness_variation: float = .40    # +- thickness fraction
    wave_amplitude_m: float = .0006           # m roll-wave arc height
    wavelength_m: float = .035         # m short train (the long train is 2.3x)
    wave_coverage_growth_per_m: float = .22   # extra arc cover per m of drop
    wave_amplitude_growth_per_m: float = 1.0         # extra arc amplitude per m of drop
    # meander and tears (§3.5-3.6)
    meander_amplitude_m: float = .014          # m sideways meander amplitude
    tear_start_m: float = None       # m below the lip; None = 0.38 x drop
    tear_threshold_fall_per_m_power: float = .30         # threshold fall per m^tear_power below tear_start
    tear_exponent: float = 1.4
    tear_stretch_threshold: float = 2.2      # tear where 1 + d(meander)/ds exceeds this
    min_slit_width_m: float = .010          # m slit width range across the flow
    max_slit_width_m: float = .035
    tear_taper_range: float = .10         # field units over which thickness tapers to 0
    rim_bead_m: float = .002              # m bead of swept water on torn edges
    # free side edges (§3.8)
    edge_retreat_coefficient: float = .06      # m x d^1.3 inward pull
    edge_band_m: float = .20         # m band of extra tearing beside each free edge
    edge_tear_strength: float = .8
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
    along_lip_m: np.ndarray           # along-lip coordinate
    drop_m: np.ndarray           # drop
    stretched_depth_m: np.ndarray           # stretched depth
    tear_start_m: float       # m below the lip
    folded_fraction: float           # share of water quads folded over by the meander
