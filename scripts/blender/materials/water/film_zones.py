"""Film zones; implementation for water.falling_film."""
import numpy as np
from materials.water import ballistic_sheet, seeded_noise


def zones(p, s, v, stream):
    """Calm/busy multiplier in [zone_min, 1]: clustered patches 0.3-1 m, busier on thick streams (stream in [-1, 1])."""
    z = (.7 + .15 * seeded_noise.clustered_noise(s, p.seed + 1, .3, 1.)
         + .10 * seeded_noise.clustered_noise(v, p.seed + 2, .3, 1.)
         + .05 * stream)
    return np.clip(z, p.zone_min, 1.)
