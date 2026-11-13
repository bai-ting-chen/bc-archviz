"""Film velocity and reloaded ripple-height checks."""

import os as _os, sys as _sys
_sys.path.append(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import controls_import_paths  # noqa: E402,F401 -- every controls topic folder on sys.path
import math
import numpy as np

def check_physics(objs, drop_height_m, stats, checks):
    """Check free-fall velocity and the persisted ripple extrema."""
    vel = np.empty(len(objs['film'].data.vertices) * 3, np.float32)
    objs['film'].data.attributes['velocity'].data.foreach_get('vector', vel)
    vmax = float(np.linalg.norm(vel.reshape(-1, 3), axis=1).max()); expect = math.sqrt(.35 ** 2 + 2 * 9.81 * drop_height_m)
    checks['velocity max ~ sqrt(v0^2+2gH)'] = abs(vmax - expect) < .1 * expect
    lo, hi = stats.get('ripple_mm', (0, 0)); checks['ripple read back non-zero'] = lo < 0 < hi
    return vmax, expect
