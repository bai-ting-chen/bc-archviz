"""Ballistic carrier of a water sheet thrown off a straight lip
(references/materials/water/water-free-falling-film.md §3.1-3.3).

Sheet coordinates: s = metres along the lip from its start (0..length), d = drop below the lip (0..drop).
World point = origin + s*along + throw(s, d)*out - d*Z. Water leaves horizontally, so every section is a
parabola with its vertex at the lip: throw = v0 * sqrt(2 d / g), with v0 = (g q)^(1/3) from the local flow q.
Lip-local coordinates used by the foot and the pool: s along the lip, o outward from the wall face.
"""
from dataclasses import dataclass

import numpy as np

from materials.water import seeded_noise

GRAVITY_M_S2 = 9.81


@dataclass
class LaunchLip:
    """A straight horizontal lip: origin_m on the wall face, along_axis = increasing s, outward_axis = direction the water is thrown."""
    origin_m: tuple            # world point at s = 0 on the lip edge
    along_axis: tuple             # direction of increasing s
    outward_axis: tuple               # horizontal direction away from the wall
    length_m: float            # m
    drop_m: float              # m from the lip to the receiving surface

    def __post_init__(self):
        self.origin_m = np.asarray(self.origin_m, float)
        along = np.asarray(self.along_axis, float)
        along[2] = 0
        self.along_axis = along / np.linalg.norm(along)
        out = np.asarray(self.outward_axis, float)
        out[2] = 0
        out -= self.along_axis * (out @ self.along_axis)                         # make it exactly horizontal-perpendicular
        self.outward_axis = out / np.linalg.norm(out)

    def world(self, s, o, z):
        """World points from along-lip s, outward distance o and absolute height z (broadcast arrays)."""
        s, o, z = np.broadcast_arrays(s, o, z)
        xy = self.origin_m[:2] + s[..., None] * self.along_axis[:2] + o[..., None] * self.outward_axis[:2]
        return np.concatenate([xy, z[..., None]], axis=-1)

    def local(self, xyz):
        """Along-lip s and outward o of world points (..., 3)."""
        rel = np.asarray(xyz)[..., :2] - self.origin_m[:2]
        return rel @ self.along_axis[:2], rel @ self.outward_axis[:2]


@dataclass
class SheetFlow:
    """Launch speed and per-stream flow (§3.1-3.2); seeds make every layer repeatable."""
    launch_speed_m_s: float = .32               # m/s mean launch speed (throw at the foot ~ v0 * sqrt(2H/g))
    launch_speed_variation: float = .40           # +- fraction, two smooth scales along the lip
    stream_variation: float = .40       # +- fraction of per-stream flow
    min_stream_width_m: float = .04        # m stream width range
    max_stream_width_m: float = .25
    stream_drift_m: float = .04            # m slow sideways drift of the stream pattern down the fall
    seed: int = 1101


def mean_launch_speed_m_s(flow, s):
    """Launch speed before per-stream variation: v0 x (1 +- v0_var) at two smooth scales (metres and decimetres)."""
    variation = (.7 * seeded_noise.clustered_noise(s, flow.seed, 1.8, 3.2)
                 + .3 * seeded_noise.clustered_noise(s, flow.seed + 1, .3, .7))
    return flow.launch_speed_m_s * (1 + flow.launch_speed_variation * variation)


def stream_factor(flow, s, drop_m):
    """Per-stream flow multiplier 1 + m, constant down each stream apart from a slow drift."""
    shift = flow.stream_drift_m * seeded_noise.clustered_noise(drop_m, flow.seed + 2, .5, 1.2)
    return 1 + flow.stream_variation * seeded_noise.clustered_noise(s - shift, flow.seed + 3, flow.min_stream_width_m, flow.max_stream_width_m)


def flow_per_width_m2_s(flow, s, drop_m):
    """Flow per metre width q (m^2/s) at (s, drop_m)."""
    return mean_launch_speed_m_s(flow, s) ** 3 / GRAVITY_M_S2 * stream_factor(flow, s, drop_m)


def launch_speed_m_s(flow, s, drop_m):
    """Local launch speed v0 = (g q)^(1/3), m/s."""
    return np.cbrt(GRAVITY_M_S2 * flow_per_width_m2_s(flow, s, drop_m))


def fall_speed_m_s(flow, s, drop_m):
    """Sheet speed U = sqrt(v0^2 + 2 g drop_m), m/s."""
    v0 = launch_speed_m_s(flow, s, drop_m)
    return np.sqrt(v0 * v0 + 2 * GRAVITY_M_S2 * np.maximum(drop_m, 0))


def sheet_thickness_m(flow, s, drop_m):
    """Sheet thickness h = q / U, m."""
    return flow_per_width_m2_s(flow, s, drop_m) / fall_speed_m_s(flow, s, drop_m)


def throw(flow, s, drop_m):
    """Outward distance of the sheet mid-surface from the wall face, m."""
    return launch_speed_m_s(flow, s, drop_m) * np.sqrt(2 * np.maximum(drop_m, 0) / GRAVITY_M_S2)


def effective_depth(flow, s, drop_m, stretch_exponent=.5, stretch_reference_m=.15):
    """Fall-time stretch coordinate v = stretch_reference_m + integral of (U(stretch_reference_m)/U)^stretch_exponent, unchanged above stretch_reference_m; metres."""
    v0 = mean_launch_speed_m_s(flow, s)
    ref = v0 * v0 + 2 * GRAVITY_M_S2 * stretch_reference_m
    drop_m = np.asarray(drop_m, float)
    tail = stretch_reference_m + ref ** (stretch_exponent / 2) * ((v0 * v0 + 2 * GRAVITY_M_S2 * drop_m) ** (1 - stretch_exponent / 2) - ref ** (1 - stretch_exponent / 2)) / (GRAVITY_M_S2 * (2 - stretch_exponent))
    return np.where(drop_m <= stretch_reference_m, drop_m, tail)


def carrier_grid(lip, flow, s, drop_m):
    """Grids S, D (nd, ns), mid-surface points P and unit normals pointing away from the wall (nd, ns, 3)."""
    S, D = np.meshgrid(s, drop_m)
    P = lip.world(S, throw(flow, S, D), lip.origin_m[2] - D)
    normal = np.cross(np.gradient(P, axis=0), np.gradient(P, axis=1))
    normal /= np.linalg.norm(normal, axis=-1, keepdims=True) + 1e-12
    normal *= np.where(normal[..., :2] @ lip.outward_axis[:2] < 0, -1., 1.)[..., None]
    return S, D, P, normal


def landing(lip, flow, s):
    """Landing line on the receiving surface: world points (len(s), 3)."""
    s = np.asarray(s, float)
    d = np.full_like(s, lip.drop_m)
    return lip.world(s, throw(flow, s, d), np.full_like(s, lip.origin_m[2] - lip.drop_m))
