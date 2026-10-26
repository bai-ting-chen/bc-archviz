"""Run Blender helper cases and write their graph and geometry baseline."""

import os as _os
import sys as _sys
_CONTROLS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in [_CONTROLS] + [_os.path.join(_CONTROLS, _t) for _t in ('archviz', 'tile', 'material', 'effects', 'water', 'lighting', 'environment', 'regression')]:
    if _d not in _sys.path:
        _sys.path.append(_d)
import json
import sys
import traceback
import bpy
from regress_graph import snapshot
from regress_rig import eval_positions, mods
from regress_cases import CASES

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
            B(lambda: f(mods()))()
            res[k] = snapshot()
        except Exception:
            res[k] = {"ERROR": traceback.format_exc().splitlines()[-1]}
    for k, fn in (("eval edge_wear", lambda m: eval_positions(m['effects.edge_wear'].edge_wear_group(), m['effects.edge_wear'].add_edge_wear)),
                  ("eval wood_wear", lambda m: eval_positions(m['materials.wood.wood_wear'].wood_wear_group(), m['effects.edge_wear'].add_edge_wear))):
        bpy.ops.wm.read_homefile(use_empty=True)
        try:
            res[k] = B(lambda: fn(mods()))()
        except Exception:
            res[k] = {"ERROR": traceback.format_exc().splitlines()[-1]}
    json.dump(res, open(OUT, "w"), indent=1, sort_keys=True)
    print("DUMPED", len(res), sum(1 for v in res.values() if "ERROR" in v), "errors")

