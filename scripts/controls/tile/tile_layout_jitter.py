"""Check jittered tile containment and variable joint gaps."""

import os as _os
import sys as _sys
_CONTROLS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in [_CONTROLS] + [_os.path.join(_CONTROLS, _t) for _t in ('archviz', 'tile', 'material', 'effects', 'water', 'lighting', 'environment', 'regression')]:
    if _d not in _sys.path:
        _sys.path.append(_d)
import bpy
import numpy as np
import materials.tile.tile_layout as tile_layout
from tile_layout_rig import CASES, plane_with, pixel_coords, stable

def check_jitter_gaps():
    """Measure face crossings for 200 tiles on each axis and reject overlap."""
    params = CASES["jitter"]
    w, h, joint = params["tile_w"], params["tile_h"], params["joint"]
    cells = np.arange(-100, 100)
    ox, oy, angle = tile_layout._jitter_transform(
        cells, cells[::-1], w, h, joint,
        params["jitter_offset"], params["jitter_rotation"])
    # Bound every corner, not only centreline gaps: containment rules out overlap
    # at the ends of a rotated tile as well as across staggered rows.
    for x in (-w / 2, w / 2):
        for y in (-h / 2, h / 2):
            xx = np.cos(angle) * x - np.sin(angle) * y + ox
            yy = np.sin(angle) * x + np.cos(angle) * y + oy
            assert np.all(np.abs(xx) <= (w + joint) / 2), "jitter: X corner outside cell"
            assert np.all(np.abs(yy) <= (h + joint) / 2), "jitter: Y corner outside cell"
    for vertical in (False, True):
        pitch = (h if vertical else w) + joint
        cells = np.arange(-100, 100)
        base = cells * pitch
        centre = base + pitch / 2

        def edge(coordinate):
            x, y = (w / 2 + joint / 2, coordinate) if vertical else (coordinate, h / 2 + joint / 2)
            return tile_layout.reference(x, y, **params)["edge"]

        # Bisect entry/exit crossings of the real, rotated tile at its cell centreline.
        bounds = []
        for entering in (True, False):
            lo = base.copy() if entering else centre.copy()
            hi = centre.copy() if entering else base + pitch - 1e-10
            assert np.all(edge(centre) > 0), "jitter: missing centre face"
            assert np.all(edge(lo if entering else hi) < 0), "jitter: face crosses cell boundary"
            for _ in range(45):
                mid = (lo + hi) / 2
                inside = edge(mid) >= 0
                move_low = ~inside if entering else inside
                lo = np.where(move_low, mid, lo)
                hi = np.where(move_low, hi, mid)
            bounds.append((lo + hi) / 2)
        gaps = bounds[0][1:] - bounds[1][:-1]
        assert np.std(gaps) > 0, "jitter: joint widths do not vary"
        assert np.all(gaps >= 0), "jitter: negative joint width (overlap)"
        print(f"JITTER_GAPS {'Y' if vertical else 'X'}: 200 tiles, "
              f"min={gaps.min():.9f} m, std={gaps.std():.9f} m")
