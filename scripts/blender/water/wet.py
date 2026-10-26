"""Wet-wall proxy behind falling water (references/materials/wet-surfaces.md › Wet wall behind falling water).

A sheet lying on the wall face over the curtain's whole footprint, with ragged ends, runoff fingers and a splash
band fading past both ends. A wetness mask driven by distance to this proxy marks exactly the wall the water wets,
even where the falling sheet stands far off the wall. Returns (V, F) arrays; water.mesh makes the object.
"""
from dataclasses import dataclass

import numpy as np

from . import noise


@dataclass
class WetParams:
    cell: float = .02            # m
    gap: float = .002            # m in front of the wall face
    band_lo: float = .20         # m splash band height range above the pool
    band_hi: float = .60
    beyond: float = .45          # m e-fold of the splash band past each end
    margin: float = 1.2          # m considered past each end
    seed: int = 2400


def proxy(lip, pool_z, p):
    """Vertices and quads of the wet proxy sheet on the wall face (world space)."""
    L = lip.length; top = lip.origin[2]
    s = np.arange(-p.margin, L + p.margin, p.cell); z = np.arange(pool_z - .01, top + p.cell, p.cell)
    S, Z = np.meshgrid(s, z)
    reach = .05 + .25 * noise.unit(z, p.seed + 3, .05, .30)
    near_end = np.clip(1.2 - np.abs(np.minimum(s, L - s)) / .35, 0, 1)
    fingers = (noise.clustered(s, p.seed + 4, .02, .07) > .55) * near_end
    finger_len = (top - pool_z) * (.2 + .6 * noise.unit(s, p.seed + 5, .03, .12))
    behind = (S >= -reach[:, None]) & (S <= L + reach[:, None])
    behind |= (fingers[None, :] > 0) & (top - Z < (finger_len * fingers)[None, :])
    band = p.band_lo + (p.band_hi - p.band_lo) * noise.unit(s, p.seed, .08, .35)
    band = band * np.exp(-np.maximum(0, np.maximum(-s, s - L)) / p.beyond)
    keep = behind | ((Z - pool_z) < band[None, :])
    nr, nc = keep.shape
    V = lip.world(S.ravel(), np.full(S.size, p.gap), Z.ravel())
    a = (np.arange(nr - 1)[:, None] * nc + np.arange(nc - 1)[None, :]).ravel()
    q = np.c_[a, a + 1, a + nc + 1, a + nc]; q = q[keep.ravel()[q].all(axis=1)]
    used = np.unique(q); remap = -np.ones(len(V), int); remap[used] = np.arange(len(used))
    return V[used], remap[q]
