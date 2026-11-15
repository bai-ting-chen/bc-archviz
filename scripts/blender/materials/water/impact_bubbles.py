"""Foot bubbles; water impact fields and geometry."""
import numpy as np
from materials.water import mesh_builders
from materials.water.impact_config import EMPTY_MESH
from materials.water.impact_drift import _span, _drift


def bubbles(lip, impact_points, strength, pool_height_m, params):
    """Floating clear domes (single or in rafts), carried far out and past the ends. (V, F); use thin-wall water."""
    rng = np.random.default_rng(params.seed + 3)
    count = int(_span(lip, impact_points) * params.bubbles_per_m)
    if count == 0:
        return EMPTY_MESH
    s, o, _, _ = _drift(lip, impact_points, rng, params.bubble_reach_m, strength ** .3, count, params, extra=.05)
    unit, dome_faces = mesh_builders._dome()
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
