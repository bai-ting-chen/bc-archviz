"""Concrete material helpers; canonical implementations."""
import os
import math
import bpy
from archviz import library
from .nodes import G, sock
from .pbr import _ph_maps, _principled, map_mean


def _edge_mask(g, radius, loc, frame, label):
    """Convexity mask from the Bevel node: 1 - dot(bevelled normal, true normal), normalised so
    a 90-degree arris reads 1.0. Convex-edge mask with
    sample_spread ~= radius."""
    geo = g.node("ShaderNodeNewGeometry", (loc[0] - 400, loc[1] - 120), frame)
    bev = g.node("ShaderNodeBevel", (loc[0] - 400, loc[1]), frame, label=label, Radius=radius)
    bev.samples = 16
    dot = g.node("ShaderNodeVectorMath", (loc[0] - 200, loc[1]), frame)
    dot.operation = "DOT_PRODUCT"
    g.link(bev.outputs["Normal"], dot.inputs[0])
    g.link(geo.outputs["Normal"], dot.inputs[1])  # shading normal: smooth cylinders stay clean
    inv = g.node("ShaderNodeMapRange", (loc[0], loc[1]), frame, label=label + " (0..1)")
    inv.inputs["From Min"].default_value, inv.inputs["From Max"].default_value = 1.0, 0.7071
    g.link(dot.outputs["Value"], inv.inputs["Value"])
    return inv.outputs["Result"]


def _bevel_chips(g, chip_spread, chip_in, noise_scale, noise_band, F_WEAR):
    """Chip mask: Bevel convexity -> remap -> x noise (shading only)."""
    chip = _edge_mask(g, chip_spread, (-700, -700), F_WEAR, "Chip curvature")
    chip_r = g.node("ShaderNodeMapRange", (-480, -700), F_WEAR, label="Chip Remap (TexRemap)")
    chip_r.inputs["From Min"].default_value, chip_r.inputs["From Max"].default_value = chip_in
    g.link(chip, chip_r.inputs["Value"])
    noise = g.node("ShaderNodeTexNoise", (-700, -950), F_WEAR, label="Wear Noise",
                   Scale=noise_scale, Detail=6.0)
    noise_r = g.node("ShaderNodeMapRange", (-480, -950), F_WEAR, label="noise band")
    noise_r.inputs["From Min"].default_value, noise_r.inputs["From Max"].default_value = noise_band
    g.link(noise.outputs[0], noise_r.inputs["Value"])
    chips = g.node("ShaderNodeMath", (-280, -800), F_WEAR, label="chips x noise")
    chips.operation = "MULTIPLY"
    g.link(chip_r.outputs["Result"], chips.inputs[0])
    g.link(noise_r.outputs["Result"], chips.inputs[1])
    return chips.outputs["Value"]


