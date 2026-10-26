"""Terrain height; implementation for terrain."""
import math


def height(x, y, centre, pad_half, pad_z=-0.03, crest=1.5, fall=6.0, run=40.0):
    """Python twin of landform_group without the noise terms (e.g. to set a camera's eye height)."""
    qx = abs(x - centre[0]) - pad_half[0]
    qy = abs(y - centre[1]) - pad_half[1]
    d = math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0)
    t = min(max((d - crest) / run, 0), 1)
    return pad_z - fall * t * t * (3 - 2 * t)
