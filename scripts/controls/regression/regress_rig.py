"""Helper regression evaluated-geometry and lazy-module fixtures."""

import os as _os
import sys as _sys
_CONTROLS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in [_CONTROLS] + [_os.path.join(_CONTROLS, _t) for _t in ('archviz', 'tile', 'material', 'effects', 'water', 'lighting', 'environment', 'regression')]:
    if _d not in _sys.path:
        _sys.path.append(_d)
import bpy

def eval_positions(group, add):
    """Record evaluated positions after adding a wear group to a diced cube."""
    bpy.ops.mesh.primitive_cube_add(size=0.4)
    ob = bpy.context.object
    import effects.edge_wear as wear
    wear.dice(ob, 0.05)
    add(ob, group)
    dg = bpy.context.evaluated_depsgraph_get()
    me = ob.evaluated_get(dg).to_mesh()
    pts = sorted((round(v.co.x, 7), round(v.co.y, 7), round(v.co.z, 7)) for v in me.vertices)
    return {"n": len(pts), "sum": [round(sum(p[i] for p in pts), 6) for i in range(3)], "head": pts[:5]}

def mods():
    """Import only modules needed by a case; do not let an unrelated import fail every case."""
    import importlib
    class Modules(dict):
        def __missing__(self, name):
            self[name] = importlib.import_module(name)
            return self[name]
    return Modules()
