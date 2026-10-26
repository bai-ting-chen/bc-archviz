"""Compare all layout outputs against the numpy reference."""

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

def check_reference(fails):
    """Check edges, joints, tile coordinates and per-tile IDs."""
    for name, p in CASES.items():
        u, v = pixel_coords()
        ref = tile_layout.reference(u, v, **p)
        cell = ref["col"] * 100003 + ref["row"]
        same = np.ones_like(cell, bool)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                same &= np.roll(np.roll(cell, dy, 0), dx, 1) == cell
        ok = same & stable(ref["joint"] == 0) | (same & stable(ref["joint"] == 1))
        img = plane_with("Edge", p)[..., 0]
        err = np.abs(img - (ref["edge"] * 10 + 0.5))[ok]
        if np.median(err) > 2e-3: fails.append(f"{name}: Edge median err {np.median(err):.4f}")
        img = plane_with("Joint", p)[..., 0]
        if np.mean(np.abs(img - ref["joint"])[ok]) > 0.01: fails.append(f"{name}: Joint mismatch")
        img = plane_with("Tile UV", p)
        face = ok & (ref["joint"] == 0)
        if np.median(np.abs(img[..., 0] - ref["tile_uv_x"])[face]) > 0.01: fails.append(f"{name}: UV x")
        if np.median(np.abs(img[..., 1] - ref["tile_uv_y"])[face]) > 0.01: fails.append(f"{name}: UV y")
        ids = plane_with("Tile ID", p)[..., 0]
        per = {}
        for c, val in zip(cell[face].ravel(), ids[face].ravel()):
            per.setdefault(c, []).append(val)
        spread = max(np.ptp(vs) for vs in per.values())
        uniq = len({round(float(np.median(vs)), 4) for vs in per.values()}) / len(per)
        if spread > 1e-4: fails.append(f"{name}: Tile ID not constant within a tile ({spread:.5f})")
        if uniq < 0.97: fails.append(f"{name}: Tile IDs not distinct ({uniq:.3f})")
