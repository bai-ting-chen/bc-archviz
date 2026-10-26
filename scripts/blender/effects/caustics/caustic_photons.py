"""Forward photon tracing for caustics that Cycles cannot converge (sun-sized sources through
glassware). Photons leave the light, refract/reflect through the exact glass/water meshes
(Snell + unpolarised Fresnel, Russian roulette, TIR) and land on the table plane. The density
becomes an irradiance map (W/m2) that the table's material adds as Lambertian reflected light
(rho * E / pi) -- the same thing a renderer's caustic photon map does.

Use:
  1. export_geometry(path, surfaces, axis, grid) -- in Blender: glass surfaces + IOR + receiver
                                         grid to .npz (defaults match glassware.glass_of_water)
  2. blender -b --factory-startup --python caustic_photons.py -- trace <geom.npz> <out.npy>
         <n_photons> <seed> <json source>         (run several in parallel)
  3. bake_irradiance(npy_paths, exr_path, sigma_cells) -- merge, kernel-smooth, float EXR (W/m2)
  4. add_caustic_light(mat, exr_path, scale, albedo_label) -- Emission = albedo * E / pi, up faces

Source json: {"type": "sun", "dir": [x,y,z] (towards light), "half_angle_deg": 0.2665,
              "irradiance": W/m2 perpendicular}
          or {"type": "area", "centre": [...], "normal": [...] (facing the scene),
              "size": m, "power": W}
"""

# Compatibility imports; each implementation has one owner (GOV_04).
from effects.caustics.photon_grid import SURFACES, GRID, _stem, _save_grid, _load_grid  # noqa: F401
from effects.caustics.photon_geometry import export_geometry  # noqa: F401
from effects.caustics.photon_trace import _fresnel, trace  # noqa: F401
from effects.caustics.photon_bake import bake_irradiance  # noqa: F401
from effects.caustics.photon_shading import add_caustic_light  # noqa: F401
import json
import math
import os
import sys

import numpy as np


# --- 1. geometry export (inside Blender) -----------------------------------------------------


# --- 2. tracer (runs in a background Blender for mathutils.bvhtree) -------------------------


# --- 3. bake (inside Blender: writes a float EXR) -------------------------------------------


# --- 4. feed the map back into the receiver's material --------------------------------------


if __name__ == "__main__" and "--" in sys.argv:
    a = sys.argv[sys.argv.index("--") + 1:]
    if a[0] == "trace":
        grid, stats = trace(a[1], int(a[3]), int(a[4]), json.loads(a[5]))
        np.save(a[2], grid)
        _save_grid(a[2])
        print("TRACE_STATS " + json.dumps(stats))
