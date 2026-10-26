"""Where falling water meets a pool: impacts, crowns, foam, floating bubbles, splash
(references/materials/water/water-splash.md, water-foam.md).

Works in lip-local coordinates (s along the lip, o outward from the wall face) and returns world-space geometry
as (vertices, faces) or drop arrays (N, 5); water.mesh makes the objects. Impacts come from the water itself (the
film's bottom row weighted by thickness, plus drops reaching the pool), so every element clusters where the
water lands instead of lining up along a drawn line.
"""
from dataclasses import dataclass

import numpy as np

EMPTY_MESH = (np.zeros((0, 3)), [])


@dataclass
class FootParams:
    """Impact spacing, crowns, foam, floating bubbles and splash (starting values; size from the shot)."""
    impact_spacing: float = .02     # m of landing line per stream impact
    crowns: float = .35             # share of impacts (the strongest) with a standing crown
    foam_per_m: float = 350.        # per m of landing line
    foam_size: float = .010         # m median (flecks under ~1 px at the final view vanish)
    foam_max: float = .04
    foam_focus: float = .4          # parent weight = strength ** focus
    foam_reach: float = .18         # m mean distance travelled from the impact
    foam_spread: float = .03        # m sideways scatter at the impact
    drift: float = .5               # extra sideways scatter per m travelled (carries past both ends)
    bubbles_per_m: float = 600.
    bubble_d: float = .006          # m median diameter
    bubble_reach: float = .5        # m mean distance travelled (+5 cm)
    raft_share: float = .15         # share of bubble spawns that are rafts of 3-11
    splash_per_m: float = 40.
    max_out: float = 1.5            # m from the wall; nothing placed beyond (keeps it on the pool)
    seed: int = 2300


def _span(lip, pts):
    """Length of the landing line covered by the impacts, m."""
    return float(np.ptp(lip.local(pts)[0])) if len(pts) else 0.


# ---------------------------------------------------------------- impacts

def impacts(lip, land_mid, land_keep, land_thick, drops, pool_z, p):
    """Impact points (N, 3) on the pool surface and strengths (N,), from the film's bottom row and falling drops."""
    rng = np.random.default_rng(p.seed)
    thick = land_thick * land_keep
    s_row, o_row = lip.local(land_mid)
    span = float(abs(s_row[-1] - s_row[0])) or lip.length
    count = max(1, int(span / p.impact_spacing))
    if thick.sum() > 0:                                   # sheet landings (none when the bottom row is fully torn)
        idx = rng.choice(len(land_mid), size=count, p=thick / thick.sum())
        s = s_row[idx] + rng.normal(0, .006, count)
        o = o_row[idx] + rng.normal(0, .012, count)
        strength = np.clip(thick[idx] / np.percentile(thick[land_keep], 90), .15, 1.5)
    else:
        s = o = strength = np.zeros(0)
    if drops is not None and len(drops):                  # drops falling through the gaps land too, weaker
        low = drops[drops[:, 2] < pool_z + .6]
        if len(low):
            pick = rng.choice(len(low), size=min(len(low), count), replace=False)
            s_drop, o_drop = lip.local(low[pick, :3])
            o_drop = o_drop + rng.uniform(0, .03, len(pick))
            s = np.r_[s, s_drop]
            o = np.r_[o, o_drop]
            strength = np.r_[strength, rng.uniform(.05, .3, len(pick))]
    if not len(s):
        return np.zeros((0, 3)), np.zeros(0)
    return lip.world(s, o, np.full_like(s, pool_z)), strength


# ---------------------------------------------------------------- crowns

def crowns(pts, strength, p):
    """Clear crowns at the strongest impacts: tilted rings with spiky rims. (V, F); use thin-wall water."""
    rng = np.random.default_rng(p.seed + 1)
    segments = 14
    angle = np.linspace(0, 2 * np.pi, segments, endpoint=False)
    verts, faces, base = [], [], 0
    for i in np.argsort(-strength)[:int(len(strength) * p.crowns)]:
        centre, s = pts[i], strength[i]
        radius = rng.uniform(.006, .02) * (.7 + .5 * s)
        height = rng.uniform(.003, .014) * s
        tilt = rng.normal(0, .3, 2)
        spikes = 1 + .6 * rng.random(segments) ** 2
        rings = [(radius * .8, -.002), (radius, height * .5), (radius * 1.15, height), (radius * 1.05, height * .2)]
        for ring, (r, z) in enumerate(rings):
            z = z * (spikes if ring == 2 else 1)                        # the rim ring is spiky
            dx, dy = r * np.cos(angle), r * np.sin(angle)
            verts.append(np.c_[centre[0] + dx, centre[1] + dy, centre[2] + z + tilt[0] * dx + tilt[1] * dy])
        for ring in range(3):
            for j in range(segments):
                a0 = base + ring * segments + j
                a1 = base + ring * segments + (j + 1) % segments
                faces.append([a0, a1, a1 + segments, a0 + segments])
        base += 4 * segments
    return (np.concatenate(verts), faces) if verts else EMPTY_MESH


# ---------------------------------------------------------------- foam and bubbles

