"""Ballistic carrier of a water sheet thrown off a straight lip (references/materials/water-free-falling-film.md §3.1-3.3).

Local coordinates: s = metres along the lip from its start (0..length), d = drop below the lip (0..drop).
World point = origin + s*along + throw(s, d)*out - d*Z. Water leaves horizontally, so every section is a
parabola with its vertex at the lip: throw = v0 * sqrt(2 d / g), v0 = (g q)^(1/3) from the local flow q.
"""
from dataclasses import dataclass

import numpy as np

from . import noise

G = 9.81


@dataclass
class Lip:
    """A straight horizontal lip. along/out are horizontal unit vectors (out = away from the wall)."""
    origin: tuple            # world point at s = 0, on the lip edge (wall face)
    along: tuple             # direction of increasing s
    out: tuple               # horizontal direction the water is thrown
    length: float            # m
    drop: float              # m, lip to the receiving surface

    def __post_init__(self):
        self.origin = np.asarray(self.origin, float)
        a = np.asarray(self.along, float); a[2] = 0; self.along = a / np.linalg.norm(a)
        o = np.asarray(self.out, float); o[2] = 0; o -= self.along * (o @ self.along)
        self.out = o / np.linalg.norm(o)

    def world(self, s, o, z):
        """World points from along-lip s, outward distance o (from the wall face) and absolute z (arrays)."""
        s, o, z = np.broadcast_arrays(s, o, z)
        p = self.origin[:2] + s[..., None] * self.along[:2] + o[..., None] * self.out[:2]
        return np.concatenate([p, z[..., None]], axis=-1)

    def local(self, xyz):
        """Along-lip s and outward o of world points (..., 3)."""
        rel = np.asarray(xyz)[..., :2] - self.origin[:2]
        return rel @ self.along[:2], rel @ self.out[:2]


@dataclass
class Flow:
    """Launch speed and per-stream flow (§3.1-3.2). Seeds make every layer repeatable."""
    v0: float = .32               # m/s mean launch speed (throw at the foot ~ v0*sqrt(2H/g))
    v0_var: float = .40           # +- fraction, two smooth scales along the lip
    stream_amp: float = .40       # +- fraction of per-stream flow m(s)
    stream_lo: float = .04        # m, stream width range
    stream_hi: float = .25
    drift: float = .04            # m, slow sideways drift of the stream pattern down the fall
    seed: int = 1101


def _v0_mean(flow, s):
    return flow.v0 * (1 + flow.v0_var * (.7 * noise.clustered(s, flow.seed, 1.8, 3.2)
                                         + .3 * noise.clustered(s, flow.seed + 1, .3, .7)))


def stream_factor(flow, s, d):
    """1 + m: per-stream flow multiplier, constant down each stream apart from a slow drift."""
    shift = flow.drift * noise.clustered(d, flow.seed + 2, .5, 1.2)
    return 1 + flow.stream_amp * noise.clustered(s - shift, flow.seed + 3, flow.stream_lo, flow.stream_hi)


def flux(flow, s, d):
    """Flow per metre width q (m^2/s) at (s, d)."""
    return _v0_mean(flow, s) ** 3 / G * stream_factor(flow, s, d)


def launch(flow, s, d):
    """Local launch speed v0 = (g q)^(1/3), m/s."""
    return np.cbrt(G * flux(flow, s, d))


def speed(flow, s, d):
    """Sheet speed U = sqrt(v0^2 + 2 g d), m/s."""
    v = launch(flow, s, d)
    return np.sqrt(v * v + 2 * G * np.maximum(d, 0))


def thickness(flow, s, d):
    """Sheet thickness h = q / U, m."""
    return flux(flow, s, d) / speed(flow, s, d)


def throw(flow, s, d):
    """Outward distance of the sheet mid-surface from the wall face, m."""
    return launch(flow, s, d) * np.sqrt(2 * np.maximum(d, 0) / G)


def effective_depth(flow, s, d, k=.5, d_ref=.15):
    """Fall-time stretch coordinate v_eff = d_ref + int (U(d_ref)/U)^k (unchanged above d_ref), m."""
    v = _v0_mean(flow, s); ref = v * v + 2 * G * d_ref; d = np.asarray(d, float)
    tail = d_ref + ref ** (k / 2) * ((v * v + 2 * G * d) ** (1 - k / 2) - ref ** (1 - k / 2)) / (G * (2 - k))
    return np.where(d <= d_ref, d, tail)


def carrier_grid(lip, flow, s, d):
    """Mid-surface points (nd, ns, 3) and unit normals pointing away from the wall, on a grid s x d."""
    S, D = np.meshgrid(s, d)
    P = lip.world(S, throw(flow, S, D), lip.origin[2] - D)
    ts = np.gradient(P, axis=1); td = np.gradient(P, axis=0)
    n = np.cross(td, ts); n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-12
    n *= np.where(n[..., :2] @ lip.out[:2] < 0, -1., 1.)[..., None]      # always away from the wall
    return S, D, P, n


def landing(lip, flow, s):
    """Landing line on the receiving surface: world points (len(s), 3)."""
    s = np.asarray(s, float); d = np.full_like(s, lip.drop)
    return lip.world(s, throw(flow, s, d), np.full_like(s, lip.origin[2] - lip.drop))
