"""Tumbler profiles; implementation for glassware."""
import math


def _arc(cx, cz, r, a0, a1, n):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cz + r * math.sin(a0 + (a1 - a0) * i / n))
            for i in range(n + 1)]


def tumbler_profiles(z0=0.73, r_out_b=0.035, r_out_t=0.050, r_in_b=0.03345, r_in_t=0.047,
                     base=0.015, height=0.155, rim_r=0.0015, foot_fillet=0.002,
                     floor_fillet=0.006, water_h=0.095, meniscus=0.002, cap_len=0.0027):
    """(r, z) polylines. Returns glass, interface, water-top profiles (each ordered so that the
    lathed normals face the 'front' medium after `lathe`'s orientation fix)."""
    zt = z0 + height
    zi = z0 + base

    def r_in(z):  # inner wall radius (straight taper)
        return r_in_b + (r_in_t - r_in_b) * (z - zi) / (zt - zi)

    def r_out(z):
        return r_out_b + (r_out_t - r_out_b) * (z - z0) / height

    zw = zi + water_h                     # flat water level
    zc = zw + meniscus                    # contact line on the wall

    # outer: centre of the foot -> foot fillet -> outer wall -> rounded rim -> inner wall down to zc
    outer = [(0.0, z0)]
    outer += _arc(r_out_b - foot_fillet, z0 + foot_fillet, foot_fillet, -math.pi / 2, 0.0, 6)
    zr = zt - rim_r
    for i in range(1, 25):
        z = z0 + foot_fillet + (zr - z0 - foot_fillet) * i / 24
        outer.append((r_out(z), z))
    rc = (r_out(zr) + r_in(zr)) / 2
    outer += _arc(rc, zr, (r_out(zr) - r_in(zr)) / 2, 0.0, math.pi, 12)[1:]
    for i in range(1, 13):
        z = zr + (zc - zr) * i / 12
        outer.append((r_in(z), z))

    # interface: contact line -> inner wall -> floor fillet -> centre of the inner floor
    iface = [(r_in(zc), zc)]
    zf = zi + floor_fillet
    for i in range(1, 25):
        z = zc + (zf - zc) * i / 24
        iface.append((r_in(z), z))
    iface += _arc(r_in(zf) - floor_fillet, zf, floor_fillet, 0.0, -math.pi / 2, 8)[1:]
    iface.append((0.0, zi))

    # water top: centre -> wall, z = zw + m * exp(-(R - r) / capillary length)
    R = r_in(zc)
    top = [(R * i / 60, zw + meniscus * math.exp(-(R - R * i / 60) / cap_len)) for i in range(61)]
    top[-1] = (R, zc)
    return outer, iface, top, {"water_level": zw, "contact": zc, "r_contact": R}
