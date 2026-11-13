"""Foot drift; implementation for water.pool_impacts."""
import numpy as np


def _span(lip, impact_points):
    """Length of the landing line covered by the impacts, m."""
    return float(np.ptp(lip.local(impact_points)[0])) if len(impact_points) else 0.


def _drift(lip, impact_points, rng, mean_dist, weight, count, params, extra=0.):
    """Spawn count items at impacts (by weight), carry them out and sideways: s, o, distance, unit direction (s, o)."""
    parent = rng.choice(len(impact_points), size=count, p=weight / weight.sum())
    s0, o0 = lip.local(impact_points[parent])
    dist = extra + rng.exponential(mean_dist, count)
    direction = np.c_[np.ones(count), rng.normal(0, .7, count)]          # (outward, sideways)
    direction /= np.linalg.norm(direction, axis=1, keepdims=True)
    o = o0 + direction[:, 0] * dist
    s = s0 + direction[:, 1] * dist + rng.normal(0, 1, count) * (params.foam_spread_m + params.lateral_spread_per_m * dist)
    return s, o, dist, direction
