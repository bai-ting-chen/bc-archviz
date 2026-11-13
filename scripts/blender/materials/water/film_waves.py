"""Film waves; implementation for water.falling_film."""
import numpy as np
from materials.water import ballistic_sheet, seeded_noise


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
