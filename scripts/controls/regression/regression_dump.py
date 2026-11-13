"""Run Blender helper cases and write their graph and geometry baseline."""

import os as _os, sys as _sys
_sys.path.append(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import controls_import_paths  # noqa: E402,F401 -- every controls topic folder on sys.path
import json
import sys
import traceback
import bpy
from regression_graph import snapshot
from regression_rig import evaluated_positions, lazy_modules
from regression_cases import CASES

def dump(SRC, HERE, OUT):
    """Dump every original helper case with one project-root state."""
    sys.path.insert(0, SRC)
    def B(fn):
        def run():
            # Each dump uses a fresh Blender process; preserve one project-root state.
            import core.archviz as a
            a.set_project(HERE)
            return fn()
        return run
    res = {}
    for k, f in CASES.items():
        bpy.ops.wm.read_homefile(use_empty=True)
        try:
            B(lambda: f(lazy_modules()))()
            res[k] = snapshot()
        except Exception:
            res[k] = {"ERROR": traceback.format_exc().splitlines()[-1]}
    for k, fn in (("eval edge_wear", lambda m: evaluated_positions(m['effects.wear'].edge_wear_group(), m['effects.wear'].add_edge_wear)),
                  ("eval wood_wear", lambda m: evaluated_positions(m['effects.wear'].edge_wear_group(**m['materials.wood.wood'].WOOD_CHIPS), m['effects.wear'].add_edge_wear))):
        bpy.ops.wm.read_homefile(use_empty=True)
        try:
            res[k] = B(lambda: fn(lazy_modules()))()
        except Exception:
            res[k] = {"ERROR": traceback.format_exc().splitlines()[-1]}
    json.dump(res, open(OUT, "w"), indent=1, sort_keys=True)
    print("DUMPED", len(res), sum(1 for v in res.values() if "ERROR" in v), "errors")

