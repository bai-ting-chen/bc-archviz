"""Night-interior recipes: artificial lights in real lumens, polished
stone, stone tiles, steel, pool water with depth tint, steam.

Photometry follows archviz.LM_PER_W (683 lm per Blender W), the same constant the physical camera
uses, so light power and exposure stay consistent. Measured in Cycles 5.2 (scripts/controls/lighting/light_units.py):
  * point / spot: power is for the FULL sphere; the spot cone only masks it
    -> a fixture putting F lm into a cone of full angle a needs P = F/683 * 4pi / (2pi(1 - cos a/2)).
  * area: Lambert emitter, P = total emitted flux (E on axis = P / (pi d^2)); `spread` focuses it.
  * IES: Cycles uses 177.83 lm/W internally -> point light power 177.83/683 (ies_light, IES_POWER).
"""

# Compatibility imports; each implementation has one owner (GOV_04).
from scene.lighting.light_objects import _light_obj, _warm  # noqa: F401
from scene.lighting.light_fixtures import downlight, led_strip, panel_light  # noqa: F401
from scene.lighting.ies_profile import ies_read  # noqa: F401
from scene.lighting.ies_fixture import IES_POWER, ies_light  # noqa: F401
from scene.lighting.emitter_shading import lens_luminance, lit_once, emitter, emitter_dots  # noqa: F401
import math
import os

import bpy

from core.archviz import LM_PER_W
from materials.shared.nodes import G
from materials.shared.nodes import sock

# --- lights ---------------------------------------------------------------------------------


# --- IES photometry (scripts/controls/lighting/ies_units.py) ---------------------------------------------
# Cycles converts the file's candela with 4pi/177.83 (D65 efficacy, intern/cycles/util/ies.cpp),
# including its multiplier and ballast factors, then multiplies by the light's power/(4pi). On a
# POINT or SPOT light, power 177.83/683 W therefore reproduces the file's candela in the 683 lm/W
# convention (measured 0.999). On an AREA light the profile multiplies a Lambert emitter: 4x on
# axis and cosine-weighted, so it is no longer the measured distribution -- use a point/spot.
# Orientation: nadir (V 0) = light -Z, C0 plane = light -Y, C90 = light -X.


# --- materials ------------------------------------------------------------------------------
