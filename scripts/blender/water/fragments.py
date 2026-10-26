"""Strings and drops of a torn falling film (references/materials/water-free-falling-film.md §3.7).

A gap is never empty: hanging strings and falling drops fill torn cells (densities per m^2 of torn area, so they
scale with the curtain), and drops/ligaments shed from torn edges (per metre of lip, weighted by drop).
Returns plain arrays; water.mesh turns them into objects.
"""
from dataclasses import dataclass

import numpy as np


@dataclass
class FragmentParams:
    """Densities and sizes of gap strings, gap drops and edge drops (starting values; size from the shot)."""
    edge_drops_per_m: float = 570.     # per m of lip
    edge_drop_d: float = .0035         # m median diameter
    edge_drop_max: float = .008
    ligament_share: float = .30        # share of edge drops that are stretched ligaments
    gap_strings_per_m2: float = 900.   # per m^2 of torn area
    gap_drops_per_m2: float = 5000.
    string_len: float = .09            # m median length (lognormal sigma 0.6, clipped 0.02-0.40)
    seed: int = 2200


def _torn_area(fs, s, d):
    ds_ = float(abs(s[1] - s[0])); dd_ = float(abs(d[1] - d[0]))
    torn = np.flatnonzero(~fs['keep'].ravel())
    return torn, len(torn) * ds_ * dd_, dd_


def edge_drops(fs, lip, p, s, d):
    """Drops and ligaments shed at torn edges: array (N, 5) = x, y, z, diameter, stretch along the fall."""
    rng = np.random.default_rng(p.seed)
    gap, D = fs['gap'], fs['D']
    edge = (np.abs(gap) < .04) & (D > fs['start'] + .2)
    idx = np.flatnonzero(edge.ravel())
    n = min(int(p.edge_drops_per_m * lip.length), len(idx))
    if n == 0: return np.zeros((0, 5))
    w = D.ravel()[idx] - fs['start']; w = w / w.sum()
    pick = rng.choice(idx, size=n, replace=False, p=w)
    mid = ((fs['front'] + fs['back']) / 2).reshape(-1, 3)[pick]; nn = fs['normal'].reshape(-1, 3)[pick]
    c = mid + nn * rng.uniform(-.004, .03, (n, 1)) + lip.along * rng.normal(0, .008, (n, 1))
    c[:, 2] -= rng.uniform(0, .05, n)
    diam = np.clip(rng.lognormal(np.log(p.edge_drop_d), .4, n), .0015, p.edge_drop_max)
    st = np.where(rng.random(n) < p.ligament_share, rng.uniform(4, 9, n), rng.uniform(1.4, 3.0, n))
    return np.c_[c, diam, st]


def gap_fill(fs, lip, p, s, d):
    """Strings (list of (M, 4) arrays: x, y, z, radius) and drops (N, 5) inside torn cells."""
    rng = np.random.default_rng(p.seed + 1)
    torn, area, dd_ = _torn_area(fs, s, d)
    mid = (fs['front'] + fs['back']) / 2; n = fs['normal']; nr, nc = fs['keep'].shape
    strings = []
    if len(torn):
        for _ in range(int(area * p.gap_strings_per_m2)):
            r0, c0 = divmod(int(rng.choice(torn)), nc)
            length = np.clip(rng.lognormal(np.log(p.string_len), .6), .02, .40)
            rows = np.arange(r0, min(nr - 1, r0 + int(length / dd_)) + 1, 2)
            if len(rows) < 3: continue
            pts = mid[rows, c0].copy()
            pts += lip.along * (rng.normal(0, .004) + .003 * np.sin(np.linspace(0, rng.uniform(2, 7), len(rows)) + rng.uniform(0, 6)))[:, None]
            pts += n[rows, c0] * rng.uniform(-.012, .012)
            k = len(rows) * dd_ * 2 / rng.uniform(.012, .025) * np.pi
            rad = rng.uniform(.0007, .0018) * (1 + .45 * np.sin(np.linspace(0, k, len(rows))))
            rad[0] *= .4; rad[-1] *= .4
            strings.append(np.c_[pts, rad])
    nd = int(area * p.gap_drops_per_m2)
    drops = np.zeros((0, 5))
    if nd and len(torn):
        k = rng.choice(torn, nd); r0, c0 = np.divmod(k, nc)
        c = mid[r0, c0] + n[r0, c0] * rng.uniform(-.01, .02, (nd, 1)) + lip.along * rng.normal(0, .006, (nd, 1))
        drops = np.c_[c, np.clip(rng.lognormal(np.log(.003), .45, nd), .0012, .007), rng.uniform(1.2, 3.0, nd)]
    return strings, drops
