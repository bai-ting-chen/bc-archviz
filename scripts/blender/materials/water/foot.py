"""Where falling water meets a pool: impacts, crowns, foam, floating bubbles, splash
(references/materials/water/water-splash.md, water-foam.md).

Works in lip-local coordinates (s along the lip, o outward from the wall face) and returns world-space geometry
as (vertices, faces) or drop arrays (N, 5); water.mesh makes the objects. Impacts come from the water itself (the
film's bottom row weighted by thickness, plus drops reaching the pool), so every element clusters where the
water lands instead of lining up along a drawn line.
"""

# Compatibility imports; each implementation has one owner (GOV_04).
from materials.water.foot_config import EMPTY_MESH, FootParams  # noqa: F401
from materials.water.foot_drift import _span, _drift  # noqa: F401
from materials.water.foot_impacts import impacts  # noqa: F401
from materials.water.foot_crowns import crowns  # noqa: F401
from materials.water.foot_foam import _fleck, foam  # noqa: F401
from materials.water.foot_bubbles import _dome, bubbles  # noqa: F401
from materials.water.foot_splash import splash  # noqa: F401
from dataclasses import dataclass

import numpy as np


# ---------------------------------------------------------------- impacts


# ---------------------------------------------------------------- crowns


# ---------------------------------------------------------------- foam and bubbles


# ---------------------------------------------------------------- splash

