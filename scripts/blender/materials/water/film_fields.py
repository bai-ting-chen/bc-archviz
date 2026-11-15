"""Carrier-free film layers in along-lip and stretched-depth coordinates (metres)."""
import numpy as np

from materials.water import seeded_noise


def zones(params, s, stretched_depth_m, stream):
    """Calm/busy multiplier in [zone_min, 1]: clustered patches 0.3-1 m, busier on thick streams (stream in [-1, 1])."""
    z = (.7 + .15 * seeded_noise.clustered_noise(s, params.seed + 1, .3, 1.)
         + .10 * seeded_noise.clustered_noise(stretched_depth_m, params.seed + 2, .3, 1.)
         + .05 * stream)
    return np.clip(z, params.zone_min, 1.)


def swell_field(s, stretched_depth_m, seed):
    """Smooth broad swell in [-1, 1]: 32 noncommensurate modes, 80-200 mm across, ~60 mm half-width along stretched_depth_m."""
    rng = np.random.default_rng(seed)
    count = 32
    k_s = rng.uniform(5, 12.5, count) * rng.choice([-1, 1], count)    # cycles per m across
    k_v = rng.uniform(.75, 1.25, count) / .36                          # cycles per m along
    phase = rng.uniform(0, 2 * np.pi, count)
    weight = rng.uniform(.5, 1.5, count)
    weight /= weight.sum()                                             # bounds the sum to [-1, 1]
    out = np.zeros(np.broadcast_shapes(np.shape(s), np.shape(stretched_depth_m)))
    for ks, kv, ph, w in zip(k_s, k_v, phase, weight):
        out += w * np.cos(2 * np.pi * (ks * s + kv * stretched_depth_m) + ph)
    return out


def _wave_train(s, stretched_depth_m, wavelength, seed, bend_lo, bend_hi):
    """One irregular train of arcs: wavelength drifts +-35 %, fronts bend, each crest has its own strength/extent."""
    v_axis = np.linspace(-1., 30., 12000)
    wavenumber = (1 + .35 * seeded_noise.clustered_noise(v_axis, seed + 5, .08, .25)) / wavelength
    cycles_axis = np.concatenate([[0], np.cumsum((wavenumber[1:] + wavenumber[:-1]) / 2 * np.diff(v_axis))])
    cycles = (np.interp(stretched_depth_m, v_axis, cycles_axis)
              + .45 * seeded_noise.clustered_noise(s, seed, bend_lo, bend_hi)
              + .35 * seeded_noise.clustered_noise(s + .3 * stretched_depth_m, seed + 1, .15, .45))
    crest = np.maximum(0, np.cos(2 * np.pi * cycles)) ** 4
    crest_id = np.floor(cycles + .5).astype(np.int64) % 4096
    rng = np.random.default_rng(seed + 9)
    strength = rng.uniform(0, 1, 4096)
    shift = rng.uniform(0, 50, 4096)
    extent = seeded_noise.clustered_noise(s + shift[crest_id], seed + 7, .04, .18)
    return crest * strength[crest_id] * np.clip(.5 + extent, 0, 1)


def roll_waves(params, s, stretched_depth_m, drop_m):
    """Roll-wave arcs across the flow, ~[0, 3]: two trains, on/off per stream, more and taller down the fall."""
    seed = params.seed + 30
    arcs = (_wave_train(s, stretched_depth_m, params.wavelength_m, seed, .06, .20)
            + .8 * _wave_train(s, stretched_depth_m, 2.3 * params.wavelength_m, seed + 20, .10, .35))
    across = seeded_noise.clustered_noise(s + 2.1 * seeded_noise.clustered_noise(stretched_depth_m, seed + 3, .1, .3), seed + 2, .03, .15)
    along = seeded_noise.clustered_noise(stretched_depth_m + 3.0 * seeded_noise.clustered_noise(s, seed + 6, .04, .15), seed + 4, .08, .30)
    cover = np.clip((.6 * across + .6 * along - .45 + params.wave_coverage_growth_per_m * drop_m) / .5, 0, 1)
    return arcs * cover * (1 + params.wave_amplitude_growth_per_m * drop_m)


def meander(params, s, stretched_depth_m, drop_m):
    """Sideways meander shape (x params.meander = metres): two along-fall scales, phase changing over a few cm across."""
    seed = params.seed + 60
    short = seeded_noise.clustered_noise(stretched_depth_m + 1.7 * seeded_noise.clustered_noise(s, seed, .03, .12), seed + 1, .03, .10)
    long_ = seeded_noise.clustered_noise(stretched_depth_m + 2.3 * seeded_noise.clustered_noise(s, seed + 2, .06, .25), seed + 3, .08, .25)
    return (.6 * short + .6 * long_) * (.4 + .3 * drop_m)


