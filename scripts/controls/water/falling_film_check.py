"""Control: build a free-falling water film with the `materials.water` package on a scene it was not written for, check it.

Scene: a 4 m wall turned 30 deg off the world axes, a 2.4 m drop into a pool, a camera looking along the wall.
Checks (printed as JSON, non-zero exit on failure): finite geometry, torn and folded fractions in range, strings and
drops present, film velocity up to sqrt(v0^2 + 2 g H), pool ripple field read back non-zero from its EXR, wet proxy
lying on the wall face, and a rendered thumbnail that is not empty.

Usage: blender -b --factory-startup --python-exit-code 1 --python falling_film_check.py -- <out_dir> [res=640] [samples=32]
Writes <out_dir>/falling_film_check.png, falling_film_ripple.exr, falling_film_check.json.
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

import bpy
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "blender"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _scene
from materials.water import water as water_mat
from materials.water import build, curtain

from falling_film_rig import scene
from falling_film_geometry import check_geometry
from falling_film_physics import check_physics
from falling_film_proxy import check_proxy
from falling_film_render import check_render

def main():
    """Run all film check families and write their original report."""
    argv = sys.argv[sys.argv.index('--') + 1:]
    OUT = Path(argv[0]); OUT.mkdir(parents=True, exist_ok=True)
    opt = dict(a.split('=') for a in argv[1:])
    RES = int(opt.get('res', 640)); SAMPLES = int(opt.get('samples', 32))

    sc, objs, stats, proxy, lip, setup, H = scene(OUT, RES, SAMPLES)
    checks = {}
    check_geometry(objs, stats, checks)
    vmax, expect = check_physics(objs, H, stats, checks)
    check_proxy(proxy, lip, setup, checks)
    check_render(sc, OUT, checks)
    stats.update(velocity_max=vmax, velocity_expected=expect)
    (OUT / 'falling_film_check.json').write_text(json.dumps(dict(checks=checks, stats=stats), indent=1, default=float))
    print(json.dumps(dict(checks=checks, stats=stats), default=float))
    if not all(checks.values()):
        raise SystemExit('falling_film_check FAILED: ' + ', '.join(k for k, v in checks.items() if not v))

if __name__ == '__main__':
    main()