def concrete_study(name="CONCRETE", tex_id="concrete_wall_009",
                   color_mult=(0.76, 0.82, 0.99), normal_strength=0.6, bump_distance=0.004,
                   round_edge=0.0025, chip_spread=0.05, chip_in=(0.40, 0.90),
                   noise_scale=14.0, noise_band=(0.35, 0.60),
                   edge_dark=True, stain=True, stain_mult=1.15, bevel_chips=True,
                   stain_map=("local", "leakage_tdlbbd1c", "Leakage_tdlbbd1c_2K_Opacity.jpg")):
    """Cast concrete: tone-matched diffuse, wired roughness/normal/height, round edges
    combined with the normal map, chipped-edge wear and a leak stain driving a worn BRDF."""
    maps, meta = _ph_maps(tex_id)
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = G(mat)
    g.frame("Maps (BoxUV, real-world size)", (0.20, 0.24, 0.30))
    g.frame("Surface relief: normal + height bump + round edges", (0.25, 0.22, 0.30))
    g.frame("Wear mask: chips x noise, edge line, leak stain", (0.30, 0.22, 0.20))
    g.frame("BRDFs", (0.20, 0.28, 0.22))
    F_MAP, F_REL, F_WEAR, F_BRDF = list(g.frames)

    uv = g.uv("BoxUV", (-1700, 200), F_MAP)
    diff = g.img(maps["diff"], "sRGB", (-1450, 450), F_MAP, uv, "diffuse")
    arm = g.img(maps["arm"], "Non-Color", (-1450, 150), F_MAP, uv, "arm (AO/rough/metal)")
    nor = g.img(maps["nor_gl"], "Non-Color", (-1450, -150), F_MAP, uv, "normal (GL)")
    hgt = g.img(maps["disp"], "Non-Color", (-1450, -450), F_MAP, uv, "height")

    tone = g.node("ShaderNodeMix", (-1100, 450), F_MAP, label="color_mult (tone match)")
    tone.data_type, tone.blend_type = "RGBA", "MULTIPLY"
    tone.inputs["Factor"].default_value = 1.0
    sock(tone.inputs, "B").default_value = (*color_mult, 1.0)
    g.link(diff.outputs["Color"], sock(tone.inputs, "A"))
    sep = g.node("ShaderNodeSeparateColor", (-1100, 150), F_MAP)
    g.link(arm.outputs["Color"], sep.inputs["Color"])
    rough = g.node("ShaderNodeMix", (-900, 150), F_MAP, label="rough: map 0.45 over 0.72")
    rough.data_type = "FLOAT"
    rough.inputs["Factor"].default_value = 0.45
    sock(rough.inputs, "A").default_value = 0.72
    g.link(sep.outputs["Green"], sock(rough.inputs, "B"))

    nmap = g.node("ShaderNodeNormalMap", (-1050, -150), F_REL, Strength=normal_strength)
    nmap.uv_map = "BoxUV"
    g.link(nor.outputs["Color"], nmap.inputs["Color"])
    bump = g.node("ShaderNodeBump", (-850, -250), F_REL, label="height as bump",
                  Distance=bump_distance)
    g.link(hgt.outputs["Color"], bump.inputs["Height"])
    g.link(nmap.outputs["Normal"], bump.inputs["Normal"])
    rnd = g.node("ShaderNodeBevel", (-650, -250), F_REL, label="Round edges (TexEdges)",
                 Radius=round_edge)
    rnd.samples = 8
    g.link(bump.outputs["Normal"], rnd.inputs["Normal"])
    relief = rnd.outputs["Normal"]

    # Wear mask = max( chips * noise , edge line , stain )
    mask = None
    if bevel_chips:
        mask = _bevel_chips(g, chip_spread, chip_in, noise_scale, noise_band, F_WEAR)

    def _union(a, b, loc):
        if a is None:
            return b
        mx = g.node("ShaderNodeMath", loc, F_WEAR, label="Lighten")
        mx.operation = "MAXIMUM"
        g.link(a, mx.inputs[0])
        g.link(b, mx.inputs[1])
        return mx.outputs["Value"]

    if edge_dark:  # thin dark arris line: spread 3 mm, remap 0.55..0.95 -> 0..0.55
        line = _edge_mask(g, 0.003, (-700, -1200), F_WEAR, "Edge Dark curvature")
        line_r = g.node("ShaderNodeMapRange", (-480, -1200), F_WEAR, label="Edge Dark Remap")
        line_r.inputs["From Min"].default_value, line_r.inputs["From Max"].default_value = 0.55, 0.95
        line_r.inputs["To Max"].default_value = 0.55
        g.link(line, line_r.inputs["Value"])
        mask = _union(mask, line_r.outputs["Result"], (-120, -950))

    if stain:
        # stain_map: a leak/runoff opacity map under the study's library/ (a Megascans download
        # needs the user's sign-in). Missing -> stop and say so; never drop the layer silently.
        stain_path = library(*stain_map)
        if not os.path.exists(stain_path):
            raise FileNotFoundError(f"leak-stain map missing: {stain_path} -- download it into the "
                                    "study library or build with stain=False and tell the user")
        suv = g.uv("SpanUV", (-900, -1450), F_WEAR)
        leak = g.img(stain_path,
                     "Non-Color", (-700, -1450), F_WEAR, suv, "Leak stain (Stain Op)")
        # v stays inside 0..v_repeat (<1), so REPEAT tiles u (wrap_u 1) and never wraps v (wrap_v 0)
        sm = g.node("ShaderNodeMath", (-450, -1450), F_WEAR, label="x1.15")
        sm.operation, sm.use_clamp = "MULTIPLY", True
        sm.inputs[1].default_value = stain_mult
        g.link(leak.outputs["Color"], sm.inputs[0])
        # runoff only streaks vertical faces: weight by 1 - |normal.z|
        geo = g.node("ShaderNodeNewGeometry", (-700, -1700), F_WEAR)
        sepn = g.node("ShaderNodeSeparateXYZ", (-500, -1700), F_WEAR)
        g.link(geo.outputs["Normal"], sepn.inputs["Vector"])
        vert = g.node("ShaderNodeMapRange", (-320, -1700), F_WEAR, label="vertical faces only")
        vert.inputs["From Min"].default_value, vert.inputs["From Max"].default_value = 0.3, 0.1
        absz = g.node("ShaderNodeMath", (-450, -1850), F_WEAR)
        absz.operation = "ABSOLUTE"
        g.link(sepn.outputs["Z"], absz.inputs[0])
        g.link(absz.outputs["Value"], vert.inputs["Value"])
        smv = g.node("ShaderNodeMath", (-200, -1500), F_WEAR, label="stain (vertical faces)")
        smv.operation = "MULTIPLY"
        g.link(sm.outputs["Value"], smv.inputs[0])
        g.link(vert.outputs["Result"], smv.inputs[1])
        mask = _union(mask, smv.outputs["Value"], (40, -1100))

    clean = g.node("ShaderNodeBsdfPrincipled", (-250, 350), F_BRDF, label="Concrete",
                   IOR=1.5)
    clean.inputs["Coat Weight"].default_value = 0.03
    g.link(sock(tone.outputs, "Result"), clean.inputs["Base Color"])
    g.link(sock(rough.outputs, "Result"), clean.inputs["Roughness"])
    g.link(relief, clean.inputs["Normal"])
    worn = g.node("ShaderNodeBsdfPrincipled", (-250, -50), F_BRDF, label="Worn BRDF",
                  Roughness=0.93)
    worn.inputs["Base Color"].default_value = (0.160, 0.155, 0.145, 1)
    worn.inputs["Coat Weight"].default_value = 0.03
    g.link(relief, worn.inputs["Normal"])
    mix = g.node("ShaderNodeMixShader", (150, 200), F_BRDF, label="Wear Layered (BRDFLayered)")
    if mask is not None:
        g.link(mask, mix.inputs["Fac"])
    else:
        mix.inputs["Fac"].default_value = 0.0
    g.link(clean.outputs["BSDF"], mix.inputs[1])
    g.link(worn.outputs["BSDF"], mix.inputs[2])
    out = g.node("ShaderNodeOutputMaterial", (400, 200))
    g.link(mix.outputs["Shader"], out.inputs["Surface"])
    mat["recipe"] = "concrete_study"
    return mat


