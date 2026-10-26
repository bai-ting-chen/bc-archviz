"""Film waves; implementation for water.film."""
import numpy as np
from materials.water import curtain, noise


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
