"""Shared UV distance, continuity and orientation measurements."""

import os as _os
import sys as _sys
_CONTROLS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in [_CONTROLS] + [_os.path.join(_CONTROLS, _t) for _t in ('archviz', 'tile', 'material', 'effects', 'water', 'lighting', 'environment', 'regression')]:
    if _d not in _sys.path:
        _sys.path.append(_d)
import bpy
def uv_vs_world(ob, uvname, metric):
    """Max |uv edge length - metric edge length| over all face edges, metres."""
    me = ob.data; uvl = me.uv_layers[uvname].data
    worst = 0.0
    for poly in me.polygons:
        li = list(poly.loop_indices)
        for a, b in zip(li, li[1:] + li[:1]):
            va = ob.matrix_world @ me.vertices[me.loops[a].vertex_index].co
            vb = ob.matrix_world @ me.vertices[me.loops[b].vertex_index].co
            du = (uvl[a].uv - uvl[b].uv).length
            worst = max(worst, abs(du - metric(va, vb)))
    return worst

def continuity(ob, name, cut_vertices=(), *, fails):
    """Check per-vertex loop UV continuity except at explicitly identified cut vertices."""
    samples = {}
    for loop in ob.data.loops:
        samples.setdefault(loop.vertex_index, []).append(ob.data.uv_layers[name].data[loop.index].uv.copy())
    for vertex, values in samples.items():
        for axis in (0, 1):
            if axis == 0 and vertex in cut_vertices:
                continue
            if max(v[axis] for v in values) - min(v[axis] for v in values) >= 1e-6:
                fails.append(f"{ob.name}: vertex {vertex} axis {axis} discontinuity")


def orientation(ob, name, u_axis, v_axis, *, fails):
    """Check signed UV increments against the requested world basis on every edge."""
    from mathutils import Vector
    u_axis, v_axis = Vector(u_axis), Vector(v_axis)
    uv = ob.data.uv_layers[name].data
    for poly in ob.data.polygons:
        li = list(poly.loop_indices)
        for a, b in zip(li, li[1:] + li[:1]):
            delta = (ob.matrix_world @ ob.data.vertices[ob.data.loops[b].vertex_index].co
                     - ob.matrix_world @ ob.data.vertices[ob.data.loops[a].vertex_index].co)
            duv = uv[b].uv - uv[a].uv
            if abs(duv.x - delta.dot(u_axis)) > 1e-5 or abs(duv.y - delta.dot(v_axis)) > 1e-5:
                fails.append(f"{ob.name}: orientation err")
                return