def retone(mat, target_rgb, tex_id, saturation=0.25):
    """Desaturate a concrete_study map toward its luminance, then scale its measured linear mean to `target_rgb` (a dark brown scan -> light grey concrete keeps its pits and pores)."""
    nt = mat.node_tree
    diff = next(n for n in nt.nodes if n.label == "diffuse")
    tone = next(n for n in nt.nodes if n.label == "color_mult (tone match)")
    mean = map_mean(tex_id)
    # a luminance mix (RGB to BW, Mix at `saturation`) - exactly what the gain below assumes
    # (Hue/Saturation scales HSV saturation and pulls channels toward the max: ~25 % too bright)
    lum = 0.2126 * mean[0] + 0.7152 * mean[1] + 0.0722 * mean[2]
    desat = [lum * (1 - saturation) + c * saturation for c in mean]
    g = G(nt)
    bw = g.node("ShaderNodeRGBToBW", (tone.location.x - 300, tone.location.y + 250), label="luminance")
    ds = g.n("ShaderNodeMix", (tone.location.x - 150, tone.location.y + 150), data_type="RGBA", label="desaturate")
    ds.inputs["Factor"].default_value = saturation
    for l in list(sock(tone.inputs, "A").links):
        nt.links.remove(l)
    g.link(diff.outputs["Color"], bw.inputs["Color"])
    g.link(bw.outputs["Val"], sock(ds.inputs, "A")); g.link(diff.outputs["Color"], sock(ds.inputs, "B"))
    g.link(sock(ds.outputs, "Result"), sock(tone.inputs, "A"))
    sock(tone.inputs, "B").default_value = (*[t / c for t, c in zip(target_rgb, desat)], 1.0)
    return [t / c for t, c in zip(target_rgb, desat)]


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
