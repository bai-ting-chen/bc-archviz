"""Where falling water meets a pool: impacts, crowns, foam, floating bubbles, splash
(references/materials/water/water-splash.md, water-foam.md).

Works in lip-local coordinates (a along the lip, o outward from the wall face) and returns world-space
geometry as (vertices, faces) arrays; water.mesh makes the objects. Impacts come from the water itself (the
film's bottom row, weighted by thickness, plus drops reaching the pool), so every element clusters where the
water lands instead of lining up along a drawn line.
"""
from dataclasses import dataclass

import numpy as np


@dataclass
class FootParams:
    """Impact spacing, crowns, foam, floating bubbles and splash (starting values; size from the shot)."""
    impact_spacing: float = .02     # m of landing line per stream impact
    crowns: float = .35             # share of impacts (strongest) with a standing crown
    foam_per_m: float = 350.
    foam_size: float = .010         # m median (size from the final view: flecks under ~1 px vanish)
    foam_max: float = .04
    foam_focus: float = .4          # parent weight = strength ** focus
    foam_reach: float = .18         # m mean distance from the impact
    foam_spread: float = .03        # m sideways scatter at the impact
    drift: float = .5               # sideways drift sigma per m travelled (carries past both ends)
    bubbles_per_m: float = 600.
    bubble_d: float = .006          # m median diameter
    bubble_reach: float = .5        # m mean (+5 cm)
    raft_share: float = .15
    splash_per_m: float = 40.
    max_out: float = 1.5            # m from the wall; nothing placed beyond (keep inside the pool)
    seed: int = 2300


def impacts(lip, land_mid, land_keep, land_thick, drops, pool_z, p):
    """Impact points (N, 3) on the pool surface and strengths (N,), from the film's bottom row and falling drops."""
    rng = np.random.default_rng(p.seed)
    thick = land_thick * land_keep
    a_mid, o_mid = lip.local(land_mid)
    span = float(abs(a_mid[-1] - a_mid[0])) or lip.length
    n = max(1, int(span / p.impact_spacing))
    if thick.sum() > 0:                      # sheet landings (none when the bottom row is fully torn)
        idx = rng.choice(len(land_mid), size=n, p=thick / thick.sum())
        a = a_mid[idx] + rng.normal(0, .006, n); o = o_mid[idx] + rng.normal(0, .012, n)
        strength = np.clip(thick[idx] / np.percentile(thick[land_keep], 90), .15, 1.5)
    else:
        a = o = strength = np.zeros(0)
    if drops is not None and len(drops):
        low = drops[drops[:, 2] < pool_z + .6]
        if len(low):
            k = rng.choice(len(low), size=min(len(low), n), replace=False)
            da, do = lip.local(low[k, :3]); do = do + rng.uniform(0, .03, len(k))
            a = np.r_[a, da]; o = np.r_[o, do]; strength = np.r_[strength, rng.uniform(.05, .3, len(k))]
    if not len(a): return np.zeros((0, 3)), np.zeros(0)
    return lip.world(a, o, np.full_like(a, pool_z)), strength


def crowns(pts, strength, p):
    """Clear crowns at the strongest impacts: tilted rings with spiky rims. Returns (V, F); use thin-wall water."""
    rng = np.random.default_rng(p.seed + 1); nseg = 14; V = []; F = []; o = 0
    ang = np.linspace(0, 2 * np.pi, nseg, endpoint=False)
    for i in np.argsort(-strength)[:int(len(strength) * p.crowns)]:
        c, s = pts[i], strength[i]
        R = rng.uniform(.006, .02) * (.7 + .5 * s); Ht = rng.uniform(.003, .014) * s
        tilt = rng.normal(0, .3, 2); spikes = 1 + .6 * rng.random(nseg) ** 2
        for ring, (rad, z) in enumerate([(R * .8, -.002), (R, Ht * .5), (R * 1.15, Ht), (R * 1.05, Ht * .2)]):
            zz = z * (spikes if ring == 2 else 1)
            V.append(np.c_[c[0] + rad * np.cos(ang), c[1] + rad * np.sin(ang),
                           c[2] + zz + tilt[0] * rad * np.cos(ang) + tilt[1] * rad * np.sin(ang)])
        for ring in range(3):
            for j in range(nseg):
                a0 = o + ring * nseg + j; a1 = o + ring * nseg + (j + 1) % nseg
                F.append([a0, a1, a1 + nseg, a0 + nseg])
        o += 4 * nseg
    return (np.concatenate(V) if V else np.zeros((0, 3))), F


def _drift(lip, pts, rng, mean, focus_w, n, p, extra=0.):
    """Parents, travelled distance and drifted lip-local positions (a, o) for n spawned items."""
    w = focus_w / focus_w.sum(); par = rng.choice(len(pts), size=n, p=w)
    a0, o0 = lip.local(pts[par])
    dist = extra + rng.exponential(mean, n)
    dirn = np.c_[np.ones(n), rng.normal(0, .7, n)]; dirn /= np.linalg.norm(dirn, axis=1, keepdims=True)
    o = o0 + dirn[:, 0] * dist
    a = a0 + dirn[:, 1] * dist + rng.normal(0, 1, n) * (p.foam_spread + p.drift * dist)
    return a, o, dist, dirn


