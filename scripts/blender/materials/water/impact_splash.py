"""Foot splash; implementation for water.pool_impacts."""
import numpy as np
from materials.water.impact_drift import _span


def splash(lip, impact_points, strength, pool_height_m, params):
    """Splash drops thrown up and out from the strongest impacts: array (N, 5) = x, y, z, diameter, stretch."""
    rng = np.random.default_rng(params.seed + 4)
    count = int(_span(lip, impact_points) * params.splash_per_m)
    if count == 0:
        return np.zeros((0, 5))
    weight = strength ** 2
    idx = rng.choice(len(impact_points), size=count, p=weight / weight.sum())
    s, o = lip.local(impact_points[idx])
    o = o + rng.uniform(0, .12, count)
    s = s + rng.normal(0, .04, count)
    centre = lip.world(s, o, pool_height_m + rng.exponential(.03, count))
    diameter = np.clip(rng.lognormal(np.log(.0022), .4, count), .001, .005)
    return np.c_[centre, diameter, rng.uniform(1, 1.8, count)]
