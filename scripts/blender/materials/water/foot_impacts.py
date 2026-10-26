"""Foot impacts; implementation for water.foot."""
import numpy as np


def impacts(lip, land_mid, land_keep, land_thick, drops, pool_z, p):
    """Impact points (N, 3) on the pool surface and strengths (N,), from the film's bottom row and falling drops."""
    rng = np.random.default_rng(p.seed)
    thick = land_thick * land_keep
    s_row, o_row = lip.local(land_mid)
    span = float(abs(s_row[-1] - s_row[0])) or lip.length
    count = max(1, int(span / p.impact_spacing))
    if thick.sum() > 0:                                   # sheet landings (none when the bottom row is fully torn)
        idx = rng.choice(len(land_mid), size=count, p=thick / thick.sum())
        s = s_row[idx] + rng.normal(0, .006, count)
        o = o_row[idx] + rng.normal(0, .012, count)
        strength = np.clip(thick[idx] / np.percentile(thick[land_keep], 90), .15, 1.5)
    else:
        s = o = strength = np.zeros(0)
    if drops is not None and len(drops):                  # drops falling through the gaps land too, weaker
        low = drops[drops[:, 2] < pool_z + .6]
        if len(low):
            pick = rng.choice(len(low), size=min(len(low), count), replace=False)
            s_drop, o_drop = lip.local(low[pick, :3])
            o_drop = o_drop + rng.uniform(0, .03, len(pick))
            s = np.r_[s, s_drop]
            o = np.r_[o, o_drop]
            strength = np.r_[strength, rng.uniform(.05, .3, len(pick))]
    if not len(s):
        return np.zeros((0, 3)), np.zeros(0)
    return lip.world(s, o, np.full_like(s, pool_z)), strength
