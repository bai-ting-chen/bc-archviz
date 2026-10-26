"""Pool-surface height field around falling water: craters, crowns, rings, wall-parallel fronts, chop
(references/materials/water-ripple.md). Pure numpy; water.pool installs it as a bump on the pool material.

The field lives on a lip-local grid: o = 0..reach_out from the wall face, a = -reach_side..length+reach_side.
Heights in metres; each component is soft-capped (tanh) so overlapping impacts never stack to centimetres.
"""
from dataclasses import dataclass

import numpy as np


@dataclass
class RippleParams:
    step: float = .004          # m grid
    reach_out: float = 2.0      # m from the wall face
    reach_side: float = 1.0     # m past each end
    crater: float = 1.0         # strength of crater/crown/capillary relief per impact
    crater_cap: float = .004    # m
    chop: float = 2.0
    chop_reach: float = .6      # m decay from the wall
    waves: float = 6.0          # strength of ring waves + line fronts
    waves_cap: float = .003     # m
    seed: int = 2310


def grid(lip, p):
    """Lip-local axes (o, a) and 2-D arrays (O, A) of the ripple field."""
    o = np.arange(0., p.reach_out, p.step); a = np.arange(-p.reach_side, lip.length + p.reach_side, p.step)
    A, O = np.meshgrid(a, o, indexing='ij')
    return o, a, O, A


def _craters(O, A, oi, ai, strength, p, rng, o_ax, a_ax):
    H = np.zeros_like(O)
    for po, pa, s in zip(oi, ai, strength):
        R = rng.uniform(.012, .04) * (.6 + .5 * s); amp = rng.uniform(.0015, .005) * s * p.crater
        j0, j1 = np.searchsorted(a_ax, [pa - .25, pa + .25]); i0, i1 = np.searchsorted(o_ax, [po - .25, po + .25])
        do = O[j0:j1, i0:i1] - po; da = (A[j0:j1, i0:i1] - pa) * rng.uniform(.7, 1.3)
        r = np.hypot(do, da) + 1e-6; th = np.arctan2(da, do)
        lobes = 1 + .35 * np.sin(rng.integers(3, 8) * th + rng.uniform(0, 6))
        h = -.7 * amp * np.exp(-(r / (.6 * R)) ** 2) + amp * lobes * np.exp(-((r - R) / (.35 * R)) ** 2)
        k = 2 * np.pi / rng.uniform(.012, .022)
        h += .35 * amp * np.sin(k * (r - R) + rng.uniform(0, 6)) * np.exp(-(r - R).clip(0) / rng.uniform(.04, .12)) * (r > R)
        H[j0:j1, i0:i1] += h
    return p.crater_cap * np.tanh(H / p.crater_cap)


def _chop(O, A, p):
    rr = np.random.default_rng(p.seed + 5); c = np.zeros_like(O)
    for _ in range(40):
        k1, k2 = rr.normal(0, 1, 2); kk = rr.uniform(2 * np.pi / .09, 2 * np.pi / .02); nrm = np.hypot(k1, k2)
        c += np.sin(kk * (k1 * O + k2 * A) / nrm + rr.uniform(0, 6)) / np.sqrt(40)
    return p.chop * .0009 * c * np.exp(-O / p.chop_reach)


def _waves(O, A, oi, ai, strength, lip, p):
    rng = np.random.default_rng(p.seed + 11); W = np.zeros_like(O)
    a_ax, o_ax = A[:, 0], O[0]
    for i in np.argsort(-strength)[:len(strength) // 2]:                 # ring sources at the stronger impacts
        po, pa, s = oi[i], ai[i], strength[i]
        for lo, hi, lf, amp in [(.02, .06, 8, .0008), (.08, .25, 12, .0005)]:
            lam = rng.uniform(lo, hi); L = lf * lam
            ja = np.abs(a_ax - pa) < 3 * L; io = np.abs(o_ax - po) < 3 * L
            if not ja.any() or not io.any(): continue
            r = np.hypot(O[np.ix_(ja, io)] - po, A[np.ix_(ja, io)] - pa) + 1e-4
            W[np.ix_(ja, io)] += amp * s * np.sin(2 * np.pi * r / lam + rng.uniform(0, 6)) * np.exp(-r / L) / np.sqrt(1 + r / .05)
    a0, a1 = float(ai.min()), float(ai.max())
    env = np.exp(-np.maximum(0, a0 - A) ** 2 / .5) * np.exp(-np.maximum(0, A - a1) ** 2 / .5)
    for _ in range(36):                                                    # fronts from the whole landing line
        lam = np.exp(rng.uniform(np.log(.05), np.log(.40))); th = rng.uniform(-.7, .7)
        ph = 2 * np.pi * (O * np.cos(th) + (A - a0) * np.sin(th)) / lam + rng.uniform(0, 6) \
            + 1.5 * np.sin(2 * np.pi * A / rng.uniform(.4, 1.5) + rng.uniform(0, 6))
        W += .00035 * np.sqrt(lam / .1) * np.sin(ph) * np.exp(-O / (10 * lam)) * env / np.sqrt(6)
    W *= p.waves
    return p.waves_cap * np.tanh(W / p.waves_cap)


def height_field(lip, impact_pts, strength, p):
    """Height (m) on the lip-local grid: returns (o_axis, a_axis, H[a, o]) faded to zero at the borders."""
    o_ax, a_ax, O, A = grid(lip, p)
    ai, oi = lip.local(impact_pts)
    rng = np.random.default_rng(p.seed)
    H = _craters(O, A, oi, ai, strength, p, rng, o_ax, a_ax) + _chop(O, A, p)
    if p.waves: H = H + _waves(O, A, oi, ai, strength, lip, p)
    H *= np.clip((p.reach_out - O) / .3, 0, 1) * np.clip((A - a_ax[0]) / .3, 0, 1) * np.clip((a_ax[-1] - A) / .3, 0, 1)
    return o_ax, a_ax, H


def slope_stats(H, step):
    """RMS and 99th-percentile surface slope (rad) of a height field: ripples need ~0.05-0.15 rad to read."""
    gy, gx = np.gradient(H, step)
    sl = np.arctan(np.hypot(gx, gy))
    return float(np.sqrt((sl ** 2).mean())), float(np.percentile(sl, 99))
