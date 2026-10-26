"""Film swell; implementation for water.film."""
import numpy as np


def swell_field(s, v, seed):
    """Smooth broad swell in [-1, 1]: 32 noncommensurate modes, 80-200 mm across, ~60 mm half-width along v."""
    rng = np.random.default_rng(seed)
    count = 32
    k_s = rng.uniform(5, 12.5, count) * rng.choice([-1, 1], count)    # cycles per m across
    k_v = rng.uniform(.75, 1.25, count) / .36                          # cycles per m along
    phase = rng.uniform(0, 2 * np.pi, count)
    weight = rng.uniform(.5, 1.5, count)
    weight /= weight.sum()                                             # bounds the sum to [-1, 1]
    out = np.zeros(np.broadcast_shapes(np.shape(s), np.shape(v)))
    for ks, kv, ph, w in zip(k_s, k_v, phase, weight):
        out += w * np.cos(2 * np.pi * (ks * s + kv * v) + ph)
    return out
