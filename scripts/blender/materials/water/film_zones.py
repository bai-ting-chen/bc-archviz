"""Film zones; implementation for water.falling_film."""
import numpy as np
from materials.water import ballistic_sheet, seeded_noise


def zones(params, s, stretched_depth_m, stream):
    """Calm/busy multiplier in [zone_min, 1]: clustered patches 0.3-1 m, busier on thick streams (stream in [-1, 1])."""
    z = (.7 + .15 * seeded_noise.clustered_noise(s, params.seed + 1, .3, 1.)
         + .10 * seeded_noise.clustered_noise(stretched_depth_m, params.seed + 2, .3, 1.)
         + .05 * stream)
    return np.clip(z, params.zone_min, 1.)
