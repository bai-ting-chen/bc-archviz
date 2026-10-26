"""Wet-wall proxy behind falling water (references/effects/wet-surfaces.md › Wet wall behind falling water).

A sheet lying on the wall face over the curtain's whole footprint, with ragged ends, runoff fingers and a splash
band fading past both ends. A wetness mask driven by distance to this proxy marks exactly the wall the water wets,
even where the falling sheet stands far off the wall. Returns (V, F) arrays; water.mesh makes the object.
"""
from dataclasses import dataclass

import numpy as np

from materials.water import noise


@dataclass
class WetParams:
    """Cell size, wall gap and splash-band shape of the wet-wall proxy."""
    cell: float = .02            # m
    gap: float = .002            # m in front of the wall face
    band_lo: float = .20         # m splash band height range above the pool
    band_hi: float = .60
    beyond: float = .45          # m e-fold of the splash band past each end
    margin: float = 1.2          # m considered past each end
    seed: int = 2400


def wet_mask(lip, pool_z, p, s, z):
    """True on the wall where it is wet: behind the curtain (ragged ends, runoff fingers) and a splash band."""
    length, top = lip.length, lip.origin[2]
    S, Z = np.meshgrid(s, z)
    reach = .05 + .25 * noise.unit(z, p.seed + 3, .05, .30)           # wet edge 5-30 cm past each end, by height
    near_end = np.clip(1.2 - np.abs(np.minimum(s, length - s)) / .35, 0, 1)
    fingers = (noise.clustered(s, p.seed + 4, .02, .07) > .55) * near_end
    finger_len = (top - pool_z) * (.2 + .6 * noise.unit(s, p.seed + 5, .03, .12))
    behind = (S >= -reach[:, None]) & (S <= length + reach[:, None])
    behind |= (fingers[None, :] > 0) & (top - Z < (finger_len * fingers)[None, :])
    band = p.band_lo + (p.band_hi - p.band_lo) * noise.unit(s, p.seed, .08, .35)
    band = band * np.exp(-np.maximum(0, np.maximum(-s, s - length)) / p.beyond)   # fades past both ends
    return behind | ((Z - pool_z) < band[None, :])


def proxy(lip, pool_z, p):
    """Vertices (world space) and quads of the wet proxy sheet lying on the wall face."""
    s = np.arange(-p.margin, lip.length + p.margin, p.cell)
    z = np.arange(pool_z - .01, lip.origin[2] + p.cell, p.cell)
    keep = wet_mask(lip, pool_z, p, s, z)
    S, Z = np.meshgrid(s, z)
    verts = lip.world(S.ravel(), np.full(S.size, p.gap), Z.ravel())
    n_rows, n_cols = keep.shape
    first = (np.arange(n_rows - 1)[:, None] * n_cols + np.arange(n_cols - 1)[None, :]).ravel()
    quads = np.c_[first, first + 1, first + n_cols + 1, first + n_cols]
    quads = quads[keep.ravel()[quads].all(axis=1)]
    used = np.unique(quads)
    remap = -np.ones(len(verts), int)
    remap[used] = np.arange(len(used))
    return verts[used], remap[quads]
