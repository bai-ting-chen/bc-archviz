"""Blender objects for the water fields: closed film sheet, string tubes, drop spheroids, generic (V, F) meshes,
and the `velocity` attribute for motion blur (references/materials/water/water-free-falling-film.md §3.9).
"""
import bpy
import numpy as np

G = 9.81


def _finish(me, material, smooth=True):
    if material is not None: me.materials.append(material)
    if smooth and len(me.polygons): me.polygons.foreach_set('use_smooth', np.ones(len(me.polygons), dtype=bool))
    me.update()
    return me


def _object(name, me, collection):
    ob = bpy.data.objects.new(name, me)
    (collection or bpy.context.scene.collection).objects.link(ob)
    return ob


def from_arrays(name, V, F, material=None, collection=None, smooth=True):
    """Object from vertices (N, 3) and a face list (any polygon sizes)."""
    me = bpy.data.meshes.new(name); me.from_pydata(np.asarray(V, float).tolist(), [], [list(map(int, f)) for f in F])
    return _object(name, _finish(me, material, smooth), collection)


def film_sheet(name, front, back, keep, material=None, collection=None):
    """Closed water body from front/back grids (nd, ns, 3): quads fully torn (all corners outside keep) removed.

    Vertex order = front grid then back grid (row-major); faces wound outward for either lip handedness.
    """
    nr, nc = keep.shape; N = nr * nc
    a = (np.arange(nr - 1)[:, None] * nc + np.arange(nc - 1)[None, :]).ravel().astype(np.int32)
    q = np.c_[a, a + 1, a + nc + 1, a + nc]
    q = q[keep.ravel()[q].any(axis=1)]
    edge = np.r_[np.arange(nc), np.arange(2 * nc - 1, N, nc), np.arange(N - 2, N - nc - 1, -1), np.arange(N - 2 * nc, 0, -nc)]
    end = np.roll(edge, -1); side = np.c_[end, edge, edge + N, end + N].astype(np.int32)
    # Winding follows the surface: front faces must point from the back skin to the front skin.
    ds_ = np.diff(front, axis=1)[:-1]; dd_ = np.diff(front, axis=0)[:, :-1]
    if np.sum(np.cross(ds_, dd_) * (front - back)[:-1, :-1]) < 0:
        q = q[:, ::-1]; side = side[:, ::-1]
    loops = np.r_[q.ravel(), (q[:, ::-1] + N).ravel(), side.ravel()]
    count = 2 * len(q) + len(side); coords = np.r_[front.reshape(-1, 3), back.reshape(-1, 3)].astype(np.float32)
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(coords)); me.vertices.foreach_set('co', coords.ravel())
    me.loops.add(len(loops)); me.loops.foreach_set('vertex_index', loops)
    me.polygons.add(count); me.polygons.foreach_set('loop_start', np.arange(count, dtype=np.int32) * 4)
    me.polygons.foreach_set('loop_total', np.full(count, 4, dtype=np.int32))
    return _object(name, _finish(me, material), collection)


def tubes(name, strings, material=None, collection=None, sides=6):
    """Tubes along polylines; each string is an (M, 4) array x, y, z, radius. Ends capped."""
    V = []; F = []; base = 0; ang = np.linspace(0, 2 * np.pi, sides + 1)[:-1]
    for s_ in strings:
        P = s_[:, :3]; R = s_[:, 3]; m = len(P)
        t = np.gradient(P, axis=0); t /= np.linalg.norm(t, axis=1, keepdims=True) + 1e-12
        ref = np.where(np.abs(t[:, :1]) < .9, [[1., 0, 0]], [[0, 1., 0]])
        u = np.cross(t, ref); u /= np.linalg.norm(u, axis=1, keepdims=True) + 1e-12; w = np.cross(t, u)
        ring = P[:, None] + R[:, None, None] * (np.cos(ang)[None, :, None] * u[:, None] + np.sin(ang)[None, :, None] * w[:, None])
        V.append(ring.reshape(-1, 3))
        for i in range(m - 1):
            for j in range(sides):
                a0 = base + i * sides + j; a1 = base + i * sides + (j + 1) % sides
                F.append([a0, a1, a1 + sides, a0 + sides])
        F.append(list(range(base + sides - 1, base - 1, -1))); F.append(list(range(base + (m - 1) * sides, base + m * sides)))
        base += m * sides
    return from_arrays(name, np.concatenate(V) if V else np.zeros((0, 3)), F, material, collection)


