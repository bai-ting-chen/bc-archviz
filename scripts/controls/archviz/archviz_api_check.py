"""Baseline for the archviz helper API: every public helper that is cheap to run headless, dumped as JSON.

Used as the refactor proof for scripts/blender/core/archviz.py (RULES GOV_04): dump before the change,
dump after, compare. Renders are skipped (they are covered by the scene controls); the helpers that
import Rhino or write files are not run here.

Usage: ARCHVIZ_PROJECT=<study folder with library/polyhaven/hdris/abandoned_hall_01>
       blender -b --factory-startup --python scripts/controls/archviz/archviz_api_check.py -- <out.json>
"""

import os as _os
import sys as _sys
_CONTROLS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in [_CONTROLS] + [_os.path.join(_CONTROLS, _t) for _t in ('archviz', 'tile', 'material', 'effects', 'water', 'lighting', 'environment', 'regression')]:
    if _d not in _sys.path:
        _sys.path.append(_d)
import json
import math
import os
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "blender"))
import core.archviz as archviz  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from archviz_api_rig import HDRI, rounded, cube, uv_table
from archviz_api_project import check_project, check_meta
from archviz_api_lighting import check_ev, check_hdri_analyse, world_summary, check_world, check_world_plain, check_sun
from archviz_api_render import check_render_setup, check_gpu
from archviz_api_camera import check_camera
from archviz_api_uv import check_uv
from archviz_api_materials import check_material_map

def run(name, fn, RESULTS):
    """Record fn()'s result, or the error, so one failing helper does not hide the rest."""
    try:
        RESULTS[name] = fn()
    except Exception as exc:  # the check reports every helper, even when one breaks
        RESULTS[name] = {"ERROR": "%s: %s" % (type(exc).__name__, exc)}

def main():
    """Record every original API case in the original order."""
    OUT = Path(sys.argv[sys.argv.index("--") + 1])
    RESULTS = {}
    run("project", check_project, RESULTS)
    run("meta", check_meta, RESULTS)
    run("ev", check_ev, RESULTS)
    run("hdri_analyse", check_hdri_analyse, RESULTS)
    run("world_lux", check_world, RESULTS)
    run("world_plain", check_world_plain, RESULTS)
    run("render_setup", check_render_setup, RESULTS)
    run("gpu", check_gpu, RESULTS)
    run("camera", check_camera, RESULTS)
    run("sun", check_sun, RESULTS)
    run("uv", check_uv, RESULTS)
    run("material_map", check_material_map, RESULTS)

    OUT.write_text(json.dumps(RESULTS, indent=2, sort_keys=True), encoding="utf-8")
    print("ARCHVIZ_API_CHECK written", OUT, "errors:", sorted(k for k, v in RESULTS.items() if "ERROR" in v))

if __name__ == '__main__':
    main()
