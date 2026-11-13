"""Wet-wall proxy behind falling water (references/effects/wet-surfaces.md › Wet extent).

A sheet lying on the wall face over the curtain's whole footprint, with ragged ends, runoff fingers and a splash
band fading past both ends. A wetness mask driven by distance to this proxy marks exactly the wall the water wets,
even where the falling sheet stands far off the wall. Returns (V, F) arrays; water.mesh_builders makes the object.
"""
from dataclasses import dataclass

import numpy as np

from materials.water import seeded_noise


@dataclass
class WetParams:
    """Cell size, wall wall_gap_m and splash-band shape of the wet-wall proxy."""
    cell_m: float = .02            # m
    wall_gap_m: float = .002            # m in front of the wall face
    min_splash_height_m: float = .20         # m splash band height range above the pool
    max_splash_height_m: float = .60
    end_decay_m: float = .45          # m e-fold of the splash band past each end
    end_margin_m: float = 1.2          # m considered past each end
    seed: int = 2400


def wet_mask(lip, pool_height_m, params, s, z):
    """True on the wall where it is wet: behind the curtain (ragged ends, runoff fingers) and a splash band."""
    length, top = lip.length_m, lip.origin_m[2]
    S, Z = np.meshgrid(s, z)
    reach = .05 + .25 * seeded_noise.unit_noise(z, params.seed + 3, .05, .30)           # wet edge 5-30 cm past each end, by height
    near_end = np.clip(1.2 - np.abs(np.minimum(s, length - s)) / .35, 0, 1)
    fingers = (seeded_noise.clustered_noise(s, params.seed + 4, .02, .07) > .55) * near_end
    finger_len = (top - pool_height_m) * (.2 + .6 * seeded_noise.unit_noise(s, params.seed + 5, .03, .12))
    behind = (S >= -reach[:, None]) & (S <= length + reach[:, None])
    behind |= (fingers[None, :] > 0) & (top - Z < (finger_len * fingers)[None, :])
    band = params.min_splash_height_m + (params.max_splash_height_m - params.min_splash_height_m) * seeded_noise.unit_noise(s, params.seed, .08, .35)
    band = band * np.exp(-np.maximum(0, np.maximum(-s, s - length)) / params.end_decay_m)   # fades past both ends
    return behind | ((Z - pool_height_m) < band[None, :])


def build_proxy(lip, pool_height_m, params):
    """Vertices (world space) and quads of the wet proxy sheet lying on the wall face."""
    s = np.arange(-params.end_margin_m, lip.length_m + params.end_margin_m, params.cell_m)
    z = np.arange(pool_height_m - .01, lip.origin_m[2] + params.cell_m, params.cell_m)
    keep = wet_mask(lip, pool_height_m, params, s, z)
    S, Z = np.meshgrid(s, z)
    verts = lip.world(S.ravel(), np.full(S.size, params.wall_gap_m), Z.ravel())
    n_rows, n_cols = keep.shape
    first = (np.arange(n_rows - 1)[:, None] * n_cols + np.arange(n_cols - 1)[None, :]).ravel()
    quads = np.c_[first, first + 1, first + n_cols + 1, first + n_cols]
    quads = quads[keep.ravel()[quads].all(axis=1)]
    used = np.unique(quads)
    remap = -np.ones(len(verts), int)
    remap[used] = np.arange(len(used))
    return verts[used], remap[quads]
