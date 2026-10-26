"""Pool-surface height field around falling water: craters, crowns, rings, wall-parallel fronts, chop
(references/materials/water/water-ripple.md). Pure numpy; water.shading installs it as a bump on the pool material.

The field lives on a lip-local grid H[s, o]: s = -reach_side..length+reach_side along the lip, o = 0..reach_out
from the wall face. Heights in metres; each component is soft-capped (tanh) so overlapping impacts never stack.
"""
from dataclasses import dataclass

import numpy as np


@dataclass
class RippleParams:
    """Grid, extent and strengths of the pool ripple field (craters, chop, ring waves, line fronts)."""
    step: float = .004          # m grid
    reach_out: float = 2.0      # m from the wall face
    reach_side: float = 1.0     # m past each end
    crater: float = 1.0         # strength of crater/crown/capillary relief per impact
    crater_cap: float = .004    # m soft cap
    chop: float = 2.0
    chop_reach: float = .6      # m decay from the wall
    waves: float = 6.0          # strength of ring waves + line fronts (0 = off)
    waves_cap: float = .003     # m soft cap
    seed: int = 2310


def grid(lip, p):
    """Axes (s_axis, o_axis) and 2-D arrays (S, O) indexed [s, o] of the ripple field."""
    o_axis = np.arange(0., p.reach_out, p.step)
    s_axis = np.arange(-p.reach_side, lip.length + p.reach_side, p.step)
    S, O = np.meshgrid(s_axis, o_axis, indexing='ij')
    return s_axis, o_axis, S, O


def _soft_cap(H, cap):
    return cap * np.tanh(H / cap)


def _craters(S, O, s_axis, o_axis, s_imp, o_imp, strength, p, rng):
    """Per impact: a crater, a lobed crown ring at radius R and damped capillary ripples outside it."""
    H = np.zeros_like(O)
    for si, oi, k in zip(s_imp, o_imp, strength):
        R = rng.uniform(.012, .04) * (.6 + .5 * k)
        amp = rng.uniform(.0015, .005) * k * p.crater
        j0, j1 = np.searchsorted(s_axis, [si - .25, si + .25])
        i0, i1 = np.searchsorted(o_axis, [oi - .25, oi + .25])
        do = O[j0:j1, i0:i1] - oi
        ds = (S[j0:j1, i0:i1] - si) * rng.uniform(.7, 1.3)              # slightly elliptical
        r = np.hypot(do, ds) + 1e-6
        lobes = 1 + .35 * np.sin(rng.integers(3, 8) * np.arctan2(ds, do) + rng.uniform(0, 6))
        h = -.7 * amp * np.exp(-(r / (.6 * R)) ** 2) + amp * lobes * np.exp(-((r - R) / (.35 * R)) ** 2)
        wavenumber = 2 * np.pi / rng.uniform(.012, .022)
        outside = (r - R).clip(0)
        h += .35 * amp * np.sin(wavenumber * (r - R) + rng.uniform(0, 6)) * np.exp(-outside / rng.uniform(.04, .12)) * (r > R)
        H[j0:j1, i0:i1] += h
    return _soft_cap(H, p.crater_cap)


def _chop(S, O, p):
    """Short irregular chop from 40 random directions, strongest at the wall."""
    rng = np.random.default_rng(p.seed + 5)
    chop = np.zeros_like(O)
    for _ in range(40):
        k_o, k_s = rng.normal(0, 1, 2)
        wavenumber = rng.uniform(2 * np.pi / .09, 2 * np.pi / .02)
        norm = np.hypot(k_o, k_s)
        chop += np.sin(wavenumber * (k_o * O + k_s * S) / norm + rng.uniform(0, 6)) / np.sqrt(40)
    return p.chop * .0009 * chop * np.exp(-O / p.chop_reach)


def _ring_waves(S, O, s_imp, o_imp, strength, rng, W):
    """Rings from the stronger half of impacts: short (2-6 cm, decay ~8 wavelengths) and long (8-25 cm, ~12)."""
    s_axis, o_axis = S[:, 0], O[0]
    for i in np.argsort(-strength)[:len(strength) // 2]:
        si, oi, k = s_imp[i], o_imp[i], strength[i]
        for lo, hi, decay_waves, amp in [(.02, .06, 8, .0008), (.08, .25, 12, .0005)]:
            wavelength = rng.uniform(lo, hi)
            decay = decay_waves * wavelength
            rows = np.abs(s_axis - si) < 3 * decay
            cols = np.abs(o_axis - oi) < 3 * decay
            if not rows.any() or not cols.any():
                continue
            block = np.ix_(rows, cols)
            r = np.hypot(O[block] - oi, S[block] - si) + 1e-4
            W[block] += (amp * k * np.sin(2 * np.pi * r / wavelength + rng.uniform(0, 6))
                         * np.exp(-r / decay) / np.sqrt(1 + r / .05))


def _line_fronts(S, O, s_imp, rng, W):
    """36 irregular fronts leaving the whole landing line within +-40 deg of the wall normal, bending along it."""
    s0, s1 = float(s_imp.min()), float(s_imp.max())
    past_ends = np.exp(-np.maximum(0, s0 - S) ** 2 / .5) * np.exp(-np.maximum(0, S - s1) ** 2 / .5)
    for _ in range(36):
        wavelength = np.exp(rng.uniform(np.log(.05), np.log(.40)))
        heading = rng.uniform(-.7, .7)
        phase = (2 * np.pi * (O * np.cos(heading) + (S - s0) * np.sin(heading)) / wavelength + rng.uniform(0, 6)
                 + 1.5 * np.sin(2 * np.pi * S / rng.uniform(.4, 1.5) + rng.uniform(0, 6)))
        W += .00035 * np.sqrt(wavelength / .1) * np.sin(phase) * np.exp(-O / (10 * wavelength)) * past_ends / np.sqrt(6)


def _waves(S, O, s_imp, o_imp, strength, p):
    rng = np.random.default_rng(p.seed + 11)
    W = np.zeros_like(O)
    _ring_waves(S, O, s_imp, o_imp, strength, rng, W)
    _line_fronts(S, O, s_imp, rng, W)
    return _soft_cap(W * p.waves, p.waves_cap)


def height_field(lip, impact_pts, strength, p):
    """Height (m) H[s, o] on the lip-local grid, faded to zero at its borders; returns (s_axis, o_axis, H)."""
    s_axis, o_axis, S, O = grid(lip, p)
    s_imp, o_imp = lip.local(impact_pts)
    rng = np.random.default_rng(p.seed)
    H = _craters(S, O, s_axis, o_axis, s_imp, o_imp, strength, p, rng) + _chop(S, O, p)
    if p.waves:
        H = H + _waves(S, O, s_imp, o_imp, strength, p)
    fade = (np.clip((p.reach_out - O) / .3, 0, 1)
            * np.clip((S - s_axis[0]) / .3, 0, 1)
            * np.clip((s_axis[-1] - S) / .3, 0, 1))
    return s_axis, o_axis, H * fade


def slope_stats(H, step):
    """RMS and 99th-percentile surface slope (rad) of a height field: ripples need ~0.05-0.15 rad to read."""
    g1, g2 = np.gradient(H, step)
    slope = np.arctan(np.hypot(g1, g2))
    return float(np.sqrt((slope ** 2).mean())), float(np.percentile(slope, 99))
