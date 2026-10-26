"""Film build; implementation for water.film."""
import numpy as np
from materials.water import curtain, noise
from materials.water.film_config import FilmFields
from materials.water.film_zones import zones
from materials.water.film_swell import swell_field
from materials.water.film_waves import roll_waves
from materials.water.film_meander import meander
from materials.water.film_ribbons import ribbon_envelope
from materials.water.film_tears import _gap_field


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
