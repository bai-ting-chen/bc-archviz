"""Film meander; implementation for water.falling_film."""
from materials.water import ballistic_sheet, seeded_noise


def meander(params, s, stretched_depth_m, drop_m):
    """Sideways meander shape (x params.meander = metres): two along-fall scales, phase changing over a few cm across."""
    seed = params.seed + 60
    short = seeded_noise.clustered_noise(stretched_depth_m + 1.7 * seeded_noise.clustered_noise(s, seed, .03, .12), seed + 1, .03, .10)
    long_ = seeded_noise.clustered_noise(stretched_depth_m + 2.3 * seeded_noise.clustered_noise(s, seed + 2, .06, .25), seed + 3, .08, .25)
    return (.6 * short + .6 * long_) * (.4 + .3 * drop_m)
