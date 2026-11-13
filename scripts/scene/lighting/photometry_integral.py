"""Integrate type-C candela over solid angle."""
import math


def lumens(vertical_angles_deg, horizontal_angles_deg, rows):
    """Integrate type-C candela rows over their vertical and horizontal angles."""
    def plane(r):
        return sum((r[j] * math.sin(math.radians(vertical_angles_deg[j])) + r[j + 1] * math.sin(math.radians(vertical_angles_deg[j + 1])))
                   / 2 * math.radians(vertical_angles_deg[j + 1] - vertical_angles_deg[j]) for j in range(len(vertical_angles_deg) - 1))
    if len(horizontal_angles_deg) == 1:
        return 2 * math.pi * plane(rows[0])
    return sum((plane(rows[k]) + plane(rows[k + 1])) / 2 * math.radians(horizontal_angles_deg[k + 1] - horizontal_angles_deg[k])
               for k in range(len(horizontal_angles_deg) - 1)) * 360.0 / (horizontal_angles_deg[-1] - horizontal_angles_deg[0])
