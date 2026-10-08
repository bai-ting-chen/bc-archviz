"""Look-dev helpers distilled from reference-recreation studies (run inside Blender).

    albedo_material(tex_id, name, target)   Poly Haven PBR at a measured albedo
    vertical_boards(mat, cylinder=None)     board marks turned vertical + per-strip tone
    long_pavers(tex_id, name, target)       Brick-Texture strips over a concrete map
    sheer(name)                             diffuse + translucent curtain
    glass_shell(objs)                       solid Rhino sphere -> thin blown-glass shell
    random_tone_material(name, c0, c1)      per-instance tone (for scattered instances)

Albedo is set from the diff map's measured linear mean (cached in the texture's meta.json as
"diff_mean_linear"), via a Vector Math gain: a Mix colour socket clamps factors > 1.
"""
import json
import os

import bpy

import archviz
from study_materials import sock


def _principled(mat):
    return next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


def map_mean(tex_id):
    """Linear mean RGB of a Poly Haven diff map; measured once, then cached in meta.json."""
    folder = os.path.join(archviz.PH, "textures", tex_id)
    meta_path = os.path.join(folder, "meta.json")
    meta = json.load(open(meta_path, encoding="utf-8"))
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
    json.dump(meta, open(meta_path, "w", encoding="utf-8"), indent=2)
    return mean


def albedo_material(tex_id, name, target, scale=1.0):
    """pbr_material whose base colour averages `target` (linear RGB)."""
    mean = map_mean(tex_id)
    m = archviz.pbr_material(tex_id, name=name, scale=scale)
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


def vertical_boards(mat, cylinder=None, strip_m=0.9, strip_tone=(0.90, 1.08), macro=(0.85, 1.10),
                    flatten=0.4):
    """Turn a board-formed map 90 deg (marks vertical) on an albedo_material.

    Flat projection fed by (z, along-wall): planar walls use x + y; `cylinder=(cx, cy, r)` uses
    arc length, so a drum gets no box-projection stretch. Adds per-strip tone (white noise per
    `strip_m` strip) x low-frequency mottling, and flattens the map's stains toward its mean by
    `flatten` (repeating marks read as tiling)."""
    N, L = mat.node_tree.nodes, mat.node_tree.links
    mapping = N["Mapping"]
    pos = mapping.inputs["Vector"].links[0].from_socket
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(pos, sep.inputs[0])
    comb = N.new("ShaderNodeCombineXYZ"); comb.label = "u = z, v = along wall"
    L.new(sep.outputs["Z"], comb.inputs["X"])
    if cylinder:
        cx, cy, r = cylinder
        dx = N.new("ShaderNodeMath"); dx.operation = "SUBTRACT"; dx.inputs[1].default_value = cx
        dy = N.new("ShaderNodeMath"); dy.operation = "SUBTRACT"; dy.inputs[1].default_value = cy
        at = N.new("ShaderNodeMath"); at.operation = "ARCTAN2"
        along = N.new("ShaderNodeMath"); along.operation = "MULTIPLY"; along.inputs[1].default_value = r
        L.new(sep.outputs["X"], dx.inputs[0]); L.new(sep.outputs["Y"], dy.inputs[0])
        L.new(dy.outputs[0], at.inputs[0]); L.new(dx.outputs[0], at.inputs[1]); L.new(at.outputs[0], along.inputs[0])
    else:
        along = N.new("ShaderNodeMath"); along.operation = "ADD"
        L.new(sep.outputs["X"], along.inputs[0]); L.new(sep.outputs["Y"], along.inputs[1])
    L.new(along.outputs[0], comb.inputs["Y"])
    L.new(comb.outputs[0], mapping.inputs["Vector"])
    for n in N:
        if n.type == "TEX_IMAGE":
            n.projection = "FLAT"

    div = N.new("ShaderNodeMath"); div.operation = "DIVIDE"; div.inputs[1].default_value = strip_m
    flo = N.new("ShaderNodeMath"); flo.operation = "FLOOR"
    wn = N.new("ShaderNodeTexWhiteNoise"); wn.noise_dimensions = "1D"
    L.new(along.outputs[0], div.inputs[0]); L.new(div.outputs[0], flo.inputs[0]); L.new(flo.outputs[0], wn.inputs["W"])
    r1 = N.new("ShaderNodeMapRange"); r1.label = "strip tone"
    r1.inputs["To Min"].default_value, r1.inputs["To Max"].default_value = strip_tone
    L.new(wn.outputs["Value"], r1.inputs["Value"])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.35; nz.inputs["Detail"].default_value = 3
    L.new(pos, nz.inputs["Vector"])
    r2 = N.new("ShaderNodeMapRange"); r2.label = "macro mottle"
    r2.inputs["From Min"].default_value, r2.inputs["From Max"].default_value = 0.35, 0.65
    r2.inputs["To Min"].default_value, r2.inputs["To Max"].default_value = macro
    L.new(nz.outputs[0], r2.inputs["Value"])
    mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    L.new(r1.outputs[0], mul.inputs[0]); L.new(r2.outputs[0], mul.inputs[1])

    bsdf = _principled(mat)
    gain = next((n for n in N if n.label == "albedo gain"), None)
    if flatten and gain is not None:
        diff = next(n for n in N if n.type == "TEX_IMAGE" and n.image.colorspace_settings.name == "sRGB")
        flat = N.new("ShaderNodeMix"); flat.data_type = "RGBA"; flat.label = "flatten stains"
        flat.inputs["Factor"].default_value = flatten
        L.new(diff.outputs["Color"], sock(flat.inputs, "A"))
        sock(flat.inputs, "B").default_value = (*mat["map_mean"], 1)
        L.new(sock(flat.outputs, "Result"), gain.inputs[0])
    src = bsdf.inputs["Base Color"].links[0].from_socket
    tone = N.new("ShaderNodeVectorMath"); tone.operation = "SCALE"; tone.label = "strip x macro"
    L.new(src, tone.inputs[0]); L.new(mul.outputs[0], tone.inputs["Scale"])
    L.new(tone.outputs[0], bsdf.inputs["Base Color"])
    return mat


