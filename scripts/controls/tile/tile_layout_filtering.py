"""Check output units and near/far joint filtering."""

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

def check_filtering(fails, far=False):
    """Check the selected near or far probe."""
    if not far:
        # Emission probe proves the new output forwards width/height in metres (Z = 0).
        size_probe = plane_with("Tile Size", dict(tile_w=0.123, tile_h=0.067, joint=0.004))
        assert np.allclose(size_probe[..., :3], (0.123, 0.067, 0), atol=1e-6), "Tile Size pass-through mismatch"

        # Zero-width joints must not produce rounding speckles.
        zero = plane_with("Joint", dict(tile_w=0.10, tile_h=0.05, joint=0))[..., 0]
        if np.mean(zero == 0) <= 0.999:
            fails.append("zero joint: nonzero mask on >= 0.1% of pixels")
    else:
        # far plane: 8 m over 200 px = 40 mm/px, so 3 mm joints are sub-pixel; with pixel filtering
        # the column means must be smooth (< 3 % spread), not banded by aliasing
        SIZE, RES = 8.0, 200
        far = plane_with("Joint", dict(tile_w=0.045, tile_h=0.145, joint=0.003), RES=RES, SIZE=SIZE)[..., 0]
        cols = far.mean(axis=0)
        if np.std(cols) / max(np.mean(cols), 1e-6) > 0.03: fails.append("far plane: joint banding (aliasing)")
