"""Film ribbons; implementation for water.film."""
import numpy as np
from materials.water import curtain, noise


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
