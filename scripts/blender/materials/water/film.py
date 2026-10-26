"""Free-falling film as a field map on the ballistic carrier
(references/materials/water/water-free-falling-film.md §3.3-3.8).

Coordinates (shared by every water module): s = metres along the lip, d = drop below the lip, v = fall-time
stretched depth (curtain.effective_depth). film_surfaces() evaluates every layer on an s x d grid and returns the
front and back skins of one water body plus the fields fragments and foot need. Each layer is its own term with
its own strength in FilmParams (RULES MAT_07); defaults are starting values to size from the shot (RULES MAT_03).
"""

# Compatibility imports; each implementation has one owner (GOV_04).
from materials.water.film_config import FilmParams, FilmFields  # noqa: F401
from materials.water.film_zones import zones  # noqa: F401
from materials.water.film_swell import swell_field  # noqa: F401
from materials.water.film_waves import _wave_train, roll_waves  # noqa: F401
from materials.water.film_meander import meander  # noqa: F401
from materials.water.film_ribbons import _ribbon_seed, _ribbon_base, _ribbon, ribbon_envelope  # noqa: F401
from materials.water.film_tears import tear_value, _gap_field  # noqa: F401
from materials.water.film_build import film_surfaces  # noqa: F401
from dataclasses import dataclass

import numpy as np

from materials.water import curtain, noise


# ---------------------------------------------------------------- layers (numpy, sheet coordinates)


# ---------------------------------------------------------------- assembly

