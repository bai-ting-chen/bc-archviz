"""Strings and drops of a torn falling film (references/materials/water/water-free-falling-film.md §3.7).

A gap is never empty: hanging strings and falling drops fill torn cells (densities per m^2 of torn area, so they
scale with the curtain), and drops/ligaments shed from torn edges (per metre of lip, more lower down).
Drops are arrays (N, 5) = x, y, z, diameter, stretch along the fall; strings are (M, 4) = x, y, z, radius.
water.mesh turns both into objects.
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


def _mid_surface(ff):
    return (ff.front + ff.back) / 2


def _torn_cells(ff, s, d):
    """Flat indices of torn grid points, torn area (m^2) and the drop step (m)."""
    step_s = float(abs(s[1] - s[0]))
    step_d = float(abs(d[1] - d[0]))
    torn = np.flatnonzero(~ff.keep.ravel())
    return torn, len(torn) * step_s * step_d, step_d


def edge_drops(ff, lip, p, s, d):
    """Drops and ligaments shed at torn edges, weighted toward the foot: array (N, 5)."""
    rng = np.random.default_rng(p.seed)
    near_edge = (np.abs(ff.gap) < .04) & (ff.D > ff.tear_start + .2)
    idx = np.flatnonzero(near_edge.ravel())
    count = min(int(p.edge_drops_per_m * lip.length), len(idx))
    if count == 0:
        return np.zeros((0, 5))
    weight = ff.D.ravel()[idx] - ff.tear_start
    pick = rng.choice(idx, size=count, replace=False, p=weight / weight.sum())
    centre = (_mid_surface(ff).reshape(-1, 3)[pick]
              + ff.normal.reshape(-1, 3)[pick] * rng.uniform(-.004, .03, (count, 1))
              + lip.along * rng.normal(0, .008, (count, 1)))
    centre[:, 2] -= rng.uniform(0, .05, count)
    diameter = np.clip(rng.lognormal(np.log(p.edge_drop_d), .4, count), .0015, p.edge_drop_max)
    is_ligament = rng.random(count) < p.ligament_share
    stretch = np.where(is_ligament, rng.uniform(4, 9, count), rng.uniform(1.4, 3.0, count))
    return np.c_[centre, diameter, stretch]


def _string(rng, mid, normal, lip, r0, c0, n_rows, step_d, median_len):
    """One beaded string hanging down from grid cell (r0, c0), following the local water path; None if too short."""
    length = np.clip(rng.lognormal(np.log(median_len), .6), .02, .40)
    rows = np.arange(r0, min(n_rows - 1, r0 + int(length / step_d)) + 1, 2)
    if len(rows) < 3:
        return None
    pts = mid[rows, c0].copy()
    sway = rng.normal(0, .004) + .003 * np.sin(np.linspace(0, rng.uniform(2, 7), len(rows)) + rng.uniform(0, 6))
    pts += lip.along * sway[:, None]
    pts += normal[rows, c0] * rng.uniform(-.012, .012)                 # in front of or behind the sheet
    beads = len(rows) * step_d * 2 / rng.uniform(.012, .025) * np.pi
    radius = rng.uniform(.0007, .0018) * (1 + .45 * np.sin(np.linspace(0, beads, len(rows))))
    radius[0] *= .4
    radius[-1] *= .4
    return np.c_[pts, radius]


def gap_fill(ff, lip, p, s, d):
    """Strings (list of (M, 4) arrays) and drops (N, 5) inside torn cells."""
    rng = np.random.default_rng(p.seed + 1)
    torn, area, step_d = _torn_cells(ff, s, d)
    mid = _mid_surface(ff)
    n_rows, n_cols = ff.keep.shape
    strings = []
    if len(torn):
        for _ in range(int(area * p.gap_strings_per_m2)):
            r0, c0 = divmod(int(rng.choice(torn)), n_cols)
            string = _string(rng, mid, ff.normal, lip, r0, c0, n_rows, step_d, p.string_len)
            if string is not None:
                strings.append(string)
    count = int(area * p.gap_drops_per_m2)
    if not count or not len(torn):
        return strings, np.zeros((0, 5))
    rows, cols = np.divmod(rng.choice(torn, count), n_cols)
    centre = (mid[rows, cols]
              + ff.normal[rows, cols] * rng.uniform(-.01, .02, (count, 1))
              + lip.along * rng.normal(0, .006, (count, 1)))
    diameter = np.clip(rng.lognormal(np.log(.003), .45, count), .0012, .007)
    return strings, np.c_[centre, diameter, rng.uniform(1.2, 3.0, count)]
