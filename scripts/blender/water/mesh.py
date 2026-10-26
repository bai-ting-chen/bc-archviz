"""Blender mesh objects for the water fields: closed film sheet, string tubes, drop spheroids and generic (V, F)
meshes. Geometry only: velocities live in water.motion, materials in water.shading.
"""
import bpy
import numpy as np


def _finish(me, material, smooth=True):
    if material is not None:
        me.materials.append(material)
    if smooth and len(me.polygons):
        me.polygons.foreach_set('use_smooth', np.ones(len(me.polygons), dtype=bool))
    me.update()
    return me


def _link(name, me, collection):
    ob = bpy.data.objects.new(name, me)
    (collection or bpy.context.scene.collection).objects.link(ob)
    return ob


def from_arrays(name, verts, faces, material=None, collection=None, smooth=True):
    """Object from vertices (N, 3) and a face list (any polygon sizes)."""
    me = bpy.data.meshes.new(name)
    me.from_pydata(np.asarray(verts, float).tolist(), [], [list(map(int, f)) for f in faces])
    return _link(name, _finish(me, material, smooth), collection)


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


def _tube_rings(points, radius, sides):
    """Ring vertices (M, sides, 3) round a polyline, perpendicular to its tangent."""
    tangent = np.gradient(points, axis=0)
    tangent /= np.linalg.norm(tangent, axis=1, keepdims=True) + 1e-12
    reference = np.where(np.abs(tangent[:, :1]) < .9, [[1., 0, 0]], [[0, 1., 0]])
    u = np.cross(tangent, reference)
    u /= np.linalg.norm(u, axis=1, keepdims=True) + 1e-12
    w = np.cross(tangent, u)
    angle = np.linspace(0, 2 * np.pi, sides + 1)[:-1]
    offset = np.cos(angle)[None, :, None] * u[:, None] + np.sin(angle)[None, :, None] * w[:, None]
    return points[:, None] + radius[:, None, None] * offset


def tubes(name, strings, material=None, collection=None, sides=6):
    """Capped tubes along polylines; each string is an (M, 4) array x, y, z, radius."""
    verts, faces, base = [], [], 0
    for string in strings:
        rings = _tube_rings(string[:, :3], string[:, 3], sides)
        m = len(rings)
        verts.append(rings.reshape(-1, 3))
        for i in range(m - 1):
            for j in range(sides):
                a0 = base + i * sides + j
                a1 = base + i * sides + (j + 1) % sides
                faces.append([a0, a1, a1 + sides, a0 + sides])
        faces.append(list(range(base + sides - 1, base - 1, -1)))                # start cap
        faces.append(list(range(base + (m - 1) * sides, base + m * sides)))       # end cap
        base += m * sides
    return from_arrays(name, np.concatenate(verts) if verts else np.zeros((0, 3)), faces, material, collection)


def _unit_sphere():
    """Low-poly unit sphere (4 rings x 8 segments + poles): vertices and triangles."""
    polar = np.linspace(0, np.pi, 6)[1:-1]
    azimuth = np.linspace(0, 2 * np.pi, 9)[:-1]
    ring = [[np.sin(a) * np.cos(b), np.sin(a) * np.sin(b), np.cos(a)] for a in polar for b in azimuth]
    unit = np.r_[[[0, 0, 1]], ring, [[0, 0, -1]]]
    tris = [[0, 1 + k, 1 + (k + 1) % 8] for k in range(8)]
    for r in range(len(polar) - 1):
        for k in range(8):
            a0 = 1 + r * 8 + k
            a1 = 1 + r * 8 + (k + 1) % 8
            tris += [[a0, a0 + 8, a1 + 8], [a0, a1 + 8, a1]]
    last = 1 + (len(polar) - 1) * 8
    tris += [[last + k, len(unit) - 1, last + (k + 1) % 8] for k in range(8)]
    return unit, np.array(tris)


def spheroids(name, drops, material=None, collection=None):
    """Low-poly drops from an (N, 5) array x, y, z, diameter, stretch along z."""
    drops = np.asarray(drops)
    if not len(drops):
        return from_arrays(name, np.zeros((0, 3)), [], material, collection)
    unit, tris = _unit_sphere()
    half = drops[:, 3] / 2
    scale = np.c_[half, half, half * drops[:, 4]]
    verts = (unit[None] * scale[:, None] + drops[:, None, :3]).reshape(-1, 3)
    faces = (tris[None] + (np.arange(len(drops)) * len(unit))[:, None, None]).reshape(-1, 3)
    return from_arrays(name, verts, faces, material, collection)
