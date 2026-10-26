"""Free-falling film as a field map on the ballistic carrier
(references/materials/water/water-free-falling-film.md §3.3-3.8).

Coordinates (shared by every water module): s = metres along the lip, d = drop below the lip, v = fall-time
stretched depth (curtain.effective_depth). film_surfaces() evaluates every layer on an s x d grid and returns the
front and back skins of one water body plus the fields fragments and foot need. Each layer is its own term with
its own strength in FilmParams (RULES MAT_07); defaults are starting values to size from the shot (RULES MAT_03).
"""
from dataclasses import dataclass

import numpy as np

from . import curtain, noise


@dataclass
class FilmParams:
    """Layer strengths and scales (metres unless noted); starting values from one courtyard-scale view."""
    # fall-time stretch (§3.3)
    stretch_k: float = .5          # exponent: 1 = physical, lower = less stretched
    stretch_ref: float = .15       # m top band left unstretched
    # fine ribbons (§3.4)
    ribbon_spacing: float = .036   # m between ribbon centres
    ribbon_wander: float = .025    # m sideways wander of each ribbon
    ribbon_varicose: float = .40   # +- width fraction
    ribbon_twist: float = 1.25     # rad
    ribbons: float = .40           # relief strength (aim slope p99 <~ 0.3 rad at full zone strength)
    zone_min: float = .40          # calm/busy zones span [zone_min, 1]
    swell: float = .003            # m sinuous swell amplitude
    swell_varicose: float = .40    # +- thickness fraction
    waves: float = .0006           # m roll-wave arc height
    wave_len: float = .035         # m short train (the long train is 2.3x)
    wave_cover_rate: float = .22   # extra arc cover per m of drop
    wave_grow: float = 1.0         # extra arc amplitude per m of drop
    # meander and tears (§3.5-3.6)
    meander: float = .014          # m sideways meander amplitude
    tear_start: float = None       # m below the lip; None = 0.38 x drop
    tear_rate: float = .30         # threshold fall per m^tear_power below tear_start
    tear_power: float = 1.4
    tear_stretch: float = 2.2      # tear where 1 + d(meander)/ds exceeds this
    slit_lo: float = .010          # m slit width range across the flow
    slit_hi: float = .035
    tear_edge: float = .10         # field units over which thickness tapers to 0
    rim: float = .002              # m bead of swept water on torn edges
    # free side edges (§3.8)
    edge_retreat: float = .06      # m x d^1.3 inward pull
    edge_band: float = .20         # m band of extra tearing beside each free edge
    edge_tear: float = .8
    free_edges: tuple = (True, True)   # (s = 0 end, s = length end); False where the sheet meets a wall
    seed: int = 2100


@dataclass
class FilmFields:
    """Result of film_surfaces: grids are (nd, ns) or (nd, ns, 3), rows = drop."""
    front: np.ndarray       # world points of the front skin
    back: np.ndarray        # world points of the back skin
    keep: np.ndarray        # True where there is water
    gap: np.ndarray         # tear field: > 0 water, < 0 torn
    normal: np.ndarray      # carrier normals, away from the wall
    S: np.ndarray           # along-lip coordinate
    D: np.ndarray           # drop
    V: np.ndarray           # stretched depth
    tear_start: float       # m below the lip
    folded: float           # share of water quads folded over by the meander


# ---------------------------------------------------------------- layers (numpy, sheet coordinates)

def zones(p, s, v, stream):
    """Calm/busy multiplier in [zone_min, 1]: clustered patches 0.3-1 m, busier on thick streams (stream in [-1, 1])."""
    z = (.7 + .15 * noise.clustered(s, p.seed + 1, .3, 1.)
         + .10 * noise.clustered(v, p.seed + 2, .3, 1.)
         + .05 * stream)
    return np.clip(z, p.zone_min, 1.)


def swell_field(s, v, seed):
    """Smooth broad swell in [-1, 1]: 32 noncommensurate modes, 80-200 mm across, ~60 mm half-width along v."""
    rng = np.random.default_rng(seed)
    count = 32
    k_s = rng.uniform(5, 12.5, count) * rng.choice([-1, 1], count)    # cycles per m across
    k_v = rng.uniform(.75, 1.25, count) / .36                          # cycles per m along
    phase = rng.uniform(0, 2 * np.pi, count)
    weight = rng.uniform(.5, 1.5, count)
    weight /= weight.sum()                                             # bounds the sum to [-1, 1]
    out = np.zeros(np.broadcast_shapes(np.shape(s), np.shape(v)))
    for ks, kv, ph, w in zip(k_s, k_v, phase, weight):
        out += w * np.cos(2 * np.pi * (ks * s + kv * v) + ph)
    return out


