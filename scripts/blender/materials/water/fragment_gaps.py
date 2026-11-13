"""Fragment gaps; implementation for water.film_fragments."""
import numpy as np
from materials.water.fragment_cells import _mid_surface, _torn_cells


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
