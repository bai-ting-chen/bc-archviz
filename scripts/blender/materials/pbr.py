"""Pbr material helpers; canonical implementations."""
import os
import bpy
from .nodes import G, sock
BUMP_DISTANCE = 0.004


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
    import archviz
    from archviz import library, read_meta
    folder = library("polyhaven", "textures", tex_id)
    meta = read_meta(folder)
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
        sock(mix.inputs, "B").default_value = (*tint, 1.0)
        mix.location = (100, 300)
        L.new(diff.outputs["Color"], sock(mix.inputs, "A"))
        L.new(sock(mix.outputs, "Result"), bsdf.inputs["Base Color"])
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


def dielectric(name, ior=1.52, tint=(1.0, 1.0, 1.0), roughness=0.0, label=None):
    """The one clear-dielectric builder (glass, water, glass-to-water interfaces): Principled,
    transmission 1. `tint` multiplies every crossing, so keep it within a few % of white."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.label = "%s (IOR %.3f)" % (name, ior) if label is None else label
    b.inputs["Base Color"].default_value = (*tint, 1)
    b.inputs["Roughness"].default_value = roughness
    b.inputs["IOR"].default_value = ior
    b.inputs["Transmission Weight"].default_value = 1.0
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    o.location = (300, 0)
    nt.links.new(b.outputs["BSDF"], o.inputs["Surface"])
    return mat


def _principled_of(mat):
    """The material's Principled BSDF; one wired to the output is added if it has none."""
    mat.use_nodes = True
    nt = mat.node_tree
    b = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if b is None:
        b = nt.nodes.new("ShaderNodeBsdfPrincipled")
        o = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"), None) or nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(b.outputs["BSDF"], o.inputs["Surface"])
    return b


def glass_material(name="Glass_Clear", tint=(0.92, 0.96, 0.97), roughness=0.0):
    """Clear glass (IOR 1.52); the default tint is slightly green, for thick panes. An existing
    material is edited in place (nodes the user added stay); a new one is built by dielectric."""
    mat = bpy.data.materials.get(name)
    if mat is None:
        return dielectric(name, 1.52, tint, roughness, label="")
    b = _principled_of(mat)
    b.inputs["Base Color"].default_value = (*tint, 1.0)
    b.inputs["Roughness"].default_value = roughness
    b.inputs["IOR"].default_value = 1.52
    b.inputs["Transmission Weight"].default_value = 1.0
    return mat


def simple_material(name, color, roughness=0.5, metallic=0.0):
    """Principled with a flat colour, roughness and metallic -- placeholders and controls."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    b = _principled_of(mat)
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
    spec = dict(spec)
    kind = spec.pop("type")
    return {"ph": lambda **k: pbr_material(**k), "glass": glass_material, "simple": simple_material}[kind](**spec)


def _ph_maps(tex_id):
    import archviz
    from archviz import library, read_meta
    folder = library("polyhaven", "textures", tex_id)
    meta = read_meta(folder)
    return {k: os.path.join(folder, v) for k, v in meta["maps"].items()}, meta


def solve_levels(path, target_rgb, gamma=0.5):
    """'Measured levels': per-channel gain that lands the map's
    mean linear colour, after a shared gamma, on a target albedo. Returns the gain."""
    import numpy as np
    img = bpy.data.images.load(path, check_existing=True)
    img.colorspace_settings.name = "sRGB"
    px = np.empty(len(img.pixels), dtype=np.float32)
    img.pixels.foreach_get(px)
    rgb = px.reshape(-1, img.channels)[:, :3].astype(np.float64)
    if not img.is_float:   # byte images come back sRGB-encoded, not linear (api-traps)
        rgb = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    mean = (rgb ** gamma).mean(axis=0)
    return tuple(float(t / max(m, 1e-4)) for t, m in zip(target_rgb, mean))


def white_backdrop(name="WHITE_BACKDROP", albedo=0.85):
    """Matte white backdrop of a measured albedo (product/studio shots)."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = G(mat)
    b = g.node("ShaderNodeBsdfPrincipled", (-300, 0), Roughness=0.9)
    b.inputs["Base Color"].default_value = (albedo, albedo, albedo, 1)
    out = g.node("ShaderNodeOutputMaterial", (0, 0))
    g.link(b.outputs["BSDF"], out.inputs["Surface"])
    return mat


def _principled(mat):
    return next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


def map_mean(tex_id):
    """Linear mean RGB of a Poly Haven diff map; measured once, then cached in meta.json."""
    import archviz
    from archviz import library, read_meta
    folder = archviz.library("polyhaven", "textures", tex_id)
    meta = archviz.read_meta(folder)
    if "diff_mean_linear" in meta:
        return tuple(meta["diff_mean_linear"])
    import numpy as np
    img = bpy.data.images.load(os.path.join(folder, meta["maps"]["diff"]), check_existing=True)
    px = np.empty(img.size[0] * img.size[1] * img.channels, dtype=np.float32)
    img.pixels.foreach_get(px)
    rgb = px.reshape(-1, img.channels)[:, :3].astype(np.float64)
    if not img.is_float:   # byte images hold sRGB-encoded values
        rgb = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    mean = tuple(round(float(v), 4) for v in rgb.mean(0))
    meta["diff_mean_linear"] = list(mean)
    archviz.write_meta(folder, meta)
    return mean


def albedo_material(tex_id, name, target, scale=1.0):
    """pbr_material whose base colour averages `target` (linear RGB)."""
    mean = map_mean(tex_id)
    m = pbr_material(tex_id, name=name, scale=scale)
    N, L = m.node_tree.nodes, m.node_tree.links
    bsdf = _principled(m)
    src = bsdf.inputs["Base Color"].links[0].from_socket
    gain = N.new("ShaderNodeVectorMath"); gain.operation = "MULTIPLY"; gain.label = "albedo gain"
    gain.location = (250, 350)
    gain.inputs[1].default_value = tuple(t / mm for t, mm in zip(target, mean))
    L.new(src, gain.inputs[0]); L.new(gain.outputs[0], bsdf.inputs["Base Color"])
    m["albedo_target"] = list(target)
    m["map_mean"] = list(mean)
    return m
