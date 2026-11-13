"""Foot foam; implementation for water.pool_impacts."""
import numpy as np
from materials.water.impact_config import EMPTY_MESH
from materials.water.impact_drift import _span, _drift


def _fleck(rng, s, o, dist, direction, params):
    """Outline of one irregular foam fleck around (s, o), stretched along its drift: arrays of s and o."""
    size = np.clip(rng.lognormal(np.log(params.foam_size_m), .7), .0015, params.max_foam_size_m)
    elongation = 1 + rng.exponential(.8) * min(1, dist / .1)
    corners = int(rng.integers(7, 14))
    angle = np.sort(rng.uniform(0, 2 * np.pi, corners))
    radius = size / 2 * (1 + .45 * rng.normal(0, 1, corners)).clip(.3, 1.8)
    along = radius * np.cos(angle) * elongation                         # along the drift
    across = radius * np.sin(angle)
    ring_o = o + along * direction[0] - across * direction[1]
    ring_s = s + along * direction[1] + across * direction[0]
    return ring_s, ring_o


def foam(lip, impact_points, strength, pool_height_m, params):
    """Irregular foam flecks clustered at impacts, drifting out and past the ends, stretched as they travel. (V, F)."""
    rng = np.random.default_rng(params.seed + 2)
    count = int(_span(lip, impact_points) * params.foam_per_m)
    if count == 0:
        return EMPTY_MESH
    s, o, dist, direction = _drift(lip, impact_points, rng, params.foam_reach_m, strength ** params.foam_focus_exponent, count, params)
    verts, faces, base = [], [], 0
    for i in range(count):
        if o[i] > params.max_outward_m:
            continue
        ring_s, ring_o = _fleck(rng, s[i], o[i], dist[i], direction[i], params)
        corners = len(ring_s)
        verts.append(lip.world(np.r_[s[i], ring_s], np.r_[o[i], ring_o], np.full(corners + 1, pool_height_m + .0009)))
        faces += [[base, base + 1 + j, base + 1 + (j + 1) % corners] for j in range(corners)]   # fan from the centre
        base += corners + 1
    return (np.concatenate(verts), faces) if verts else EMPTY_MESH