def spheroids(name, drops, material=None, collection=None):
    """Low-poly drops, (N, 5) = x, y, z, diameter, stretch along z."""
    u = np.linspace(0, np.pi, 6)[1:-1]; w = np.linspace(0, 2 * np.pi, 9)[:-1]
    unit = np.r_[[[0, 0, 1]], [[np.sin(a) * np.cos(b), np.sin(a) * np.sin(b), np.cos(a)] for a in u for b in w], [[0, 0, -1]]]
    nu = len(unit); tri = [[0, 1 + k, 1 + (k + 1) % 8] for k in range(8)]
    for r in range(len(u) - 1):
        for k in range(8):
            a0 = 1 + r * 8 + k; a1 = 1 + r * 8 + (k + 1) % 8; tri += [[a0, a0 + 8, a1 + 8], [a0, a1 + 8, a1]]
    last = 1 + (len(u) - 1) * 8; tri += [[last + k, nu - 1, last + (k + 1) % 8] for k in range(8)]
    tri = np.array(tri)
    drops = np.asarray(drops)
    if not len(drops): return from_arrays(name, np.zeros((0, 3)), [], material, collection)
    scale = np.c_[drops[:, 3] / 2, drops[:, 3] / 2, drops[:, 3] / 2 * drops[:, 4]]
    V = (unit[None] * scale[:, None] + drops[:, None, :3]).reshape(-1, 3)
    F = (tri[None] + (np.arange(len(drops)) * nu)[:, None, None]).reshape(-1, 3)
    return from_arrays(name, V, F, material, collection)


def set_velocity(ob, vel):
    """Store a per-vertex `velocity` (m/s) and enable deformation motion blur on the object."""
    me = ob.data
    a = me.attributes.get('velocity') or me.attributes.new('velocity', 'FLOAT_VECTOR', 'POINT')
    a.data.foreach_set('vector', np.ascontiguousarray(vel, dtype=np.float32).ravel())
    ob.cycles.use_motion_blur = True; ob.cycles.use_deform_motion = True


def film_velocity(front, back, lip_z, v0=.35):
    """Velocity for film_sheet's vertex order: U(d) = sqrt(v0^2 + 2 g d) along the local fall direction (row diffs)."""
    out = []
    for P in (front, back):
        t = np.gradient(P, axis=0); t /= np.linalg.norm(t, axis=-1, keepdims=True) + 1e-12
        out.append((t * np.sqrt(v0 ** 2 + 2 * G * np.clip(lip_z - P[..., 2], 0, None))[..., None]).reshape(-1, 3))
    return np.r_[out[0], out[1]]


def falling_velocity(ob, lip_z, v0=.35):
    """Straight-down velocity at the local fall speed for every vertex of an object (strings, drops)."""
    me = ob.data; c = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', c); c = c.reshape(-1, 3)
    U = np.sqrt(v0 ** 2 + 2 * G * np.clip(lip_z - c[:, 2], 0, None))
    set_velocity(ob, np.c_[np.zeros_like(U), np.zeros_like(U), -U])


def thin_wall_copy(material, name):
    """Copy of a water material with Principled Thin Wall on: glints and rims, straight transmission (open shells)."""
    m = material.copy(); m.name = name
    for nd in m.node_tree.nodes:
        if nd.type == 'BSDF_PRINCIPLED': nd.inputs['Thin Wall'].default_value = True
    return m
