"""Foot impacts; implementation for water.pool_impacts."""
import numpy as np


def impacts(lip, landing_midpoints, landing_mask, landing_thickness_m, drops, pool_height_m, params):
    """Impact points (N, 3) on the pool surface and strengths (N,), from the film's bottom row and falling drops."""
    rng = np.random.default_rng(params.seed)
    thick = landing_thickness_m * landing_mask
    s_row, o_row = lip.local(landing_midpoints)
    span = float(abs(s_row[-1] - s_row[0])) or lip.length_m
    count = max(1, int(span / params.impact_spacing_m))
    if thick.sum() > 0:                                   # sheet landings (none when the bottom row is fully torn)
        idx = rng.choice(len(landing_midpoints), size=count, p=thick / thick.sum())
        s = s_row[idx] + rng.normal(0, .006, count)
        o = o_row[idx] + rng.normal(0, .012, count)
        strength = np.clip(thick[idx] / np.percentile(thick[landing_mask], 90), .15, 1.5)
    else:
        s = o = strength = np.zeros(0)
    if drops is not None and len(drops):                  # drops falling through the gaps land too, weaker
        low = drops[drops[:, 2] < pool_height_m + .6]
        if len(low):
            pick = rng.choice(len(low), size=min(len(low), count), replace=False)
            s_drop, o_drop = lip.local(low[pick, :3])
            o_drop = o_drop + rng.uniform(0, .03, len(pick))
            s = np.r_[s, s_drop]
            o = np.r_[o, o_drop]
            strength = np.r_[strength, rng.uniform(.05, .3, len(pick))]
    if not len(s):
        return np.zeros((0, 3)), np.zeros(0)
    return lip.world(s, o, np.full_like(s, pool_height_m)), strength
