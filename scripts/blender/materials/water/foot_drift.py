"""Foot drift; implementation for water.foot."""
import numpy as np


def _span(lip, pts):
    """Length of the landing line covered by the impacts, m."""
    return float(np.ptp(lip.local(pts)[0])) if len(pts) else 0.


def _drift(lip, pts, rng, mean_dist, weight, count, p, extra=0.):
    """Spawn count items at impacts (by weight), carry them out and sideways: s, o, distance, unit direction (s, o)."""
    parent = rng.choice(len(pts), size=count, p=weight / weight.sum())
    s0, o0 = lip.local(pts[parent])
    dist = extra + rng.exponential(mean_dist, count)
    direction = np.c_[np.ones(count), rng.normal(0, .7, count)]          # (outward, sideways)
    direction /= np.linalg.norm(direction, axis=1, keepdims=True)
    o = o0 + direction[:, 0] * dist
    s = s0 + direction[:, 1] * dist + rng.normal(0, 1, count) * (p.foam_spread + p.drift * dist)
    return s, o, dist, direction
