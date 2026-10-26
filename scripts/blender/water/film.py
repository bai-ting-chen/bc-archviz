"""Free-falling film as a field map on the ballistic carrier (references/materials/water/water-free-falling-film.md §3.3-3.8).

film_surfaces() evaluates every layer on a grid (s along the lip, d drop) and returns the front and back skins of
one water body, the water/torn mask and the fields the fragments and foot need. Every layer is its own term with
its own strength in FilmParams (RULES MAT_07); defaults are starting values to size from the shot (RULES MAT_03).
"""
from dataclasses import dataclass

import numpy as np

from . import curtain, noise

G = 9.81


@dataclass
class FilmParams:
    """Layer strengths and scales (metres, unless noted). Defaults = starting values from one courtyard-scale study."""
    stretch_k: float = .5          # fall-time stretch exponent (1 = physical)
    stretch_ref: float = .15       # m, top band left unstretched
    ribbon_spacing: float = .036   # m between ribbon centres
    ribbon_wander: float = .025    # m
    ribbon_varicose: float = .40   # +- width fraction
    ribbon_twist: float = 1.25     # rad
    ribbons: float = .40           # relief strength (aim slope p99 <~ 0.3 rad at full zone strength)
    zone_min: float = .40          # calm/busy zone range [zone_min, 1]
    swell: float = .003            # m sinuous swell amplitude
    swell_varicose: float = .40    # +- thickness fraction
    waves: float = .0006           # m roll-wave arc height
    wave_len: float = .035         # m short train (long train = 2.3x)
    wave_cover_rate: float = .22   # extra cover per m of drop
    wave_grow: float = 1.0         # extra amplitude per m of drop
    meander: float = .014          # m sideways meander amplitude
    tear_start: float = None       # m below the lip; None = 0.38 * drop
    tear_rate: float = .30
    tear_power: float = 1.4
    tear_stretch: float = 2.2      # tear where 1 + d(dy)/ds exceeds this
    slit_lo: float = .010          # m slit width range across
    slit_hi: float = .035
    tear_edge: float = .10         # field units over which thickness tapers to 0
    rim: float = .002              # m bead on torn edges
    edge_retreat: float = .06      # m * d^1.3 inward pull of the free side edges
    edge_band: float = .20         # m extra-tear band beside each free edge
    edge_tear: float = .8
    free_edges: tuple = (True, True)   # (s = 0 end, s = length end) are free (False = meets a wall)
    seed: int = 2100


# ---- individual layers (numpy, local coordinates) ----

def zones(p, s, v, m):
    """Calm/busy multiplier in [zone_min, 1]: clustered patches 0.3-1 m, busier on thick streams."""
    z = .7 + .15 * noise.clustered(s, p.seed + 1, .3, 1.) + .10 * noise.clustered(v, p.seed + 2, .3, 1.) + .05 * m
    return np.clip(z, p.zone_min, 1.)


def swell_field(s, v, seed):
    """Smooth broad swell in [-1, 1]: 32 noncommensurate modes, 80-200 mm across, ~60 mm half-width along v."""
    rng = np.random.default_rng(seed); n = 32
    fs = rng.uniform(5, 12.5, n) * rng.choice([-1, 1], n); fv = rng.uniform(.75, 1.25, n) / .36
    ph = rng.uniform(0, 2 * np.pi, n); w = rng.uniform(.5, 1.5, n); w /= w.sum()
    out = np.zeros(np.broadcast_shapes(np.shape(s), np.shape(v)))
    for a, b, c, ww in zip(fs, fv, ph, w):
        out += ww * np.cos(2 * np.pi * (a * s + b * v) + c)
    return out


