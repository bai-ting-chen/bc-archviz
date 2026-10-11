"""Glass of water built for correct refraction in Cycles (no nested-IOR priority there).

Three interfaces, each its own surface, normals defining which medium is in front:
  GLASS      air  -> glass   IOR 1.52    outer wall, rounded rim, inner wall ABOVE the water
  INTERFACE  water | glass   IOR 1.52/1.33 = 1.143 (front = water side, back = glass side)
                             inner wall BELOW the water + curved inner floor
  WATER_TOP  air  -> water   IOR 1.33    free surface with a capillary meniscus
GLASS + INTERFACE enclose the glass solid; INTERFACE + WATER_TOP enclose the water.
"""
import math

import bpy

N_GLASS, N_WATER = 1.52, 1.333


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


def lathe(name, profile, centre, segments=256, normal_hint=None):
    """Revolve an (r, z) polyline about the Z axis through `centre`. Points with r == 0 become a
    single pole vertex. `normal_hint(p)` -> desired normal direction at point p (to orient)."""
    import bmesh
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        if r < 1e-9:
            rings.append([bm.verts.new((centre[0], centre[1], z))])
        else:
            rings.append([bm.verts.new((centre[0] + r * math.cos(2 * math.pi * k / segments),
                                        centre[1] + r * math.sin(2 * math.pi * k / segments), z))
                          for k in range(segments)])
    for a, b in zip(rings, rings[1:]):
        for k in range(segments):
            k1 = (k + 1) % segments
            if len(a) == 1:
                bm.faces.new((a[0], b[k], b[k1]))
            elif len(b) == 1:
                bm.faces.new((a[k], b[0], a[k1]))
            else:
                bm.faces.new((a[k], b[k], b[k1], a[k1]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)   # closed profiles: weld the seam ring
    bm.normal_update()
    if normal_hint:  # area-weighted vote over all faces (lathe winding is consistent)
        vote = sum(f.calc_area() * f.normal.dot(normal_hint(f.calc_center_median())) for f in bm.faces)
        if vote < 0:
            bmesh.ops.reverse_faces(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def dielectric(name, ior, tint=(1, 1, 1)):
    """Kept for existing scripts: archviz.dielectric."""
    import archviz
    return archviz.dielectric(name, ior, tint)


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