def long_pavers(tex_id, name, target, row=0.18, length=0.75, mortar=0.008, long_axis="Y", scale=0.5,
                tone=((0.95, 0.95, 0.95), (0.72, 0.72, 0.71)), mortar_color=(0.22, 0.22, 0.22)):
    """Running-bond strips over a concrete map. `long_axis` = world axis of the strips' length
    (read it from the vanishing point the long joints run to). Mortar < 8 mm vanishes at frame
    scale; joints recessed by bump."""
    m = albedo_material(tex_id, name, target, scale=scale)
    N, L = m.node_tree.nodes, m.node_tree.links
    geo = N.new("ShaderNodeNewGeometry")
    sep = N.new("ShaderNodeSeparateXYZ"); comb = N.new("ShaderNodeCombineXYZ")
    L.new(geo.outputs["Position"], sep.inputs["Vector"])
    other = "X" if long_axis.upper() == "Y" else "Y"
    L.new(sep.outputs[long_axis.upper()], comb.inputs["X"]); L.new(sep.outputs[other], comb.inputs["Y"])
    br = N.new("ShaderNodeTexBrick"); br.offset = 0.5; br.offset_frequency = 1
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Brick Width"].default_value = length
    br.inputs["Row Height"].default_value = row
    br.inputs["Mortar Size"].default_value = mortar
    br.inputs["Mortar Smooth"].default_value = 0.3
    br.inputs["Bias"].default_value = 0.0
    br.inputs["Color1"].default_value = (*tone[0], 1); br.inputs["Color2"].default_value = (*tone[1], 1)
    br.inputs["Mortar"].default_value = (*mortar_color, 1)
    L.new(comb.outputs["Vector"], br.inputs["Vector"])
    bsdf = _principled(m)
    src = bsdf.inputs["Base Color"].links[0].from_socket
    mul = N.new("ShaderNodeMix"); mul.data_type = "RGBA"; mul.blend_type = "MULTIPLY"
    mul.inputs["Factor"].default_value = 1.0
    L.new(src, sock(mul.inputs, "A")); L.new(br.outputs["Color"], sock(mul.inputs, "B"))
    L.new(sock(mul.outputs, "Result"), bsdf.inputs["Base Color"])
    bump = N.new("ShaderNodeBump"); bump.inputs["Distance"].default_value = 0.004; bump.invert = True
    L.new(br.outputs["Fac"], bump.inputs["Height"])
    if bsdf.inputs["Normal"].links:
        L.new(bsdf.inputs["Normal"].links[0].from_node.outputs["Normal"], bump.inputs["Normal"])
    L.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def sheer(name="CURTAIN_SHEER", color=(0.80, 0.78, 0.75), translucency=0.5):
    """Sheer curtain: Mix(Diffuse, Translucent) — a lit room behind glows through it."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    N.clear()
    d = N.new("ShaderNodeBsdfDiffuse"); d.inputs["Color"].default_value = (*color, 1)
    t = N.new("ShaderNodeBsdfTranslucent"); t.inputs["Color"].default_value = (*color, 1)
    mx = N.new("ShaderNodeMixShader"); mx.inputs[0].default_value = translucency
    o = N.new("ShaderNodeOutputMaterial")
    L.new(d.outputs[0], mx.inputs[1]); L.new(t.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], o.inputs[0])
    return m


def glass_shell(objs, thickness=0.003):
    """Solid Rhino spheres are lens balls: Solidify inward to a thin shell, shade smooth."""
    for o in objs:
        if not o.modifiers.get("Shell"):
            mod = o.modifiers.new("Shell", "SOLIDIFY")
            mod.thickness, mod.offset = thickness, -1.0
        for p in o.data.polygons:
            p.use_smooth = True


def random_tone_material(name, c0, c1, roughness=0.6, translucent=0.0):
    """Base colour between c0 and c1 per instance (Object Info > Random); optional translucency
    for leaves."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    N.clear()
    oi = N.new("ShaderNodeObjectInfo"); ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*c0, 1); ramp.color_ramp.elements[1].color = (*c1, 1)
    L.new(oi.outputs["Random"], ramp.inputs[0])
    b = N.new("ShaderNodeBsdfPrincipled"); b.inputs["Roughness"].default_value = roughness
    L.new(ramp.outputs[0], b.inputs["Base Color"])
    o = N.new("ShaderNodeOutputMaterial")
    if translucent:
        t = N.new("ShaderNodeBsdfTranslucent"); L.new(ramp.outputs[0], t.inputs[0])
        mx = N.new("ShaderNodeMixShader"); mx.inputs[0].default_value = translucent
        L.new(b.outputs[0], mx.inputs[1]); L.new(t.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], o.inputs[0])
    else:
        L.new(b.outputs[0], o.inputs[0])
    return m