def foam(lip, pts, strength, pool_z, p):
    """Irregular foam flecks clustered at impacts, drifting out and past the ends, stretched as they travel. (V, F)."""
    rng = np.random.default_rng(p.seed + 2)
    span = float(np.ptp(lip.local(pts)[0])) if len(pts) else 0
    n = int(span * p.foam_per_m)
    if n == 0: return np.zeros((0, 3)), []
    a, o, dist, dirn = _drift(lip, pts, rng, p.foam_reach, strength ** p.foam_focus, n, p)
    V = []; F = []; k = 0
    for i in range(n):
        if o[i] > p.max_out: continue
        size = np.clip(rng.lognormal(np.log(p.foam_size), .7), .0015, p.foam_max)
        elong = 1 + rng.exponential(.8) * min(1, dist[i] / .1)
        m = int(rng.integers(7, 14)); ang = np.sort(rng.uniform(0, 2 * np.pi, m))
        rad = size / 2 * (1 + .45 * rng.normal(0, 1, m)).clip(.3, 1.8)
        lo_, la_ = rad * np.cos(ang) * elong, rad * np.sin(ang)        # along the drift, across it
        ro = o[i] + lo_ * dirn[i, 0] - la_ * dirn[i, 1]; ra = a[i] + lo_ * dirn[i, 1] + la_ * dirn[i, 0]
        V.append(lip.world(np.r_[a[i], ra], np.r_[o[i], ro], np.full(m + 1, pool_z + .0009)))
        F += [[k, k + 1 + j, k + 1 + (j + 1) % m] for j in range(m)]; k += m + 1
    return (np.concatenate(V) if V else np.zeros((0, 3))), F


def _dome():
    ang = np.linspace(0, 2 * np.pi, 9)[:-1]; el = np.array([0., .55, 1.05, 1.45])
    ring = np.array([[np.cos(e) * np.cos(t), np.cos(e) * np.sin(t), np.sin(e)] for e in el[:-1] for t in ang])
    unit = np.r_[ring, [[0, 0, 1]]]; tri = []
    for r in range(len(el) - 2):
        for j in range(8):
            a0 = r * 8 + j; a1 = r * 8 + (j + 1) % 8; tri.append([a0, a1, a1 + 8, a0 + 8])
    top = (len(el) - 2) * 8; tri += [[top + j, top + (j + 1) % 8, len(unit) - 1] for j in range(8)]
    return unit, tri


def bubbles(lip, pts, strength, pool_z, p):
    """Floating clear domes (single or rafts), carried far out and past the ends. (V, F); use thin-wall water."""
    rng = np.random.default_rng(p.seed + 3)
    span = float(np.ptp(lip.local(pts)[0])) if len(pts) else 0
    n = int(span * p.bubbles_per_m)
    if n == 0: return np.zeros((0, 3)), []
    a, o, dist, _ = _drift(lip, pts, rng, p.bubble_reach, strength ** .3, n, p, extra=.05)
    unit, tri = _dome(); nu = len(unit); V = []; F = []; k = 0
    for i in range(n):
        if o[i] > p.max_out: continue
        count = 1 if rng.random() > p.raft_share else int(rng.integers(3, 12))
        for _ in range(count):
            r = np.clip(rng.lognormal(np.log(p.bubble_d / 2), .5), .001, .0075)
            da, do = (rng.normal(0, .006, 2) * np.sqrt(count)) if count > 1 else (0., 0.)
            c = lip.world(np.array([a[i] + da]), np.array([o[i] + do]), np.array([pool_z - .2 * r]))[0]
            V.append(unit * [r, r, .85 * r] + c); F += [[k + v for v in f] for f in tri]; k += nu
    return (np.concatenate(V) if V else np.zeros((0, 3))), F


def splash(lip, pts, strength, pool_z, p):
    """Splash drops thrown up and out from the strongest impacts: array (N, 5) = x, y, z, diameter, stretch."""
    rng = np.random.default_rng(p.seed + 4)
    span = float(np.ptp(lip.local(pts)[0])) if len(pts) else 0
    n = int(span * p.splash_per_m)
    if n == 0: return np.zeros((0, 5))
    w = strength ** 2; idx = rng.choice(len(pts), size=n, p=w / w.sum())
    a, o = lip.local(pts[idx]); o = o + rng.uniform(0, .12, n); a = a + rng.normal(0, .04, n)
    c = lip.world(a, o, pool_z + rng.exponential(.03, n))
    return np.c_[c, np.clip(rng.lognormal(np.log(.0022), .4, n), .001, .005), rng.uniform(1, 1.8, n)]
