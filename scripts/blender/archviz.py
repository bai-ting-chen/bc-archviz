"""Archviz helpers that run inside Blender (via the Blender MCP or the Python console).

Rhino supplies geometry only. Everything visual -- materials, lighting, cameras, render
settings -- is built here, from the local Poly Haven library.

    import os, sys; sys.path.insert(0, os.path.expanduser(r"~\\.claude\\skills\\blender-archviz\\scripts\\blender"))
    import archviz
"""
import json
import math
import os

import bpy

# Code lives in the skill; assets live in the current project's library/ (polyhaven/, local/).
# The project: set_project(path), else env ARCHVIZ_PROJECT, else the nearest folder holding a
# library/ above the open .blend or the working directory.
_PROJECT = os.environ.get("ARCHVIZ_PROJECT")


def set_project(path):
    global _PROJECT
    _PROJECT = os.path.abspath(path)


def project_root():
    if _PROJECT:
        return _PROJECT
    starts = [os.path.dirname(bpy.data.filepath)] if bpy.data.filepath else []
    for d in starts + [os.getcwd()]:
        while True:
            if os.path.isdir(os.path.join(d, "library")):
                return d
            if os.path.dirname(d) == d:
                break
            d = os.path.dirname(d)
    raise RuntimeError("no project library/ found: call archviz.set_project(<project folder>)")


def library(*parts):
    """Path inside the project's library/, e.g. library("polyhaven", "hdris", hdri_id)."""
    return os.path.join(project_root(), "library", *parts)

BUMP_DISTANCE = 0.004  # metres of height for a full-range displacement map, used as bump only


# --- materials -----------------------------------------------------------------------------

def _img(nodes, path, colorspace, loc):
    n = nodes.new("ShaderNodeTexImage")
    n.image = bpy.data.images.load(path, check_existing=True)
    n.image.colorspace_settings.name = colorspace
    n.projection = "BOX"  # world-space box mapping: no UVs needed on Rhino meshes
    n.projection_blend = 0.2
    n.location = loc
    return n


def pbr_material(tex_id, name=None, scale=1.0, tint=None):
    """Material from a Poly Haven texture folder, box-mapped in world space at real-world size.

    scale: multiplies the texture's real-world size (2.0 = twice as large).
    tint: optional (r, g, b) multiplied into the base color.
    """
    folder = library("polyhaven", "textures", tex_id)
    meta = json.load(open(os.path.join(folder, "meta.json"), encoding="utf-8"))
    maps = {k: os.path.join(folder, v) for k, v in meta["maps"].items()}
    w_mm, h_mm = meta.get("dimensions_mm", [1000, 1000])

    mat = bpy.data.materials.get(name or tex_id) or bpy.data.materials.new(name or tex_id)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    N, L = nt.nodes, nt.links
    out = N.new("ShaderNodeOutputMaterial"); out.location = (900, 0)
    bsdf = N.new("ShaderNodeBsdfPrincipled"); bsdf.location = (550, 0)
    L.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    geo = N.new("ShaderNodeNewGeometry"); geo.location = (-900, 0)
    mapping = N.new("ShaderNodeMapping"); mapping.location = (-700, 0)
    mapping.inputs["Scale"].default_value = (1000 / (w_mm * scale), 1000 / (h_mm * scale), 1000 / (w_mm * scale))
    L.new(geo.outputs["Position"], mapping.inputs["Vector"])

    diff = _img(N, maps["diff"], "sRGB", (-400, 300))
    L.new(mapping.outputs["Vector"], diff.inputs["Vector"])
    if tint:
        mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        next(x for x in mix.inputs if x.name == "B" and x.enabled).default_value = (*tint, 1.0)
        mix.location = (100, 300)
        L.new(diff.outputs["Color"], next(x for x in mix.inputs if x.name == "A" and x.enabled))
        L.new(next(x for x in mix.outputs if x.name == "Result" and x.enabled), bsdf.inputs["Base Color"])
    else:
        L.new(diff.outputs["Color"], bsdf.inputs["Base Color"])

    if "arm" in maps:  # R = AO (unused, Cycles computes it), G = roughness, B = metallic
        arm = _img(N, maps["arm"], "Non-Color", (-400, 0))
        L.new(mapping.outputs["Vector"], arm.inputs["Vector"])
        sep = N.new("ShaderNodeSeparateColor"); sep.location = (100, 0)
        L.new(arm.outputs["Color"], sep.inputs["Color"])
        L.new(sep.outputs["Green"], bsdf.inputs["Roughness"])
        L.new(sep.outputs["Blue"], bsdf.inputs["Metallic"])

    # Height map as bump: correct with box mapping, unlike tangent-space normal maps.
    if "disp" in maps:
        disp = _img(N, maps["disp"], "Non-Color", (-400, -300))
        L.new(mapping.outputs["Vector"], disp.inputs["Vector"])
        bump = N.new("ShaderNodeBump"); bump.location = (100, -300)
        bump.inputs["Distance"].default_value = BUMP_DISTANCE * scale
        L.new(disp.outputs["Color"], bump.inputs["Height"])
        L.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    mat["source"] = meta["source"]
    return mat


