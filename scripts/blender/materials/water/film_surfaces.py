"""Film build; implementation for water.falling_film."""
import numpy as np
from materials.water import ballistic_sheet, seeded_noise
from materials.water.film_config import FilmFields
from materials.water.film_zones import zones
from materials.water.film_swell import swell_field
from materials.water.film_waves import roll_waves
from materials.water.film_meander import meander
from materials.water.film_ribbons import ribbon_envelope
from materials.water.film_tears import _gap_field


def film_surfaces(lip, flow, params, s, drop_m):
    """Evaluate every layer on the grid s x drop_m (metres) and return FilmFields."""
    S, D, P, normal = ballistic_sheet.carrier_grid(lip, flow, s, drop_m)
    V = ballistic_sheet.effective_depth(flow, S, D, params.stretch_exponent, params.stretch_reference_m)
    stream = (ballistic_sheet.stream_factor(flow, S, D) - 1) / max(flow.stream_variation, 1e-6)
    h = ballistic_sheet.sheet_thickness_m(flow, S, D)

    env_front, env_back = ribbon_envelope(params, S, V, h)
    relief_front = np.maximum(env_front - h / 2, 0)
    relief_back = np.minimum(env_back + h / 2, 0)
    zone = zones(params, S, V, stream)
    varicose = 1 + params.swell_thickness_variation * swell_field(S, V, params.seed + 41)
    sinuous = params.swell_amplitude_m * swell_field(S, V, params.seed + 40)
    front = (h / 2 + params.ribbon_relief_strength * zone * relief_front) * varicose + params.wave_amplitude_m * roll_waves(params, S, V, D)
    back = (-h / 2 + params.ribbon_relief_strength * zone * relief_back) * varicose

    start = .38 * lip.drop_m if params.tear_start_m is None else params.tear_start_m
    lateral = params.meander_amplitude_m * meander(params, S, V, D)
    gap = _gap_field(params, lip, s, S, D, V, lateral, start)
    taper = np.sqrt(np.clip(gap / params.tear_taper_range, 0, 1))                  # rounded rim, zero thickness at the tear
    bead = params.rim_bead_m * np.exp(-((gap - .03) / .03) ** 2) * (D > start)
    mid = (front + back) / 2 + sinuous
    half = (front - back) / 2 * taper + .5 * bead * taper

    shift = lip.along_axis[None, None, :] * lateral[..., None]
    F = P + normal * (mid + half)[..., None] + shift
    B = P + normal * (mid - half)[..., None] + shift
    keep = gap > 0
    folded = (np.diff(F @ lip.along_axis, axis=1) <= 0) & keep[:, 1:] & keep[:, :-1]
    return FilmFields(front=F, back=B, keep=keep, gap=gap, normal=normal, along_lip_m=S, drop_m=D, stretched_depth_m=V,
                      tear_start_m=start, folded_fraction=float(folded.mean()))
