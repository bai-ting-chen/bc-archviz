"""Film geometry validity, winding and occupancy checks."""

import os as _os
import sys as _sys
_CONTROLS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in [_CONTROLS] + [_os.path.join(_CONTROLS, _t) for _t in ('archviz', 'tile', 'material', 'effects', 'water', 'lighting', 'environment', 'regression')]:
    if _d not in _sys.path:
        _sys.path.append(_d)
import numpy as np

def check_geometry(objs, stats, checks):
    """Measure finite outward geometry, tears, folds and fragments."""
    co = np.empty(len(objs['film'].data.vertices) * 3, np.float32); objs['film'].data.vertices.foreach_get('co', co)
    checks['film finite'] = bool(np.isfinite(co).all())
    vol = 0.0; v3 = co.reshape(-1, 3)
    for poly in objs['film'].data.polygons:            # signed volume > 0 <=> faces wound outward
        idx = list(poly.vertices); a0 = v3[idx[0]]
        for i in range(1, len(idx) - 1): vol += np.dot(a0, np.cross(v3[idx[i]], v3[idx[i + 1]])) / 6
    checks['film wound outward (signed volume > 0)'] = vol > 0
    stats['film_signed_volume_m3'] = float(vol)
    checks['torn fraction 0.03-0.40'] = .03 <= stats['torn'] <= .40
    checks['folded fraction < 0.30'] = stats['folded'] < .30
    checks['strings and drops present'] = stats['strings'] > 0 and stats['drops'] > 0
