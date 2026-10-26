"""Ballistic carrier of a water sheet thrown off a straight lip
(references/materials/water/water-free-falling-film.md §3.1-3.3).

Sheet coordinates: s = metres along the lip from its start (0..length), d = drop below the lip (0..drop).
World point = origin + s*along + throw(s, d)*out - d*Z. Water leaves horizontally, so every section is a
parabola with its vertex at the lip: throw = v0 * sqrt(2 d / g), with v0 = (g q)^(1/3) from the local flow q.
Lip-local coordinates used by the foot and the pool: s along the lip, o outward from the wall face.
"""
from dataclasses import dataclass

import numpy as np

from . import noise

G = 9.81


@dataclass
class Lip:
    """A straight horizontal lip: origin on the wall face, along = increasing s, out = direction the water is thrown."""
    origin: tuple            # world point at s = 0 on the lip edge
    along: tuple             # direction of increasing s
    out: tuple               # horizontal direction away from the wall
    length: float            # m
    drop: float              # m from the lip to the receiving surface

    def __post_init__(self):
        self.origin = np.asarray(self.origin, float)
        along = np.asarray(self.along, float)
        along[2] = 0
        self.along = along / np.linalg.norm(along)
        out = np.asarray(self.out, float)
        out[2] = 0
        out -= self.along * (out @ self.along)                         # make it exactly horizontal-perpendicular
        self.out = out / np.linalg.norm(out)

    def world(self, s, o, z):
        """World points from along-lip s, outward distance o and absolute height z (broadcast arrays)."""
        s, o, z = np.broadcast_arrays(s, o, z)
        xy = self.origin[:2] + s[..., None] * self.along[:2] + o[..., None] * self.out[:2]
        return np.concatenate([xy, z[..., None]], axis=-1)

    def local(self, xyz):
        """Along-lip s and outward o of world points (..., 3)."""
        rel = np.asarray(xyz)[..., :2] - self.origin[:2]
        return rel @ self.along[:2], rel @ self.out[:2]


@dataclass
class Flow:
    """Launch speed and per-stream flow (§3.1-3.2); seeds make every layer repeatable."""
    v0: float = .32               # m/s mean launch speed (throw at the foot ~ v0 * sqrt(2H/g))
    v0_var: float = .40           # +- fraction, two smooth scales along the lip
    stream_amp: float = .40       # +- fraction of per-stream flow
    stream_lo: float = .04        # m stream width range
    stream_hi: float = .25
    drift: float = .04            # m slow sideways drift of the stream pattern down the fall
    seed: int = 1101


def mean_launch(flow, s):
    """Launch speed before per-stream variation: v0 x (1 +- v0_var) at two smooth scales (metres and decimetres)."""
    variation = (.7 * noise.clustered(s, flow.seed, 1.8, 3.2)
                 + .3 * noise.clustered(s, flow.seed + 1, .3, .7))
    return flow.v0 * (1 + flow.v0_var * variation)


def stream_factor(flow, s, d):
    """Per-stream flow multiplier 1 + m, constant down each stream apart from a slow drift."""
    shift = flow.drift * noise.clustered(d, flow.seed + 2, .5, 1.2)
    return 1 + flow.stream_amp * noise.clustered(s - shift, flow.seed + 3, flow.stream_lo, flow.stream_hi)


def flux(flow, s, d):
    """Flow per metre width q (m^2/s) at (s, d)."""
    return mean_launch(flow, s) ** 3 / G * stream_factor(flow, s, d)


def launch(flow, s, d):
    """Local launch speed v0 = (g q)^(1/3), m/s."""
    return np.cbrt(G * flux(flow, s, d))


def speed(flow, s, d):
    """Sheet speed U = sqrt(v0^2 + 2 g d), m/s."""
    v0 = launch(flow, s, d)
    return np.sqrt(v0 * v0 + 2 * G * np.maximum(d, 0))


def thickness(flow, s, d):
    """Sheet thickness h = q / U, m."""
    return flux(flow, s, d) / speed(flow, s, d)


def throw(flow, s, d):
    """Outward distance of the sheet mid-surface from the wall face, m."""
    return launch(flow, s, d) * np.sqrt(2 * np.maximum(d, 0) / G)


def effective_depth(flow, s, d, k=.5, d_ref=.15):
    """Fall-time stretch coordinate v = d_ref + integral of (U(d_ref)/U)^k, unchanged above d_ref; metres."""
    v0 = mean_launch(flow, s)
    ref = v0 * v0 + 2 * G * d_ref
    d = np.asarray(d, float)
    tail = d_ref + ref ** (k / 2) * ((v0 * v0 + 2 * G * d) ** (1 - k / 2) - ref ** (1 - k / 2)) / (G * (2 - k))
    return np.where(d <= d_ref, d, tail)


def carrier_grid(lip, flow, s, d):
    """Grids S, D (nd, ns), mid-surface points P and unit normals pointing away from the wall (nd, ns, 3)."""
    S, D = np.meshgrid(s, d)
    P = lip.world(S, throw(flow, S, D), lip.origin[2] - D)
    normal = np.cross(np.gradient(P, axis=0), np.gradient(P, axis=1))
    normal /= np.linalg.norm(normal, axis=-1, keepdims=True) + 1e-12
    normal *= np.where(normal[..., :2] @ lip.out[:2] < 0, -1., 1.)[..., None]
    return S, D, P, normal


def landing(lip, flow, s):
    """Landing line on the receiving surface: world points (len(s), 3)."""
    s = np.asarray(s, float)
    d = np.full_like(s, lip.drop)
    return lip.world(s, throw(flow, s, d), np.full_like(s, lip.origin[2] - lip.drop))
