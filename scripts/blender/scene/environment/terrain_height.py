"""Terrain height; implementation for terrain."""
import math


def height(x, y, centre, pad_half_size_m, pad_height_m=-0.03, crest_distance_m=1.5, fall_height_m=6.0, slope_run_m=40.0):
    """Python twin of landform_group without the noise terms (e.g. to set a camera's eye height)."""
    qx = abs(x - centre[0]) - pad_half_size_m[0]
    qy = abs(y - centre[1]) - pad_half_size_m[1]
    d = math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0)
    t = min(max((d - crest_distance_m) / slope_run_m, 0), 1)
    return pad_height_m - fall_height_m * t * t * (3 - 2 * t)
