"""Control: TileUV distances = true surface distances (planar wall, rotated wall, floor,
cylinder crossing the ±pi cut). Run: blender -b --factory-startup --python <this>"""

import os as _os
import sys as _sys
_CONTROLS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in [_CONTROLS] + [_os.path.join(_CONTROLS, _t) for _t in ('archviz', 'tile', 'material', 'effects', 'water', 'lighting', 'environment', 'regression')]:
    if _d not in _sys.path:
        _sys.path.append(_d)
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "blender"))
import bpy, bmesh, numpy as np
import materials.tile.tile_mapping as tile_mapping
sys.path.insert(0, os.path.dirname(__file__))
from tile_mapping_distances import check_distances
from tile_mapping_planar import check_planar, check_slab
from tile_mapping_rings import check_rings
from tile_mapping_contract import check_contract
from tile_mapping_annulus import check_annulus
from tile_mapping_rig import uv_vs_world, continuity, orientation

def main():
    """Run all UV mapping families in their original order."""
    bpy.ops.wm.read_homefile(use_empty=True)
    fails = []
    w, f, c = check_distances(fails)
    check_planar(w, f, c, fails)
    check_rings(fails)
    slab = check_slab(fails)
    check_contract(slab, f, fails)
    check_annulus(fails)
    print("TILE_MAPPING_CHECK", "FAIL" if fails else "PASS", *fails, sep="\n  ")
    return 1 if fails else 0

if __name__ == '__main__':
    sys.exit(main())