def glass_material(name="Glass_Clear", tint=(0.92, 0.96, 0.97), roughness=0.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    b = mat.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*tint, 1.0)
    b.inputs["Roughness"].default_value = roughness
    b.inputs["IOR"].default_value = 1.52
    b.inputs["Transmission Weight"].default_value = 1.0
    return mat


def simple_material(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    b = mat.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1.0)
    b.inputs["Roughness"].default_value = roughness
    b.inputs["Metallic"].default_value = metallic
    return mat


def material_from_spec(spec):
    """spec: "ph:<tex_id>" | "glass" | {"type": "ph"|"glass"|"simple", ...kwargs}."""
    if isinstance(spec, str):
        if spec.startswith("ph:"):
            return pbr_material(spec[3:])
        if spec == "glass":
            return glass_material()
        raise ValueError(spec)
    kind = spec.pop("type")
    return {"ph": lambda **k: pbr_material(**k), "glass": glass_material, "simple": simple_material}[kind](**spec)


# --- world / lighting ----------------------------------------------------------------------

def world_hdri(hdri_id, strength=1.0, rotation_deg=0.0, res=None):
    folder = library("polyhaven", "hdris", hdri_id)
    meta = json.load(open(os.path.join(folder, "meta.json"), encoding="utf-8"))
    path = os.path.join(folder, meta["file"] if res is None else "{}_{}.hdr".format(hdri_id, res))
    world = bpy.data.worlds.get("HDRI_" + hdri_id) or bpy.data.worlds.new("HDRI_" + hdri_id)
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    coord = nt.nodes.new("ShaderNodeTexCoord"); coord.location = (-800, 0)
    mapping = nt.nodes.new("ShaderNodeMapping"); mapping.location = (-600, 0)
    mapping.inputs["Rotation"].default_value[2] = math.radians(rotation_deg)
    env = nt.nodes.new("ShaderNodeTexEnvironment"); env.location = (-350, 0)
    env.image = bpy.data.images.load(path, check_existing=True)
    bg = nt.nodes.new("ShaderNodeBackground"); bg.location = (-50, 0)
    bg.inputs["Strength"].default_value = strength
    out = nt.nodes.new("ShaderNodeOutputWorld"); out.location = (200, 0)
    nt.links.new(coord.outputs["Generated"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], env.inputs["Vector"])
    nt.links.new(env.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    world["source"] = meta["source"]
    bpy.context.scene.world = world
    return world


# --- Rhino geometry ------------------------------------------------------------------------

def import_rhino(path, collection_name=None):
    """Import a .3dm as geometry only. Layers -> nested collections, blocks -> instances,
    named views -> cameras. Any material that rides along is discarded."""
    before = set(bpy.data.materials)
    bpy.ops.import_3dm.some_data(
        filepath=path, import_layers_as_empties=False, import_instances=True,
        import_named_views=True, import_views=False, import_hidden_objects=False,
        import_hidden_layers=False, merge_by_distance=True)
    for m in set(bpy.data.materials) - before:
        bpy.data.materials.remove(m)
    root = bpy.data.collections.get(collection_name or os.path.splitext(os.path.basename(path))[0])
    for ob in root.all_objects if root else ():
        if ob.type == "MESH":
            ob.data.materials.clear()
    return root


def _ancestors(coll, parents):
    while coll:
        yield coll
        coll = parents.get(coll)


def apply_material_map(root, mapping):
    """mapping: {collection_name: material spec}. Each mesh gets the material of the nearest
    collection (its layer, a parent layer, or its block definition) that has an entry."""
    mats = {k: material_from_spec(dict(v) if isinstance(v, dict) else v) for k, v in mapping.items()}
    parents = {}
    for c in [root, *root.children_recursive]:
        for ch in c.children:
            parents[ch] = c
    report = {}
    for ob in root.all_objects:
        if ob.type != "MESH":
            continue
        for coll in ob.users_collection:
            hit = next((mats[c.name] for c in _ancestors(coll, parents) if c.name in mats), None)
            if hit:
                ob.data.materials.clear()
                ob.data.materials.append(hit)
                report.setdefault(hit.name, []).append(ob.name)
                break
        else:
            report.setdefault("<unmapped>", []).append(ob.name)
    return report


# --- camera / render -----------------------------------------------------------------------

def use_camera(name, lens=None):
    cam = bpy.data.objects[name]
    if lens:
        cam.data.lens = lens
    cam.data.sensor_width = 36
    bpy.context.scene.camera = cam
    return cam


def framing_render(root, path):
    """Fast Workbench render, one colour per layer collection -- compare with the reference
    (`scripts/refmatch.py pair --overlay`) while solving the camera. Restores the engine after."""
    import random
    sc = bpy.context.scene
    engine = sc.render.engine
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light, sc.display.shading.color_type = "STUDIO", "OBJECT"
    for o in root.all_objects:
        random.seed(sum(map(ord, o.users_collection[0].name)))
        o.color = (random.random(), random.random(), random.random(), 1)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    sc.render.engine = engine
    return path


def render_setup(width=1920, height=1080, samples=256, look="AgX - Medium High Contrast", exposure=0.0):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "GPU"
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.01
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = "OPTIX"
    sc.cycles.max_bounces = 12
    sc.cycles.transparent_max_bounces = 16
    sc.render.resolution_x, sc.render.resolution_y = width, height
    sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = look
    except TypeError:
        pass
    sc.view_settings.exposure = exposure
    sc.unit_settings.system = "METRIC"


def render_to(path):
    sc = bpy.context.scene
    sc.render.filepath = path
    sc.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
    return path


# --- UVs -----------------------------------------------------------------------------------

def directional_uv(obj, size, name="BoxUV", axis=None, along="U"):
    """Box UVs for DIRECTIONAL textures (wood grain, boards, brushed metal, vein-cut or banded
    stone, ribbed/corrugated sheet, woven fabric, long-format tiles): U follows one direction on
    every face — the object's longest dimension, or world `axis` ("X"/"Y"/"Z", e.g. "Z" for
    vertical cladding). Plain box_uv projects each face along its own dominant axis, which turns
    the image 90 deg between faces (grain along the top of a plank, across its side). Faces whose
    normal lies along that direction (end grain) get the other two axes. along="V" for textures
    whose direction runs up the image. 1 UV unit = `size` metres. Returns the axis used."""
    import bmesh
    dims = obj.dimensions
    grain = "XYZ".index(axis) if axis else max(range(3), key=lambda i: dims[i])
    mw, rot = obj.matrix_world, obj.matrix_world.to_3x3()
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    uv = bm.loops.layers.uv.get(name) or bm.loops.layers.uv.new(name)
    for f in bm.faces:
        n = (rot @ f.normal).normalized()
        ax = max(range(3), key=lambda i: abs(n[i]))
        plane = [i for i in range(3) if i != ax]
        u_ax = grain if grain in plane else plane[0]
        v_ax = next(i for i in plane if i != u_ax)
        for lp in f.loops:
            p = mw @ lp.vert.co
            uv_ = (p[u_ax] / size, p[v_ax] / size)
            lp[uv].uv = uv_ if along == "U" else (uv_[1], uv_[0])
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.uv_layers.active = obj.data.uv_layers[name]
    return "XYZ"[grain]


def box_uv(obj, size=1.0, name="BoxUV"):
    """Real-world box UVs in world space: 1 UV unit = `size` metres. Each face is projected
    along its dominant world axis, so tangent-space normal maps and UV-based displacement
    behave (unlike shader box projection, which has no tangents)."""
    import bmesh
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    uv = bm.loops.layers.uv.get(name) or bm.loops.layers.uv.new(name)
    mw = obj.matrix_world
    rot = mw.to_3x3()
    for f in bm.faces:
        n = (rot @ f.normal).normalized()
        ax = max(range(3), key=lambda i: abs(n[i]))
        for lp in f.loops:
            p = mw @ lp.vert.co
            if ax == 2:
                u, v = p.x * (1 if n.z > 0 else -1), p.y
            elif ax == 0:
                u, v = p.y * (1 if n.x > 0 else -1), p.z
            else:
                u, v = -p.x * (1 if n.y > 0 else -1), p.z
            lp[uv].uv = (u / size, v / size)
    bm.to_mesh(me)
    bm.free()
    me.uv_layers.active = me.uv_layers[name]
    me.uv_layers[name].active_render = True


def height_span_uv(obj, u_size=4.0, v_repeat=1.0, name="SpanUV"):
    """Second UV set for once-per-object maps (leak stains): u tiles every `u_size` metres
    along the face, v runs 0..v_repeat from the object's bottom to its top."""
    import bmesh
    mw = obj.matrix_world
    zs = [(mw @ v.co).z for v in obj.data.vertices]
    z0, h = min(zs), max(max(zs) - min(zs), 1e-6)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    uv = bm.loops.layers.uv.get(name) or bm.loops.layers.uv.new(name)
    rot = mw.to_3x3()
    for f in bm.faces:
        n = (rot @ f.normal).normalized()
        for lp in f.loops:
            p = mw @ lp.vert.co
            horiz = p.y if abs(n.x) > abs(n.y) else p.x
            lp[uv].uv = (horiz / u_size, (p.z - z0) / h * v_repeat)
    bm.to_mesh(obj.data)
    bm.free()


# --- physically scaled light and camera -----------------------------------------------------

LM_PER_W = 683.0  # luminous efficacy used to read Cycles radiance as photometric units


def hdri_analyse(hdri_id, rotation_deg=0.0):
    """Horizontal illuminance (lux at strength 1) and direction to the brightest region of an
    equirect HDRI, in Blender world space after a Z rotation. The sun direction is the
    luminance centroid of the top 0.05 % texels."""
    import numpy as np
    folder = library("polyhaven", "hdris", hdri_id)
    meta = json.load(open(os.path.join(folder, "meta.json"), encoding="utf-8"))
    img = bpy.data.images.load(os.path.join(folder, meta["file"]), check_existing=True)
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(h, w, 4)  # row 0 = bottom (elevation -90 deg)
    lum = 0.2126 * px[..., 0] + 0.7152 * px[..., 1] + 0.0722 * px[..., 2]
    elev = ((np.arange(h) + 0.5) / h - 0.5) * np.pi
    # Cycles equirect (direction_to_equirectangular): u = 0.5 - atan2(y, x) / 2pi
    phi = (0.5 - (np.arange(w) + 0.5) / w) * 2 * np.pi
    d_omega = (2 * np.pi / w) * (np.pi / h) * np.cos(elev)
    up = elev > 0
    E = float((lum[up] * (np.sin(elev[up]) * d_omega[up])[:, None]).sum()) * LM_PER_W
    thr = np.quantile(lum, 0.9995)
    ys, xs = np.nonzero(lum >= thr)
    wts = lum[ys, xs]
    el, ph = elev[ys], phi[xs]
    dx, dy, dz = np.cos(el) * np.cos(ph), np.cos(el) * np.sin(ph), np.sin(el)
    v = np.array([(dx * wts).sum(), (dy * wts).sum(), (dz * wts).sum()])
    v /= np.linalg.norm(v)
    # The world Mapping node rotates the lookup (s = Rz . d), so the world direction is Rz^T . s
    r = math.radians(rotation_deg)
    v = np.array([math.cos(r) * v[0] + math.sin(r) * v[1], -math.sin(r) * v[0] + math.cos(r) * v[1], v[2]])
    return {"lux_at_strength_1": E, "sun_dir": v.tolist(),
            "sun_elev_deg": math.degrees(math.asin(v[2])),
            "sun_az_deg": math.degrees(math.atan2(v[1], v[0]))}


def world_hdri_lux(hdri_id, target_lux, rotation_deg=0.0, visible=True):
    """HDRI world scaled so the upper hemisphere delivers `target_lux` on a horizontal plane."""
    info = hdri_analyse(hdri_id, rotation_deg)
    strength = target_lux / info["lux_at_strength_1"]
    world = world_hdri(hdri_id, strength=strength, rotation_deg=rotation_deg)
    world.cycles_visibility.camera = visible
    info["strength"] = strength
    return info


def ev100(iso, fstop, shutter_s):
    return math.log2(fstop ** 2 / shutter_s) - math.log2(iso / 100.0)


def physical_camera(cam_obj, iso, fstop, shutter_s, focal_mm, sensor_mm=36.0,
                    focus_distance=None, dof=True):
    """Real camera triple -> Blender. Exposure follows the saturation-based sensor model
    (pixel = L / (1.2 * 2^EV100), L in cd/m2): stops = log2(683 / 1.2) - EV100.
    The same f-stop drives depth of field, so brightness and DOF stay in sync."""
    ev = ev100(iso, fstop, shutter_s)
    cam = cam_obj.data
    cam.lens, cam.sensor_width, cam.sensor_fit = focal_mm, sensor_mm, "HORIZONTAL"
    cam.dof.use_dof = dof
    cam.dof.aperture_fstop = fstop
    if focus_distance:
        cam.dof.focus_distance = focus_distance
    sc = bpy.context.scene
    sc.camera = cam_obj
    sc.view_settings.exposure = math.log2(LM_PER_W / 1.2) - ev
    return {"ev100": ev, "exposure_stops": sc.view_settings.exposure}


def straighten_verticals(cam_obj):
    """Architectural shift lens: level the camera (pitch 90 deg) and recover the framing
    with vertical lens shift, so verticals stay parallel."""
    from mathutils import Vector
    cam = cam_obj.data
    fwd = cam_obj.matrix_world.to_3x3() @ Vector((0, 0, -1))
    pitch = math.asin(max(-1, min(1, fwd.z)))
    e = cam_obj.rotation_euler.copy()
    cam_obj.rotation_mode = "XYZ"
    yaw = math.atan2(fwd.y, fwd.x) - math.pi / 2
    cam_obj.rotation_euler = (math.pi / 2, 0.0, yaw)
    # Blender shift is a fraction of the sensor's larger side (sensor_fit HORIZONTAL, width).
    cam.shift_y = cam.lens * math.tan(pitch) / cam.sensor_width
    return {"pitch_deg": math.degrees(pitch), "shift_y": cam.shift_y, "was": tuple(e)}


def sun_from_direction(direction, strength_lux, angle_deg=0.53, name="Sun_matched"):
    """Sun lamp pointing along -direction (direction = towards the sun). Strength in lux.
    Only for scenes WITHOUT an HDRI (tests, controls): with an HDRI sky the map is the sole
    natural light and its own sun does this job (RULES 8a)."""
    from mathutils import Vector
    d = Vector(direction).normalized()
    lamp = bpy.data.lights.get(name) or bpy.data.lights.new(name, "SUN")
    lamp.energy = strength_lux / LM_PER_W  # Blender sun strength is irradiance, W/m2
    lamp.angle = math.radians(angle_deg)
    ob = bpy.data.objects.get(name) or bpy.data.objects.new(name, lamp)
    if ob.name not in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(ob)
    ob.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    return ob
