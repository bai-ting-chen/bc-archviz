"""Mesh drops; implementation for water.mesh."""
import numpy as np
from materials.water.mesh_objects import from_arrays


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