def _wave_train(s, v, lam, seed, bend_lo, bend_hi):
    vv = np.linspace(-1., 30., 12000); kk = (1 + .35 * noise.clustered(vv, seed + 5, .08, .25)) / lam
    cyc = np.interp(v, vv, np.concatenate([[0], np.cumsum((kk[1:] + kk[:-1]) / 2 * np.diff(vv))]))
    c = cyc + .45 * noise.clustered(s, seed, bend_lo, bend_hi) + .35 * noise.clustered(s + .3 * v, seed + 1, .15, .45)
    crest = np.maximum(0, np.cos(2 * np.pi * c)) ** 4
    n = np.floor(c + .5).astype(np.int64) % 4096
    rng = np.random.default_rng(seed + 9); strength = rng.uniform(0, 1, 4096); shift = rng.uniform(0, 50, 4096)
    extent = noise.clustered(s + shift[n], seed + 7, .04, .18)
    return crest * strength[n] * np.clip(.5 + extent, 0, 1)


def roll_waves(p, s, v, d):
    """Roll-wave arcs across the flow in [0, ~3]: two irregular trains, per-crest strength, per-stream on/off, growing."""
    sd = p.seed + 30
    w = _wave_train(s, v, p.wave_len, sd, .06, .20) + .8 * _wave_train(s, v, 2.3 * p.wave_len, sd + 20, .10, .35)
    across = noise.clustered(s + 2.1 * noise.clustered(v, sd + 3, .1, .3), sd + 2, .03, .15)
    along = noise.clustered(v + 3.0 * noise.clustered(s, sd + 6, .04, .15), sd + 4, .08, .30)
    patch = np.clip((.6 * across + .6 * along - .45 + p.wave_cover_rate * d) / .5, 0, 1)
    return w * patch * (1 + p.wave_grow * d)


def meander(p, s, v, d):
    """Sideways meander shape (multiply by p.meander): two along-fall scales, phases changing over a few cm across."""
    sd = p.seed + 60
    a = noise.clustered(v + 1.7 * noise.clustered(s, sd, .03, .12), sd + 1, .03, .10)
    b = noise.clustered(v + 2.3 * noise.clustered(s, sd + 2, .06, .25), sd + 3, .08, .25)
    return (.6 * a + .6 * b) * (.4 + .3 * d)


