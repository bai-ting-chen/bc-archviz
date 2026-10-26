"""Mesh tubes; implementation for water.mesh."""
import numpy as np
from materials.water.mesh_objects import from_arrays


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
