"""Photon trace; implementation for caustic_photons."""
import json
import math
import numpy as np
from effects.caustics.photon_grid import GRID


def _fresnel(cos_i, eta):
    """Unpolarised dielectric Fresnel. eta = n1/n2. Returns (R, cos_t) ; R = 1 on TIR."""
    sin2_t = eta * eta * (1.0 - cos_i * cos_i)
    if sin2_t >= 1.0:
        return 1.0, 0.0
    cos_t = math.sqrt(1.0 - sin2_t)
    rs = (eta * cos_i - cos_t) / (eta * cos_i + cos_t)
    rp = (cos_i - eta * cos_t) / (cos_i + eta * cos_t)
    return 0.5 * (rs * rs + rp * rp), cos_t


def trace(geom_path, n, seed, source, max_bounce=40):
    """Trace n photons from `source` through the exported glass and histogram where they land (background Blender)."""
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    g = np.load(geom_path, allow_pickle=True)
    verts = [tuple(v) for v in g["verts"]]
    faces = [list(f) for f in g["faces"]]
    surf, etas = g["surf"], g["eta"]
    ax, ay = float(g["axis"][0]), float(g["axis"][1])
    if "grid" in g.files:                     # the grid stored with the geometry wins
        GRID.update(json.loads(str(g["grid"])))
    bvh = BVHTree.FromPolygons(verts, faces)
    rng = np.random.default_rng(seed)
    res, x0, y0, size, zt = GRID["res"], GRID["x0"], GRID["y0"], GRID["size"], GRID["z"]
    cell = size / res
    grid = np.zeros((res, res), dtype=np.float64)
    centre = Vector((ax, ay, float(np.mean([v[2] for v in verts]))))   # aim at the glass
    Z = Vector((0, 0, 1))
    launched_power = 0.0
    landed_power = 0.0
    touched = 0
    touched_power = 0.0

    if source["type"] == "sun":
        d_sun = Vector(source["dir"]).normalized()
        u = d_sun.orthogonal().normalized()
        v = d_sun.cross(u)
        R_launch = 0.10                                   # covers the tumbler's bounding sphere
        A = math.pi * R_launch ** 2
        phi = source["irradiance"] * A / n                # W per photon
        cone = math.radians(source["half_angle_deg"])
    else:
        lc, ln = Vector(source["centre"]), Vector(source["normal"]).normalized()
        lu = ln.orthogonal().normalized()
        lv = ln.cross(lu)
        L_size = source["size"]
        A_t, R_t = math.pi * 0.10 ** 2, 0.10

    for i in range(n):
        if source["type"] == "sun":
            r, a = R_launch * math.sqrt(rng.random()), 2 * math.pi * rng.random()
            o = centre + u * (r * math.cos(a)) + v * (r * math.sin(a)) + d_sun * 0.6
            # direction: uniform inside the solar disc
            ca = 1.0 - rng.random() * (1.0 - math.cos(cone))
            sa, b = math.sqrt(max(0.0, 1 - ca * ca)), 2 * math.pi * rng.random()
            w = -(d_sun * ca + u * (sa * math.cos(b)) + v * (sa * math.sin(b)))
            p_w = phi
        else:
            o = lc + lu * ((rng.random() - 0.5) * L_size) + lv * ((rng.random() - 0.5) * L_size)
            r, a = R_t * math.sqrt(rng.random()), 2 * math.pi * rng.random()
            dvec = centre - o
            tu = dvec.normalized().orthogonal().normalized()
            tv = dvec.normalized().cross(tu)
            tgt = centre + tu * (r * math.cos(a)) + tv * (r * math.sin(a))
            w = (tgt - o)
            d2 = w.length_squared
            w.normalize()
            cos_l = max(0.0, w.dot(ln))
            cos_t = abs(w.dot(dvec.normalized()))
            p_w = source["power"] * A_t * cos_l * cos_t / (math.pi * d2 * n)
        launched_power += p_w
        hit_any = False
        for _ in range(max_bounce):
            loc, nf, idx, dist = bvh.ray_cast(o, w, 3.0)
            if loc is None:
                break
            hit_any = True
            # smooth normal for a surface of revolution: re-aim the horizontal part radially
            rad = Vector((loc.x - ax, loc.y - ay, 0.0))
            if rad.length > 1e-7:
                rad.normalize()
                h = math.copysign(math.hypot(nf.x, nf.y), nf.x * rad.x + nf.y * rad.y)
                nrm = (rad * h + Z * nf.z).normalized()
            else:
                nrm = nf
            e = float(etas[surf[idx]])
            cos_i = -w.dot(nrm)
            if cos_i > 0:          # front side: front medium -> back medium
                eta, nn = 1.0 / e, nrm
            else:
                eta, nn, cos_i = e, -nrm, -cos_i
            R, cos_t = _fresnel(cos_i, eta)
            if rng.random() < R:
                w = (w + nn * (2.0 * cos_i)).normalized()
            else:
                w = (w * eta + nn * (eta * cos_i - cos_t)).normalized()
            o = loc + w * 1e-6
        if not hit_any:
            continue               # direct light: Cycles already renders it
        touched += 1
        touched_power += p_w
        if w.z < 0:
            t = (zt - o.z) / w.z
            if t > -1e-4:
                px, py = o.x + w.x * t, o.y + w.y * t
                ix, iy = int((px - x0) / cell), int((py - y0) / cell)
                if 0 <= ix < res and 0 <= iy < res:
                    grid[iy, ix] += p_w
                    landed_power += p_w
    return grid, {"launched_W": launched_power, "touched_W": touched_power, "landed_W": landed_power,
                  "touched": touched, "n": n}
