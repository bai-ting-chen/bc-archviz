"""Fragment cells; implementation for water.fragments."""
import numpy as np


def _mid_surface(ff):
    return (ff.front + ff.back) / 2


def _torn_cells(ff, s, d):
    """Flat indices of torn grid points, torn area (m^2) and the drop step (m)."""
    step_s = float(abs(s[1] - s[0]))
    step_d = float(abs(d[1] - d[0]))
    torn = np.flatnonzero(~ff.keep.ravel())
    return torn, len(torn) * step_s * step_d, step_d
