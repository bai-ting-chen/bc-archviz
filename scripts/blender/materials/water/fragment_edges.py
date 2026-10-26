"""Fragment edges; implementation for water.fragments."""
import numpy as np
from materials.water.fragment_cells import _mid_surface


def edge_drops(ff, lip, p, s, d):
    """Drops and ligaments shed at torn edges, weighted toward the foot: array (N, 5)."""
    rng = np.random.default_rng(p.seed)
    near_edge = (np.abs(ff.gap) < .04) & (ff.D > ff.tear_start + .2)
    idx = np.flatnonzero(near_edge.ravel())
    count = min(int(p.edge_drops_per_m * lip.length), len(idx))
    if count == 0:
        return np.zeros((0, 5))
    weight = ff.D.ravel()[idx] - ff.tear_start
    pick = rng.choice(idx, size=count, replace=False, p=weight / weight.sum())
    centre = (_mid_surface(ff).reshape(-1, 3)[pick]
              + ff.normal.reshape(-1, 3)[pick] * rng.uniform(-.004, .03, (count, 1))
              + lip.along * rng.normal(0, .008, (count, 1)))
    centre[:, 2] -= rng.uniform(0, .05, count)
    diameter = np.clip(rng.lognormal(np.log(p.edge_drop_d), .4, count), .0015, p.edge_drop_max)
    is_ligament = rng.random(count) < p.ligament_share
    stretch = np.where(is_ligament, rng.uniform(4, 9, count), rng.uniform(1.4, 3.0, count))
    return np.c_[centre, diameter, stretch]
