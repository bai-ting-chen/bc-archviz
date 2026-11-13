"""Control: TileLayout node group = numpy reference (stack, running, rotated), ids distinct per
tile, no aliasing banding on a far plane. Run: blender -b --factory-startup --python <this>"""

import os as _os, sys as _sys
_sys.path.append(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import controls_import_paths  # noqa: E402,F401 -- every controls topic folder on sys.path
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "blender"))
sys.path.insert(0, os.path.dirname(__file__))
import bpy, numpy as np
import _scene
import materials.tile.tile_layout as tile_layout
from tile_layout_rig import RES, SIZE, CASES, OUTS, plane_with, pixel_coords, stable
from tile_layout_reference import check_reference
from tile_layout_jitter import check_jitter_gaps
from tile_layout_rebuild import check_rebuild
from tile_layout_filtering import check_filtering

def main():
    """Run the layout check families and retain their existing CLI result."""
    fails = []
    check_reference(fails)
    try:
        check_jitter_gaps()
    except AssertionError as exc:
        fails.append(str(exc))
    check_filtering(fails, far=False)
    for changed in (False, True):
        try:
            check_rebuild(changed)
        except AssertionError as exc:
            fails.append(f"rebuild (interface changed={changed}): {exc}")
    check_filtering(fails, far=True)
    print("TILE_LAYOUT_CHECK", "FAIL" if fails else "PASS", *fails, sep="\n  ")
    return 1 if fails else 0

if __name__ == '__main__':
    sys.exit(main())