def _wave_train(s, v, wavelength, seed, bend_lo, bend_hi):
    """One irregular train of arcs: wavelength drifts +-35 %, fronts bend, each crest has its own strength/extent."""
    v_axis = np.linspace(-1., 30., 12000)
    wavenumber = (1 + .35 * noise.clustered(v_axis, seed + 5, .08, .25)) / wavelength
    cycles_axis = np.concatenate([[0], np.cumsum((wavenumber[1:] + wavenumber[:-1]) / 2 * np.diff(v_axis))])
    cycles = (np.interp(v, v_axis, cycles_axis)
              + .45 * noise.clustered(s, seed, bend_lo, bend_hi)
              + .35 * noise.clustered(s + .3 * v, seed + 1, .15, .45))
    crest = np.maximum(0, np.cos(2 * np.pi * cycles)) ** 4
    crest_id = np.floor(cycles + .5).astype(np.int64) % 4096
    rng = np.random.default_rng(seed + 9)
    strength = rng.uniform(0, 1, 4096)
    shift = rng.uniform(0, 50, 4096)
    extent = noise.clustered(s + shift[crest_id], seed + 7, .04, .18)
    return crest * strength[crest_id] * np.clip(.5 + extent, 0, 1)


def roll_waves(p, s, v, d):
    """Roll-wave arcs across the flow, ~[0, 3]: two trains, on/off per stream, more and taller down the fall."""
    seed = p.seed + 30
    arcs = (_wave_train(s, v, p.wave_len, seed, .06, .20)
            + .8 * _wave_train(s, v, 2.3 * p.wave_len, seed + 20, .10, .35))
    across = noise.clustered(s + 2.1 * noise.clustered(v, seed + 3, .1, .3), seed + 2, .03, .15)
    along = noise.clustered(v + 3.0 * noise.clustered(s, seed + 6, .04, .15), seed + 4, .08, .30)
    cover = np.clip((.6 * across + .6 * along - .45 + p.wave_cover_rate * d) / .5, 0, 1)
    return arcs * cover * (1 + p.wave_grow * d)


def meander(p, s, v, d):
    """Sideways meander shape (x p.meander = metres): two along-fall scales, phase changing over a few cm across."""
    seed = p.seed + 60
    short = noise.clustered(v + 1.7 * noise.clustered(s, seed, .03, .12), seed + 1, .03, .10)
    long_ = noise.clustered(v + 2.3 * noise.clustered(s, seed + 2, .06, .25), seed + 3, .08, .25)
    return (.6 * short + .6 * long_) * (.4 + .3 * d)


def _ribbon_seed(p, i):
    return p.seed + 1000 + 7 * (i % 100000)


def _ribbon_base(p, i):
    """Rest position of ribbon i along the lip, m: even spacing with a fixed jitter of up to 8 mm."""
    return i * p.ribbon_spacing + .008 * noise.clustered(np.array([0.]), _ribbon_seed(p, i) + 1, .375, .625)[0]


