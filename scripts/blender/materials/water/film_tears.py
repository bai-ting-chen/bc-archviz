"""Film tears; implementation for water.film."""
import numpy as np
from materials.water import curtain, noise


def tear_value(p, s, v):
    """High = torn: narrow across (slit_lo..slit_hi), long and finite along the stretched fall."""
    seed = p.seed + 150
    across = noise.clustered(s + .04 * noise.clustered(v, seed + 1, .2, .6), seed, p.slit_lo, p.slit_hi)
    along = noise.clustered(v + 2.5 * noise.clustered(s, seed + 2, .05, .2), seed + 3, .15, .6)
    return .55 * across + .55 * along


def _gap_field(p, lip, s, S, D, V, lateral, start):
    """Tear field (> 0 water): slit field + where the meander stretches the sheet + dissolving free edges."""
    stretch = 1 + np.gradient(lateral, s, axis=1)
    ramp = np.clip((D - start) / .6, 0, 1)                             # tears fade in over 0.6 m
    gap = 1.25 - p.tear_rate * np.maximum(0, D - start) ** p.tear_power - tear_value(p, S, V)
    gap = np.minimum(gap, .25 * (p.tear_stretch - stretch) * ramp + (1 - ramp) * 9)
    for end, free in enumerate(p.free_edges):
        if not free:
            continue
        dist = S if end == 0 else lip.length - S                      # distance from that end
        seed = p.seed + 200 + end * 10
        retreat = (p.edge_retreat * D ** 1.3 * (1 + .5 * noise.clustered(V, seed, .1, .4))
                   + .015 * noise.clustered(V + 2 * noise.clustered(S, seed + 1, .05, .2), seed + 2, .04, .15))
        gap = np.minimum(gap, (dist - retreat) / .05)
        band = np.exp(-np.maximum(dist - retreat, 0) / p.edge_band) * np.clip(D / .6, 0, 1)
        gap = gap - p.edge_tear * band
    return gap
