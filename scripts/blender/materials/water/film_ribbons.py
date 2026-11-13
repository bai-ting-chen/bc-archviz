"""Film ribbons; implementation for water.falling_film."""
import numpy as np
from materials.water import ballistic_sheet, seeded_noise


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
