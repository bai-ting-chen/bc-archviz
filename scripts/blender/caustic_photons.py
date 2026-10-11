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
import json
import math
import sys

import numpy as np

SURFACES = {"GLASS_TUMBLER": 1.52, "GLASS_WATER_INTERFACE": 1.52 / 1.333, "WATER_SURFACE": 1.333}
GRID = {"x0": -0.45, "y0": -0.45, "size": 0.90, "res": 900, "z": 0.7300}   # 1 mm cells


# --- 1. geometry export (inside Blender) -----------------------------------------------------

def export_geometry(path, surfaces=SURFACES, axis=(0.0, 0.0), grid=None):
    """`surfaces` {object: eta}; `grid` overrides GRID (receiver plane x0, y0, size, res, z) and
    is stored with the geometry so the tracer, bake and material all use the same one."""
    import bpy
    if grid:
        GRID.update(grid)
    V, F, S, E = [], [], [], []
    off = 0
    for sid, (name, eta) in enumerate(surfaces.items()):
        ob = bpy.data.objects[name]
        mw = ob.matrix_world
        V += [tuple(mw @ v.co) for v in ob.data.vertices]
        for p in ob.data.polygons:
            F.append([off + i for i in p.vertices])
            S.append(sid)
        E.append(eta)
        off += len(ob.data.vertices)
    np.savez(path, verts=np.array(V), faces=np.array(F, dtype=object), surf=np.array(S),
             eta=np.array(E), axis=np.array(axis), grid=json.dumps(GRID), allow_pickle=True)
    return {"verts": len(V), "faces": len(F)}


# --- 2. tracer (runs in a background Blender for mathutils.bvhtree) -------------------------

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
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    g = np.load(geom_path, allow_pickle=True)
    verts = [tuple(v) for v in g["verts"]]
    faces = [list(f) for f in g["faces"]]
    surf, etas = g["surf"], g["eta"]
    ax, ay = float(g["axis"][0]), float(g["axis"][1])
    if "grid" in g.files:
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


# --- 3. bake (inside Blender: writes a float EXR) -------------------------------------------

def bake_irradiance(npy_paths, exr_path, sigma_cells=1.0):
    import bpy
    # each worker's grid is already a full estimate (photon power uses that worker's own n): AVERAGE
    grid = sum(np.load(p) for p in npy_paths) / len(npy_paths)
    cell = GRID["size"] / GRID["res"]
    E = grid / (cell * cell)                                  # W/m2 per cell
    if sigma_cells > 0:                                       # photon-map style kernel
        k = int(3 * sigma_cells) + 1
        x = np.arange(-k, k + 1)
        g1 = np.exp(-0.5 * (x / sigma_cells) ** 2)
        g1 /= g1.sum()
        E = np.apply_along_axis(lambda r: np.convolve(r, g1, mode="same"), 1, E)
        E = np.apply_along_axis(lambda c: np.convolve(c, g1, mode="same"), 0, E)
    res = GRID["res"]
    img = bpy.data.images.get("CAUSTIC_E") or bpy.data.images.new("CAUSTIC_E", res, res,
                                                                   float_buffer=True, alpha=False)
    px = np.zeros((res, res, 4), dtype=np.float32)
    px[..., 0] = px[..., 1] = px[..., 2] = E
    px[..., 3] = 1.0
    img.pixels.foreach_set(px.ravel())
    # NOT img.save(): for generated float images it bakes the scene view transform + exposure into
    # the file (a 100 W/m2 spike came back as 7.1). save_render with explicit EXR settings is exact.
    s = bpy.context.scene.render.image_settings
    prev = (s.file_format, s.color_depth, s.exr_codec)
    s.file_format, s.color_depth, s.exr_codec = "OPEN_EXR", "32", "ZIP"
    img.save_render(exr_path)
    s.file_format, s.color_depth, s.exr_codec = prev
    img.filepath_raw = exr_path
    img.source = "FILE"
    img.colorspace_settings.name = "Non-Color"
    img.reload()
    return {"E_max_W_m2": float(E.max()), "E_p99_W_m2": float(np.quantile(E[E > 0], 0.99)) if (E > 0).any() else 0.0}


# --- 4. feed the map back into the receiver's material --------------------------------------

