"""Foot bubbles; implementation for water.pool_impacts."""
import numpy as np
from materials.water.impact_config import EMPTY_MESH
from materials.water.impact_drift import _span, _drift


def _dome():
    """Unit dome (upper hemisphere, 8 segments): vertices and quad/triangle faces."""
    angle = np.linspace(0, 2 * np.pi, 9)[:-1]
    elevation = np.array([0., .55, 1.05, 1.45])
    ring = np.array([[np.cos(e) * np.cos(t), np.cos(e) * np.sin(t), np.sin(e)] for e in elevation[:-1] for t in angle])
    unit = np.r_[ring, [[0, 0, 1]]]
    faces = []
    for r in range(len(elevation) - 2):
        for j in range(8):
            a0 = r * 8 + j
            a1 = r * 8 + (j + 1) % 8
            faces.append([a0, a1, a1 + 8, a0 + 8])
    top = (len(elevation) - 2) * 8
    faces += [[top + j, top + (j + 1) % 8, len(unit) - 1] for j in range(8)]
    return unit, faces


def bubbles(lip, impact_points, strength, pool_height_m, params):
    """Floating clear domes (single or in rafts), carried far out and past the ends. (V, F); use thin-wall water."""
    rng = np.random.default_rng(params.seed + 3)
    count = int(_span(lip, impact_points) * params.bubbles_per_m)
    if count == 0:
        return EMPTY_MESH
    s, o, _, _ = _drift(lip, impact_points, rng, params.bubble_reach_m, strength ** .3, count, params, extra=.05)
    unit, dome_faces = _dome()
    verts, faces, base = [], [], 0
    for i in range(count):
        if o[i] > params.max_outward_m:
            continue
        in_raft = 1 if rng.random() > params.raft_share else int(rng.integers(3, 12))
        for _ in range(in_raft):
            r = np.clip(rng.lognormal(np.log(params.bubble_diameter_m / 2), .5), .001, .0075)
            ds, do = (rng.normal(0, .006, 2) * np.sqrt(in_raft)) if in_raft > 1 else (0., 0.)
            centre = lip.world(np.array([s[i] + ds]), np.array([o[i] + do]), np.array([pool_height_m - .2 * r]))[0]
            verts.append(unit * [r, r, .85 * r] + centre)                 # squashed, sunk 20 % of the radius
            faces += [[base + v for v in f] for f in dome_faces]
            base += len(unit)
    return (np.concatenate(verts), faces) if verts else EMPTY_MESH
