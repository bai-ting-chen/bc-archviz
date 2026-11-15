"""Strings and drops inside torn film cells and along their edges."""
from dataclasses import dataclass

import numpy as np


@dataclass
class FragmentParams:
    """Densities and sizes of gap strings, gap drops and edge drops (starting values; size from the shot)."""
    edge_drops_per_m: float = 570.     # per m of lip
    edge_drop_diameter_m: float = .0035         # m median diameter
    max_edge_drop_diameter_m: float = .008
    ligament_share: float = .30        # share of edge drops that are stretched ligaments
    gap_strings_per_m2: float = 900.   # per m^2 of torn area
    gap_drops_per_m2: float = 5000.
    string_length_m: float = .09            # m median length (lognormal sigma 0.6, clipped 0.02-0.40)
    seed: int = 2200


def _mid_surface(ff):
    return (ff.front + ff.back) / 2


def _torn_cells(ff, s, d):
    """Flat indices of torn grid points, torn area (m^2) and the drop step (m)."""
    step_s = float(abs(s[1] - s[0]))
    step_d = float(abs(d[1] - d[0]))
    torn = np.flatnonzero(~ff.keep.ravel())
    return torn, len(torn) * step_s * step_d, step_d


def edge_drops(film_fields, lip, params, s, d):
    """Drops and ligaments shed at torn edges, weighted toward the foot: array (N, 5)."""
    rng = np.random.default_rng(params.seed)
    near_edge = (np.abs(film_fields.gap) < .04) & (film_fields.drop_m > film_fields.tear_start_m + .2)
    idx = np.flatnonzero(near_edge.ravel())
    count = min(int(params.edge_drops_per_m * lip.length_m), len(idx))
    if count == 0:
        return np.zeros((0, 5))
    weight = film_fields.drop_m.ravel()[idx] - film_fields.tear_start_m
    pick = rng.choice(idx, size=count, replace=False, p=weight / weight.sum())
    centre = (_mid_surface(film_fields).reshape(-1, 3)[pick]
              + film_fields.normal.reshape(-1, 3)[pick] * rng.uniform(-.004, .03, (count, 1))
              + lip.along_axis * rng.normal(0, .008, (count, 1)))
    centre[:, 2] -= rng.uniform(0, .05, count)
    diameter = np.clip(rng.lognormal(np.log(params.edge_drop_diameter_m), .4, count), .0015, params.max_edge_drop_diameter_m)
    is_ligament = rng.random(count) < params.ligament_share
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
    pts += lip.along_axis * sway[:, None]
    pts += normal[rows, c0] * rng.uniform(-.012, .012)                 # in front of or behind the sheet
    beads = len(rows) * step_d * 2 / rng.uniform(.012, .025) * np.pi
    radius = rng.uniform(.0007, .0018) * (1 + .45 * np.sin(np.linspace(0, beads, len(rows))))
    radius[0] *= .4
    radius[-1] *= .4
    return np.c_[pts, radius]


def gap_fill(film_fields, lip, params, s, d):
    """Strings (list of (M, 4) arrays) and drops (N, 5) inside torn cells."""
    rng = np.random.default_rng(params.seed + 1)
    torn, area, step_d = _torn_cells(film_fields, s, d)
    mid = _mid_surface(film_fields)
    n_rows, n_cols = film_fields.keep.shape
    strings = []
    if len(torn):
        for _ in range(int(area * params.gap_strings_per_m2)):
            r0, c0 = divmod(int(rng.choice(torn)), n_cols)
            string = _string(rng, mid, film_fields.normal, lip, r0, c0, n_rows, step_d, params.string_length_m)
            if string is not None:
                strings.append(string)
    count = int(area * params.gap_drops_per_m2)
    if not count or not len(torn):
        return strings, np.zeros((0, 5))
    rows, cols = np.divmod(rng.choice(torn, count), n_cols)
    centre = (mid[rows, cols]
              + film_fields.normal[rows, cols] * rng.uniform(-.01, .02, (count, 1))
              + lip.along_axis * rng.normal(0, .006, (count, 1)))
    diameter = np.clip(rng.lognormal(np.log(.003), .45, count), .0012, .007)
    return strings, np.c_[centre, diameter, rng.uniform(1.2, 3.0, count)]
