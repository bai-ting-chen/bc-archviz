"""Film tears; implementation for water.falling_film."""
import numpy as np
from materials.water import ballistic_sheet, seeded_noise


def tear_value(params, s, stretched_depth_m):
    """High = torn: narrow across (slit_lo..slit_hi), long and finite along the stretched fall."""
    seed = params.seed + 150
    across = seeded_noise.clustered_noise(s + .04 * seeded_noise.clustered_noise(stretched_depth_m, seed + 1, .2, .6), seed, params.min_slit_width_m, params.max_slit_width_m)
    along = seeded_noise.clustered_noise(stretched_depth_m + 2.5 * seeded_noise.clustered_noise(s, seed + 2, .05, .2), seed + 3, .15, .6)
    return .55 * across + .55 * along


def _gap_field(params, lip, s, along_lip_m, drop_m, stretched_depth_m, lateral, start):
    """Tear field (> 0 water): slit field + where the meander stretches the sheet + dissolving free edges."""
    stretch = 1 + np.gradient(lateral, s, axis=1)
    ramp = np.clip((drop_m - start) / .6, 0, 1)                             # tears fade in over 0.6 m
    gap = 1.25 - params.tear_threshold_fall_per_m_power * np.maximum(0, drop_m - start) ** params.tear_exponent - tear_value(params, along_lip_m, stretched_depth_m)
    gap = np.minimum(gap, .25 * (params.tear_stretch_threshold - stretch) * ramp + (1 - ramp) * 9)
    for end, free in enumerate(params.free_edges):
        if not free:
            continue
        dist = along_lip_m if end == 0 else lip.length_m - along_lip_m                      # distance from that end
        seed = params.seed + 200 + end * 10
        retreat = (params.edge_retreat_coefficient * drop_m ** 1.3 * (1 + .5 * seeded_noise.clustered_noise(stretched_depth_m, seed, .1, .4))
                   + .015 * seeded_noise.clustered_noise(stretched_depth_m + 2 * seeded_noise.clustered_noise(along_lip_m, seed + 1, .05, .2), seed + 2, .04, .15))
        gap = np.minimum(gap, (dist - retreat) / .05)
        band = np.exp(-np.maximum(dist - retreat, 0) / params.edge_band_m) * np.clip(drop_m / .6, 0, 1)
        gap = gap - params.edge_tear_strength * band
    return gap