def _ribbon_seed(params, i):
    return params.seed + 1000 + 7 * (i % 100000)


def _ribbon_base(params, i):
    """Rest position of ribbon i along the lip, m: even spacing with a fixed jitter of up to 8 mm."""
    return i * params.ribbon_spacing_m + .008 * seeded_noise.clustered_noise(np.array([0.]), _ribbon_seed(params, i) + 1, .375, .625)[0]


def _ribbon(params, i, v_col):
    """Centre, half-width, half-thickness and twist of ribbon i along the fall (v_col = stretched depth there)."""
    seed = _ribbon_seed(params, i)
    zero = np.array([0.])
    centre = (_ribbon_base(params, i)
              + params.ribbon_wander_m * seeded_noise.clustered_noise(v_col, seed + 2, .225, .375)
              + .005 * seeded_noise.clustered_noise(v_col, seed + 3, .075, .125))
    braid = np.clip((seeded_noise.clustered_noise(v_col, params.seed + 900 + i // 2, .27, .45) - .05) * 2.5, 0, 1)
    centre = centre + (1 if i % 2 == 0 else -1) * .014 * braid          # pairs approach and split
    width = ((.008 + .009 * seeded_noise.unit_noise(zero, seed + 4, .375, .625)[0])
             * (1 + params.ribbon_width_variation * seeded_noise.clustered_noise(v_col, seed + 5, .09, .15)))
    thick = (.0007 + .0035 * seeded_noise.unit_noise(v_col, seed + 6, .079, .131) ** 3
             + .018 * np.maximum(0, seeded_noise.clustered_noise(v_col, seed + 8, .052, .088) - .55) ** 2)   # sparse lens swells
    twist = params.ribbon_twist_rad * seeded_noise.clustered_noise(v_col, seed + 7, .071, .119)
    return centre, width, thick, twist


def ribbon_envelope(params, along_lip_m, stretched_depth_m, thickness_m):
    """Front/back offsets of the union of twisted elliptical ribbons over a sheet of thickness thickness_m (front >= thickness_m/2)."""
    s_axis = along_lip_m[0]
    front, back = thickness_m * .5, -thickness_m * .5
    first = int(np.floor((s_axis[0] - .05) / params.ribbon_spacing_m))
    last = int(np.ceil((s_axis[-1] + .05) / params.ribbon_spacing_m))
    for i in range(first, last + 1):
        base = _ribbon_base(params, i)
        v_col = stretched_depth_m[:, int(np.clip(np.searchsorted(s_axis, base), 0, len(s_axis) - 1))]
        centre, w, t, twist = _ribbon(params, i, v_col)
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


def tear_value(params, s, stretched_depth_m):
    """High = torn: narrow across (slit_lo..slit_hi), long and finite along the stretched fall."""
    seed = params.seed + 150
    across = seeded_noise.clustered_noise(s + .04 * seeded_noise.clustered_noise(stretched_depth_m, seed + 1, .2, .6), seed, params.min_slit_width_m, params.max_slit_width_m)
    along = seeded_noise.clustered_noise(stretched_depth_m + 2.5 * seeded_noise.clustered_noise(s, seed + 2, .05, .2), seed + 3, .15, .6)
    return .55 * across + .55 * along


def _gap_field(params, lip_length_m, s, along_lip_m, drop_m, stretched_depth_m, lateral, start):
    """Tear field (> 0 water): slit field + where the meander stretches the sheet + dissolving free edges."""
    stretch = 1 + np.gradient(lateral, s, axis=1)
    ramp = np.clip((drop_m - start) / .6, 0, 1)                             # tears fade in over 0.6 m
    gap = 1.25 - params.tear_threshold_fall_per_m_power * np.maximum(0, drop_m - start) ** params.tear_exponent - tear_value(params, along_lip_m, stretched_depth_m)
    gap = np.minimum(gap, .25 * (params.tear_stretch_threshold - stretch) * ramp + (1 - ramp) * 9)
    for end, free in enumerate(params.free_edges):
        if not free:
            continue
        dist = along_lip_m if end == 0 else lip_length_m - along_lip_m                      # distance from that end
        seed = params.seed + 200 + end * 10
        retreat = (params.edge_retreat_coefficient * drop_m ** 1.3 * (1 + .5 * seeded_noise.clustered_noise(stretched_depth_m, seed, .1, .4))
                   + .015 * seeded_noise.clustered_noise(stretched_depth_m + 2 * seeded_noise.clustered_noise(along_lip_m, seed + 1, .05, .2), seed + 2, .04, .15))
        gap = np.minimum(gap, (dist - retreat) / .05)
        band = np.exp(-np.maximum(dist - retreat, 0) / params.edge_band_m) * np.clip(drop_m / .6, 0, 1)
        gap = gap - params.edge_tear_strength * band
    return gap
