"""Fragment edges; implementation for water.film_fragments."""
import numpy as np
from materials.water.fragment_cells import _mid_surface


def edge_drops(film_fields, lip, params, s, d):
    """Drops and ligaments shed at torn edges, weighted toward the foot: array (N, 5)."""
    rng = np.random.default_rng(params.seed)
    near_edge = (np.abs(film_fields.gap) < .04) & (film_fields.drop_m > film_fields.tear_start_m + .2)
    idx = np.flatnonzero(near_edge.ravel())
    count = min(int(params.edge_drops_per_m * lip.length_m), len(idx))
    if count == 0:
        return np.zeros((0, 5))
    weight = film_fields.drop_m.ravel()[idx] - film_fields.tear_start_m
    pick = rng.choice(idx, size=count, replace=False, p=weight / weight.sum())
    centre = (_mid_surface(film_fields).reshape(-1, 3)[pick]
              + film_fields.normal.reshape(-1, 3)[pick] * rng.uniform(-.004, .03, (count, 1))
              + lip.along_axis * rng.normal(0, .008, (count, 1)))
    centre[:, 2] -= rng.uniform(0, .05, count)
    diameter = np.clip(rng.lognormal(np.log(params.edge_drop_diameter_m), .4, count), .0015, params.max_edge_drop_diameter_m)
    is_ligament = rng.random(count) < params.ligament_share
    stretch = np.where(is_ligament, rng.uniform(4, 9, count), rng.uniform(1.4, 3.0, count))
    return np.c_[centre, diameter, stretch]
