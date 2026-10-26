"""Glass assembly; implementation for glassware."""
from materials.shared.pbr import dielectric
from materials.glass.tumbler_profiles import tumbler_profiles
from materials.glass.lathe_geometry import lathe


N_GLASS, N_WATER = 1.52, 1.333


def glass_of_water(centre=(0.0, 0.0), z0=0.73, water_h=0.095, segments=256, lift=0.0001):
    """Build the three surfaces; returns dict of objects and profile info."""
    from mathutils import Vector
    outer, iface, top, info = tumbler_profiles(z0=z0 + lift, water_h=water_h)
    c = Vector((centre[0], centre[1], 0))
    radial = lambda p: Vector((p.x - c.x, p.y - c.y, 0)).normalized() if (p.xy - c.xy).length > 1e-6 else Vector((0, 0, -1))
    # glass votes: outer wall/foot should face away from the axis/down; the inner wall (closer to
    # the axis than the outer wall at that height) faces the cavity -- count only outer faces.
    def glass_hint(p):
        r = (p.xy - c.xy).length
        if p.z < z0 + lift + 0.001:
            return Vector((0, 0, -1))
        return radial(p) if r > outer_r_at(p.z) - 0.0005 else Vector((0, 0, 0))
    def outer_r_at(z):
        return 0.035 + (0.050 - 0.035) * (z - z0 - lift) / 0.155
    glass = lathe("GLASS_TUMBLER", outer, centre, segments, normal_hint=glass_hint)
    # interface front = water side, i.e. pointing into the cavity (toward the axis / upward)
    inter = lathe("GLASS_WATER_INTERFACE", iface, centre, segments, normal_hint=lambda p: -radial(p))
    water = lathe("WATER_SURFACE", top, centre, segments, normal_hint=lambda p: Vector((0, 0, 1)))
    glass.data.materials.append(dielectric("GLASS_SODA_LIME", N_GLASS, (0.985, 1.0, 0.99)))
    inter.data.materials.append(dielectric("GLASS_TO_WATER", N_GLASS / N_WATER))
    water.data.materials.append(dielectric("WATER", N_WATER))
    for ob in (glass, inter, water):
        ob.cycles.is_caustics_caster = True
    return {"glass": glass, "interface": inter, "water": water, **info}


def glass_of_water_mnee(centre=(0.0, 0.0), z0=0.73, water_h=0.095, segments=256, lift=0.0001,
                        gap=0.00005):
    """Native-caustics build: every refractive surface is an MNEE caster and no sun path crosses
    more than 4 interfaces (Cycles MNEE limit). Below the waterline the thin wall is merged into
    the water (a 3 mm parallel wall barely deviates rays: air->glass->water ~= air->water).
      WATER_BODY   IOR 1.333: meniscus top, annulus under the wall, OUTER wall to the base
      GLASS_SHELL  IOR 1.52 : the tumbler wall above the waterline + rounded rim (closed ring)
      GLASS_BASE   IOR 1.52 : the thick foot (closed)
    Visible to the camera AND casting caustics -- one view layer."""
    from mathutils import Vector
    outer, iface, top, info = tumbler_profiles(z0=z0 + lift, water_h=water_h)
    zb = z0 + lift
    zi = zb + 0.015
    zc = info["contact"]
    r_out = lambda z: 0.035 + (0.050 - 0.035) * (z - zb) / 0.155
    r_in = lambda z: 0.03345 + (0.047 - 0.03345) * (z - zi) / (zb + 0.155 - zi)

    # water: meniscus centre -> contact (r_in) -> annulus to r_out -> outer wall down -> floor centre
    water = [p for p in top] + [(r_out(zc) , zc)]
    water += [(r_out(zc + (zi + gap - zc) * i / 30), zc + (zi + gap - zc) * i / 30) for i in range(1, 31)]
    water += [(0.0, zi + gap)]
    # shell: ring from the contact height up to the rim (outer wall up, rim, inner wall down, close)
    rim = [p for p in outer if p[1] >= zc - 1e-9 and p[0] >= r_in(p[1]) - 1e-6]
    shell = [(r_in(zc + gap), zc + gap), (r_out(zc + gap), zc + gap)]
    shell += [(r_out(z), z) for z in [zc + gap + (rim[0][1] - zc - gap) * i / 10 for i in range(1, 10)]]
    shell += rim + [(r_in(zc + gap), zc + gap)]
    # base: foot fillet + outer wall up to the floor, flat top
    base = [p for p in outer if p[1] <= zi - 1e-9]
    base += [(r_out(zi), zi), (0.0, zi)]

    c = Vector((centre[0], centre[1], 0))
    out_from = lambda zc_: (lambda p: (p - Vector((c.x, c.y, zc_))).normalized())
    w = lathe("WATER_BODY", water, centre, segments, normal_hint=out_from((zi + zc) / 2))
    def ring_hint(p):  # shell normals point away from the wall's mid-surface
        r = (p.xy - c.xy).length
        mid = (r_out(p.z) + r_in(p.z)) / 2
        if p.z > (rim[0][1] if rim else zc) and abs(r - mid) < 0.0012:
            return Vector((0, 0, 1))
        return Vector((p.x - c.x, p.y - c.y, 0)).normalized() * (1 if r > mid else -1)
    s = lathe("GLASS_SHELL", shell, centre, segments, normal_hint=ring_hint)
    b = lathe("GLASS_BASE", base, centre, segments, normal_hint=out_from((zb + zi) / 2))
    w.data.materials.append(dielectric("WATER", N_WATER))
    for ob in (s, b):
        ob.data.materials.append(dielectric("GLASS_SODA_LIME", N_GLASS, (0.985, 1.0, 0.99)))
    for ob in (w, s, b):
        ob.cycles.is_caustics_caster = True
    return {"water": w, "shell": s, "base": b, **info}