def add_caustic_light(mat, exr_path, scale=1.0, albedo_label="Pine + satin varnish coat"):
    """Adds Emission = albedo * E / pi on up-facing faces, E sampled at world XY from the map.
    `albedo_label`: label of the receiver's BSDF whose Base Color input carries the albedo (the
    default is study_materials.coated_wood's)."""
    import bpy
    nt = mat.node_tree
    for n in [n for n in nt.nodes if n.label.startswith("caustic map")]:
        nt.nodes.remove(n)
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    surf_src = out.inputs["Surface"].links[0].from_socket
    albedo_src = next(n for n in nt.nodes if n.label == albedo_label).inputs["Base Color"].links[0].from_socket
    N = lambda kind, loc, label: _node(nt, kind, loc, "caustic map: " + label)
    geo = N("ShaderNodeNewGeometry", (-400, -1600), "position")
    mp = N("ShaderNodeMapping", (-200, -1600), "world XY -> map UV")
    mp.inputs["Location"].default_value = (-GRID["x0"] / GRID["size"], -GRID["y0"] / GRID["size"], 0)
    mp.inputs["Scale"].default_value = (1 / GRID["size"], 1 / GRID["size"], 1)
    nt.links.new(geo.outputs["Position"], mp.inputs["Vector"])
    tex = N("ShaderNodeTexImage", (0, -1600), "irradiance W/m2")
    tex.image = bpy.data.images.load(exr_path, check_existing=True)
    tex.image.colorspace_settings.name = "Non-Color"
    tex.extension, tex.interpolation = "CLIP", "Cubic"
    nt.links.new(mp.outputs["Vector"], tex.inputs["Vector"])
    up = N("ShaderNodeSeparateXYZ", (0, -1850), "normal z")
    nt.links.new(geo.outputs["Normal"], up.inputs["Vector"])
    upm = N("ShaderNodeMapRange", (200, -1850), "up-facing only")
    upm.inputs["From Min"].default_value, upm.inputs["From Max"].default_value = 0.85, 0.95
    nt.links.new(up.outputs["Z"], upm.inputs["Value"])
    rad = N("ShaderNodeMath", (250, -1600), "E / pi x scale")
    rad.operation = "MULTIPLY"
    rad.inputs[1].default_value = scale / math.pi
    nt.links.new(tex.outputs["Color"], rad.inputs[0])
    m2 = N("ShaderNodeMath", (420, -1700), "on top only")
    m2.operation = "MULTIPLY"
    nt.links.new(rad.outputs[0], m2.inputs[0])
    nt.links.new(upm.outputs["Result"], m2.inputs[1])
    col = N("ShaderNodeMix", (600, -1550), "albedo x E/pi")
    col.data_type, col.blend_type = "RGBA", "MULTIPLY"
    col.inputs["Factor"].default_value = 1.0
    nt.links.new(albedo_src, next(s for s in col.inputs if s.name == "A" and s.enabled))
    em = N("ShaderNodeEmission", (800, -1550), "reflected caustic light")
    nt.links.new(next(s for s in col.outputs if s.name == "Result" and s.enabled), em.inputs["Color"])
    nt.links.new(m2.outputs[0], em.inputs["Strength"])
    # the Mix colour's B is driven by a grey value = 1 (albedo * 1), strength carries E/pi
    next(s for s in col.inputs if s.name == "B" and s.enabled).default_value = (1, 1, 1, 1)
    add = N("ShaderNodeAddShader", (1000, -300), "surface + caustic")
    nt.links.new(surf_src, add.inputs[0])
    nt.links.new(em.outputs["Emission"], add.inputs[1])
    nt.links.new(add.outputs["Shader"], out.inputs["Surface"])
    return mat


def _node(nt, kind, loc, label):
    n = nt.nodes.new(kind)
    n.location, n.label = loc, label
    return n


if __name__ == "__main__" and "--" in sys.argv:
    a = sys.argv[sys.argv.index("--") + 1:]
    if a[0] == "trace":
        grid, stats = trace(a[1], int(a[3]), int(a[4]), json.loads(a[5]))
        np.save(a[2], grid)
        print("TRACE_STATS " + json.dumps(stats))
