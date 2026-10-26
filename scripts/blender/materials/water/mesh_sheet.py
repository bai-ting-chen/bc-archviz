"""Mesh sheet; implementation for water.mesh."""
import bpy
import numpy as np
from materials.water.mesh_objects import _finish, _link


def _grid_quads(n_rows, n_cols):
    """Quads (a, a+1, a+cols+1, a+cols) of a row-major grid."""
    first = (np.arange(n_rows - 1)[:, None] * n_cols + np.arange(n_cols - 1)[None, :]).ravel().astype(np.int32)
    return np.c_[first, first + 1, first + n_cols + 1, first + n_cols]


def _border_loop(n_rows, n_cols):
    """Grid indices round the outer border, in order."""
    n = n_rows * n_cols
    return np.r_[np.arange(n_cols), np.arange(2 * n_cols - 1, n, n_cols),
                 np.arange(n - 2, n - n_cols - 1, -1), np.arange(n - 2 * n_cols, 0, -n_cols)]


def film_sheet(name, front, back, keep, material=None, collection=None):
    """Closed water body from front/back grids (nd, ns, 3); quads whose four corners are all torn are removed.

    Vertex order = front grid then back grid (row-major), which water.motion.film_velocity relies on.
    Faces are wound outward for either lip handedness (front faces point from the back skin to the front skin).
    """
    n_rows, n_cols = keep.shape
    n = n_rows * n_cols
    quads = _grid_quads(n_rows, n_cols)
    quads = quads[keep.ravel()[quads].any(axis=1)]
    border = _border_loop(n_rows, n_cols)
    nxt = np.roll(border, -1)
    sides = np.c_[nxt, border, border + n, nxt + n].astype(np.int32)
    along_s = np.diff(front, axis=1)[:-1]
    along_d = np.diff(front, axis=0)[:, :-1]
    if np.sum(np.cross(along_s, along_d) * (front - back)[:-1, :-1]) < 0:
        quads = quads[:, ::-1]
        sides = sides[:, ::-1]
    loops = np.r_[quads.ravel(), (quads[:, ::-1] + n).ravel(), sides.ravel()]
    count = 2 * len(quads) + len(sides)
    coords = np.r_[front.reshape(-1, 3), back.reshape(-1, 3)].astype(np.float32)
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(coords))
    me.vertices.foreach_set('co', coords.ravel())
    me.loops.add(len(loops))
    me.loops.foreach_set('vertex_index', loops)
    me.polygons.add(count)
    me.polygons.foreach_set('loop_start', np.arange(count, dtype=np.int32) * 4)
    me.polygons.foreach_set('loop_total', np.full(count, 4, dtype=np.int32))
    return _link(name, _finish(me, material), collection)
