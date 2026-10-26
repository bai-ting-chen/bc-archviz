"""Photon geometry; implementation for caustic_photons."""
import json
import numpy as np
from effects.caustics.photon_grid import SURFACES, GRID


def export_geometry(path, surfaces=SURFACES, axis=(0.0, 0.0), grid=None):
    """`surfaces` {object: eta}; `grid` overrides GRID (receiver plane x0, y0, size, res, z) and
    is stored with the geometry so the tracer, bake and material all use the same one."""
    import bpy
    if grid:
        GRID.update(grid)
    V, F, S, E = [], [], [], []
    off = 0
    for sid, (name, eta) in enumerate(surfaces.items()):
        ob = bpy.data.objects[name]
        mw = ob.matrix_world
        V += [tuple(mw @ v.co) for v in ob.data.vertices]
        for p in ob.data.polygons:
            F.append([off + i for i in p.vertices])
            S.append(sid)
        E.append(eta)
        off += len(ob.data.vertices)
    np.savez(path, verts=np.array(V), faces=np.array(F, dtype=object), surf=np.array(S),
             eta=np.array(E), axis=np.array(axis), grid=json.dumps(GRID), allow_pickle=True)
    return {"verts": len(V), "faces": len(F)}