def _ribbon(p, i, v_col):
    """Centre, half-width, half-thickness and twist of ribbon i along the fall (v_col = stretched depth there)."""
    seed = _ribbon_seed(p, i)
    zero = np.array([0.])
    centre = (_ribbon_base(p, i)
              + p.ribbon_wander * noise.clustered(v_col, seed + 2, .225, .375)
              + .005 * noise.clustered(v_col, seed + 3, .075, .125))
    braid = np.clip((noise.clustered(v_col, p.seed + 900 + i // 2, .27, .45) - .05) * 2.5, 0, 1)
    centre = centre + (1 if i % 2 == 0 else -1) * .014 * braid          # pairs approach and split
    width = ((.008 + .009 * noise.unit(zero, seed + 4, .375, .625)[0])
             * (1 + p.ribbon_varicose * noise.clustered(v_col, seed + 5, .09, .15)))
    thick = (.0007 + .0035 * noise.unit(v_col, seed + 6, .079, .131) ** 3
             + .018 * np.maximum(0, noise.clustered(v_col, seed + 8, .052, .088) - .55) ** 2)   # sparse lens swells
    twist = p.ribbon_twist * noise.clustered(v_col, seed + 7, .071, .119)
    return centre, width, thick, twist


def ribbon_envelope(p, S, V, h):
    """Front/back offsets of the union of twisted elliptical ribbons over a sheet of thickness h (front >= h/2)."""
    s_axis = S[0]
    front, back = h * .5, -h * .5
    first = int(np.floor((s_axis[0] - .05) / p.ribbon_spacing))
    last = int(np.ceil((s_axis[-1] + .05) / p.ribbon_spacing))
    for i in range(first, last + 1):
        base = _ribbon_base(p, i)
        v_col = V[:, int(np.clip(np.searchsorted(s_axis, base), 0, len(s_axis) - 1))]
        centre, w, t, twist = _ribbon(p, i, v_col)
        lo = max(0, int(np.searchsorted(s_axis, centre.min() - .035)) - 1)
        hi = min(len(s_axis), int(np.searchsorted(s_axis, centre.max() + .035)) + 1)
        if hi <= lo:
            continue
        dy = s_axis[None, lo:hi] - centre[:, None]
        ca, sa = np.cos(twist), np.sin(twist)
        r2 = (w * ca) ** 2 + (t * sa) ** 2
        inside = np.maximum(0, 1 - dy * dy / r2[:, None])
        mid = ((w * w - t * t) * ca * sa / r2)[:, None] * dy               # centre line of the tilted ellipse
        half = (w * t / np.sqrt(r2))[:, None] * np.sqrt(inside)           # half height through it
        hit = inside > 0
        np.maximum(front[:, lo:hi], np.where(hit, mid + half, front[:, lo:hi]), out=front[:, lo:hi])
        np.minimum(back[:, lo:hi], np.where(hit, mid - half, back[:, lo:hi]), out=back[:, lo:hi])
    return front, back


def tear_value(p, s, v):
    """High = torn: narrow across (slit_lo..slit_hi), long and finite along the stretched fall."""
    seed = p.seed + 150
    across = noise.clustered(s + .04 * noise.clustered(v, seed + 1, .2, .6), seed, p.slit_lo, p.slit_hi)
    along = noise.clustered(v + 2.5 * noise.clustered(s, seed + 2, .05, .2), seed + 3, .15, .6)
    return .55 * across + .55 * along


def _gap_field(p, lip, s, S, D, V, lateral, start):
    """Tear field (> 0 water): slit field + where the meander stretches the sheet + dissolving free edges."""
    stretch = 1 + np.gradient(lateral, s, axis=1)
    ramp = np.clip((D - start) / .6, 0, 1)                             # tears fade in over 0.6 m
    gap = 1.25 - p.tear_rate * np.maximum(0, D - start) ** p.tear_power - tear_value(p, S, V)
    gap = np.minimum(gap, .25 * (p.tear_stretch - stretch) * ramp + (1 - ramp) * 9)
    for end, free in enumerate(p.free_edges):
        if not free:
            continue
        dist = S if end == 0 else lip.length - S                      # distance from that end
        seed = p.seed + 200 + end * 10
        retreat = (p.edge_retreat * D ** 1.3 * (1 + .5 * noise.clustered(V, seed, .1, .4))
                   + .015 * noise.clustered(V + 2 * noise.clustered(S, seed + 1, .05, .2), seed + 2, .04, .15))
        gap = np.minimum(gap, (dist - retreat) / .05)
        band = np.exp(-np.maximum(dist - retreat, 0) / p.edge_band) * np.clip(D / .6, 0, 1)
        gap = gap - p.edge_tear * band
    return gap


# ---------------------------------------------------------------- assembly

def film_surfaces(lip, flow, p, s, d):
    """Evaluate every layer on the grid s x d (metres) and return FilmFields."""
    S, D, P, normal = curtain.carrier_grid(lip, flow, s, d)
    V = curtain.effective_depth(flow, S, D, p.stretch_k, p.stretch_ref)
    stream = (curtain.stream_factor(flow, S, D) - 1) / max(flow.stream_amp, 1e-6)
    h = curtain.thickness(flow, S, D)

    env_front, env_back = ribbon_envelope(p, S, V, h)
    relief_front = np.maximum(env_front - h / 2, 0)
    relief_back = np.minimum(env_back + h / 2, 0)
    zone = zones(p, S, V, stream)
    varicose = 1 + p.swell_varicose * swell_field(S, V, p.seed + 41)
    sinuous = p.swell * swell_field(S, V, p.seed + 40)
    front = (h / 2 + p.ribbons * zone * relief_front) * varicose + p.waves * roll_waves(p, S, V, D)
    back = (-h / 2 + p.ribbons * zone * relief_back) * varicose

    start = .38 * lip.drop if p.tear_start is None else p.tear_start
    lateral = p.meander * meander(p, S, V, D)
    gap = _gap_field(p, lip, s, S, D, V, lateral, start)
    taper = np.sqrt(np.clip(gap / p.tear_edge, 0, 1))                  # rounded rim, zero thickness at the tear
    bead = p.rim * np.exp(-((gap - .03) / .03) ** 2) * (D > start)
    mid = (front + back) / 2 + sinuous
    half = (front - back) / 2 * taper + .5 * bead * taper

    shift = lip.along[None, None, :] * lateral[..., None]
    F = P + normal * (mid + half)[..., None] + shift
    B = P + normal * (mid - half)[..., None] + shift
    keep = gap > 0
    folded = (np.diff(F @ lip.along, axis=1) <= 0) & keep[:, 1:] & keep[:, :-1]
    return FilmFields(front=F, back=B, keep=keep, gap=gap, normal=normal, S=S, D=D, V=V,
                      tear_start=start, folded=float(folded.mean()))
