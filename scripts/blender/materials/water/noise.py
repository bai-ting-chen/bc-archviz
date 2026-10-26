"""Smooth, irregular, seeded 1-D noise: the single noise source for the water fields (metres in, [-1, 1] out).

Knots are spaced irregularly (uniform in [lo, hi] metres), values uniform in [-1, 1], joined by a
quintic smoothstep (C2): no repeated wavelength, no steps. Covers x in [-100, 1100] m.
"""
from functools import lru_cache

import numpy as np

_X0, _X1 = -100.0, 1100.0


@lru_cache(maxsize=1024)
def _knots(seed, lo, hi):
    rng = np.random.default_rng(seed)
    n = int((_X1 - _X0) / lo) + 4
    x = _X0 + np.r_[0.0, np.cumsum(rng.uniform(lo, hi, n))]
    x = x[: np.searchsorted(x, _X1) + 2]
    return x, rng.uniform(-1, 1, len(x))


def smooth(t):
    """Quintic smoothstep of t clipped to [0, 1]."""
    t = np.clip(t, 0, 1)
    return t * t * t * (10 + t * (-15 + 6 * t))


def clustered(x, seed, lo, hi):
    """Irregular smooth noise in [-1, 1] at x metres; knot spacing uniform in [lo, hi] metres."""
    k, v = _knots(int(seed), float(lo), float(hi))
    x = np.asarray(x, dtype=np.float64)
    if x.size and (x.min() < k[0] or x.max() > k[-1]):
        raise ValueError(f'noise argument outside [{k[0]:.0f}, {k[-1]:.0f}] m')
    i = np.clip(np.searchsorted(k, x) - 1, 0, len(k) - 2)
    t = smooth((x - k[i]) / (k[i + 1] - k[i]))
    return v[i] * (1 - t) + v[i + 1] * t


def unit(x, seed, lo, hi):
    """Same noise mapped to [0, 1]."""
    return .5 + .5 * clustered(x, seed, lo, hi)
