"""Film meander; implementation for water.film."""
from materials.water import curtain, noise


def meander(p, s, v, d):
    """Sideways meander shape (x p.meander = metres): two along-fall scales, phase changing over a few cm across."""
    seed = p.seed + 60
    short = noise.clustered(v + 1.7 * noise.clustered(s, seed, .03, .12), seed + 1, .03, .10)
    long_ = noise.clustered(v + 2.3 * noise.clustered(s, seed + 2, .06, .25), seed + 3, .08, .25)
    return (.6 * short + .6 * long_) * (.4 + .3 * d)