def _drift(lip, pts, rng, mean_dist, weight, count, p, extra=0.):
    """Spawn count items at impacts (by weight), carry them out and sideways: s, o, distance, unit direction (s, o)."""
    parent = rng.choice(len(pts), size=count, p=weight / weight.sum())
    s0, o0 = lip.local(pts[parent])
    dist = extra + rng.exponential(mean_dist, count)
    direction = np.c_[np.ones(count), rng.normal(0, .7, count)]          # (outward, sideways)
    direction /= np.linalg.norm(direction, axis=1, keepdims=True)
    o = o0 + direction[:, 0] * dist
    s = s0 + direction[:, 1] * dist + rng.normal(0, 1, count) * (p.foam_spread + p.drift * dist)
    return s, o, dist, direction


def _fleck(rng, s, o, dist, direction, p):
    """Outline of one irregular foam fleck around (s, o), stretched along its drift: arrays of s and o."""
    size = np.clip(rng.lognormal(np.log(p.foam_size), .7), .0015, p.foam_max)
    elongation = 1 + rng.exponential(.8) * min(1, dist / .1)
    corners = int(rng.integers(7, 14))
    angle = np.sort(rng.uniform(0, 2 * np.pi, corners))
    radius = size / 2 * (1 + .45 * rng.normal(0, 1, corners)).clip(.3, 1.8)
    along = radius * np.cos(angle) * elongation                         # along the drift
    across = radius * np.sin(angle)
    ring_o = o + along * direction[0] - across * direction[1]
    ring_s = s + along * direction[1] + across * direction[0]
    return ring_s, ring_o


def foam(lip, pts, strength, pool_z, p):
    """Irregular foam flecks clustered at impacts, drifting out and past the ends, stretched as they travel. (V, F)."""
    rng = np.random.default_rng(p.seed + 2)
    count = int(_span(lip, pts) * p.foam_per_m)
    if count == 0:
        return EMPTY_MESH
    s, o, dist, direction = _drift(lip, pts, rng, p.foam_reach, strength ** p.foam_focus, count, p)
    verts, faces, base = [], [], 0
    for i in range(count):
        if o[i] > p.max_out:
            continue
        ring_s, ring_o = _fleck(rng, s[i], o[i], dist[i], direction[i], p)
        corners = len(ring_s)
        verts.append(lip.world(np.r_[s[i], ring_s], np.r_[o[i], ring_o], np.full(corners + 1, pool_z + .0009)))
        faces += [[base, base + 1 + j, base + 1 + (j + 1) % corners] for j in range(corners)]   # fan from the centre
        base += corners + 1
    return (np.concatenate(verts), faces) if verts else EMPTY_MESH


def _dome():
    """Unit dome (upper hemisphere, 8 segments): vertices and quad/triangle faces."""
    angle = np.linspace(0, 2 * np.pi, 9)[:-1]
    elevation = np.array([0., .55, 1.05, 1.45])
    ring = np.array([[np.cos(e) * np.cos(t), np.cos(e) * np.sin(t), np.sin(e)] for e in elevation[:-1] for t in angle])
    unit = np.r_[ring, [[0, 0, 1]]]
    faces = []
    for r in range(len(elevation) - 2):
        for j in range(8):
            a0 = r * 8 + j
            a1 = r * 8 + (j + 1) % 8
            faces.append([a0, a1, a1 + 8, a0 + 8])
    top = (len(elevation) - 2) * 8
    faces += [[top + j, top + (j + 1) % 8, len(unit) - 1] for j in range(8)]
    return unit, faces


def bubbles(lip, pts, strength, pool_z, p):
    """Floating clear domes (single or in rafts), carried far out and past the ends. (V, F); use thin-wall water."""
    rng = np.random.default_rng(p.seed + 3)
    count = int(_span(lip, pts) * p.bubbles_per_m)
    if count == 0:
        return EMPTY_MESH
    s, o, _, _ = _drift(lip, pts, rng, p.bubble_reach, strength ** .3, count, p, extra=.05)
    unit, dome_faces = _dome()
    verts, faces, base = [], [], 0
    for i in range(count):
        if o[i] > p.max_out:
            continue
        in_raft = 1 if rng.random() > p.raft_share else int(rng.integers(3, 12))
        for _ in range(in_raft):
            r = np.clip(rng.lognormal(np.log(p.bubble_d / 2), .5), .001, .0075)
            ds, do = (rng.normal(0, .006, 2) * np.sqrt(in_raft)) if in_raft > 1 else (0., 0.)
            centre = lip.world(np.array([s[i] + ds]), np.array([o[i] + do]), np.array([pool_z - .2 * r]))[0]
            verts.append(unit * [r, r, .85 * r] + centre)                 # squashed, sunk 20 % of the radius
            faces += [[base + v for v in f] for f in dome_faces]
            base += len(unit)
    return (np.concatenate(verts), faces) if verts else EMPTY_MESH


# ---------------------------------------------------------------- splash

def splash(lip, pts, strength, pool_z, p):
    """Splash drops thrown up and out from the strongest impacts: array (N, 5) = x, y, z, diameter, stretch."""
    rng = np.random.default_rng(p.seed + 4)
    count = int(_span(lip, pts) * p.splash_per_m)
    if count == 0:
        return np.zeros((0, 5))
    weight = strength ** 2
    idx = rng.choice(len(pts), size=count, p=weight / weight.sum())
    s, o = lip.local(pts[idx])
    o = o + rng.uniform(0, .12, count)
    s = s + rng.normal(0, .04, count)
    centre = lip.world(s, o, pool_z + rng.exponential(.03, count))
    diameter = np.clip(rng.lognormal(np.log(.0022), .4, count), .001, .005)
    return np.c_[centre, diameter, rng.uniform(1, 1.8, count)]