def ribbon_envelope(p, s_grid, v, h):
    """Front/back offsets (>= h/2, <= -h/2) of the ribbon union over a base sheet of thickness h (2-D arrays)."""
    s_axis = s_grid[0]; front = h * .5; back = -h * .5
    s0, s1 = s_axis[0], s_axis[-1]
    first = int(np.floor((s0 - .05) / p.ribbon_spacing)); last = int(np.ceil((s1 + .05) / p.ribbon_spacing))
    for i in range(first, last + 1):
        sd = p.seed + 1000 + 7 * (i % 100000)
        base = i * p.ribbon_spacing + .008 * noise.clustered(np.array([0.]), sd + 1, .375, .625)[0]
        vc = v[:, int(np.clip(np.searchsorted(s_axis, base), 0, len(s_axis) - 1))]
        cy = base + p.ribbon_wander * noise.clustered(vc, sd + 2, .225, .375) + .005 * noise.clustered(vc, sd + 3, .075, .125)
        cy = cy + (1 if i % 2 == 0 else -1) * .014 * np.clip((noise.clustered(vc, p.seed + 900 + i // 2, .27, .45) - .05) * 2.5, 0, 1)
        w = (.008 + .009 * noise.unit(np.array([0.]), sd + 4, .375, .625)[0]) * (1 + p.ribbon_varicose * noise.clustered(vc, sd + 5, .09, .15))
        t = .0007 + .0035 * noise.unit(vc, sd + 6, .079, .131) ** 3 + .018 * np.maximum(0, noise.clustered(vc, sd + 8, .052, .088) - .55) ** 2
        a = p.ribbon_twist * noise.clustered(vc, sd + 7, .071, .119)
        lo = max(0, int(np.searchsorted(s_axis, cy.min() - .035)) - 1)
        hi = min(len(s_axis), int(np.searchsorted(s_axis, cy.max() + .035)) + 1)
        if hi <= lo: continue
        dy = s_axis[None, lo:hi] - cy[:, None]; ca, sa = np.cos(a), np.sin(a)
        r2 = (w * ca) ** 2 + (t * sa) ** 2
        q = np.maximum(0, 1 - dy * dy / r2[:, None])
        mid = ((w * w - t * t) * ca * sa / r2)[:, None] * dy
        half = (w * t / np.sqrt(r2))[:, None] * np.sqrt(q)
        ok = q > 0
        np.maximum(front[:, lo:hi], np.where(ok, mid + half, front[:, lo:hi]), out=front[:, lo:hi])
        np.minimum(back[:, lo:hi], np.where(ok, mid - half, back[:, lo:hi]), out=back[:, lo:hi])
    return front, back


def tear_value(p, s, v):
    """High = torn: narrow across (slit_lo..slit_hi), long and finite along the stretched fall."""
    sd = p.seed + 150
    across = noise.clustered(s + .04 * noise.clustered(v, sd + 1, .2, .6), sd, p.slit_lo, p.slit_hi)
    along = noise.clustered(v + 2.5 * noise.clustered(s, sd + 2, .05, .2), sd + 3, .15, .6)
    return .55 * across + .55 * along


# ---- assembly ----

def film_surfaces(lip, flow, p, s, d):
    """All layers on the grid s x d: front/back world points (nd, ns, 3), water mask, and fields for fragments/foot."""
    S, D, P, n = curtain.carrier_grid(lip, flow, s, d)
    V = curtain.effective_depth(flow, S, D, p.stretch_k, p.stretch_ref)
    m = curtain.stream_factor(flow, S, D) - 1
    h = curtain.thickness(flow, S, D)
    ef, eb = ribbon_envelope(p, S, V, h)
    rf = np.maximum(ef - h / 2, 0); rb = np.minimum(eb + h / 2, 0)
    z = zones(p, S, V, m / max(flow.stream_amp, 1e-6))
    var = 1 + p.swell_varicose * swell_field(S, V, p.seed + 41)
    off = p.swell * swell_field(S, V, p.seed + 40)
    front = (h / 2 + p.ribbons * z * rf) * var + p.waves * roll_waves(p, S, V, D)
    back = (-h / 2 + p.ribbons * z * rb) * var
    # tears: field + where the meander stretches the sheet, from tear_start down
    start = .38 * lip.drop if p.tear_start is None else p.tear_start
    dy = p.meander * meander(p, S, V, D)
    stretch = 1 + np.gradient(dy, s, axis=1)
    ramp = np.clip((D - start) / .6, 0, 1)
    gap = 1.25 - p.tear_rate * np.maximum(0, D - start) ** p.tear_power - tear_value(p, S, V)
    gap = np.minimum(gap, .25 * (p.tear_stretch - stretch) * ramp + (1 - ramp) * 9)
    for end, free in zip((0, 1), p.free_edges):                 # dissolving free side edges
        if not free: continue
        e = S if end == 0 else lip.length - S
        sd = p.seed + 200 + end * 10
        retreat = p.edge_retreat * D ** 1.3 * (1 + .5 * noise.clustered(V, sd, .1, .4)) \
            + .015 * noise.clustered(V + 2 * noise.clustered(S, sd + 1, .05, .2), sd + 2, .04, .15)
        gap = np.minimum(gap, (e - retreat) / .05)
        gap = gap - p.edge_tear * np.exp(-np.maximum(e - retreat, 0) / p.edge_band) * np.clip(D / .6, 0, 1)
    taper = np.sqrt(np.clip(gap / p.tear_edge, 0, 1))
    bead = p.rim * np.exp(-((gap - .03) / .03) ** 2) * (D > start)
    mid_off = (front + back) / 2 + off; half = (front - back) / 2 * taper + .5 * bead * taper
    F = P + n * (mid_off + half)[..., None]; B = P + n * (mid_off - half)[..., None]
    lat = lip.along[None, None, :] * dy[..., None]
    F += lat; B += lat
    keep = gap > 0
    return dict(front=F, back=B, keep=keep, gap=gap, normal=n, S=S, D=D, V=V,
                start=start, folded=float(((np.diff(F @ lip.along, axis=1) <= 0) & keep[:, 1:] & keep[:, :-1]).mean()))
