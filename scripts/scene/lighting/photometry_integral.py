"""Integrate type-C candela over solid angle."""
import math


def lumens(v, h, rows):
    """Integrate type-C candela rows over their vertical and horizontal angles."""
    def plane(r):
        return sum((r[j] * math.sin(math.radians(v[j])) + r[j + 1] * math.sin(math.radians(v[j + 1])))
                   / 2 * math.radians(v[j + 1] - v[j]) for j in range(len(v) - 1))
    if len(h) == 1:
        return 2 * math.pi * plane(rows[0])
    return sum((plane(rows[k]) + plane(rows[k + 1])) / 2 * math.radians(h[k + 1] - h[k])
               for k in range(len(h) - 1)) * 360.0 / (h[-1] - h[0])
