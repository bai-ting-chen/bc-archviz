"""Shader-node recipes: concrete, gravel, coated wood, glass, glazed tiles.

Every material is a Cycles node tree, laid out in labelled frames so it reads in the
Shader Editor.
"""
import json
import os

import bpy

from archviz import library


class G:
    """Tiny node-graph builder: frames, images on a named UV map, links."""

    def __init__(self, mat):
        mat.use_nodes = True
        self.nt = mat.node_tree
        self.nt.nodes.clear()
        self.frames = {}

    def frame(self, label, color=None):
        f = self.nt.nodes.new("NodeFrame")
        f.label, f.label_size = label, 14
        if color:
            f.use_custom_color, f.color = True, color
        self.frames[label] = f
        return f

    def node(self, kind, loc, frame=None, label=None, **inputs):
        n = self.nt.nodes.new(kind)
        n.location = loc
        if label:
            n.label = label
        if frame:
            n.parent = self.frames[frame]
        for k, v in inputs.items():
            n.inputs[k].default_value = v
        return n

    def img(self, path, colorspace, loc, frame, vector, label=None):
        n = self.node("ShaderNodeTexImage", loc, frame, label)
        n.image = bpy.data.images.load(path, check_existing=True)
        n.image.colorspace_settings.name = colorspace
        n.extension = "REPEAT"
        self.link(vector, n.inputs["Vector"])
        return n

    def uv(self, name, loc, frame):
        n = self.node("ShaderNodeUVMap", loc, frame, label="UV: " + name)
        n.uv_map = name
        return n.outputs["UV"]

    def link(self, a, b):
        self.nt.links.new(a, b)


def sock(sockets, name):
    """Active socket by name (Mix nodes keep hidden same-named sockets per data type)."""
    return next(s for s in sockets if s.name == name and s.enabled)


def _ph_maps(tex_id):
    folder = library("polyhaven", "textures", tex_id)
    meta = json.load(open(os.path.join(folder, "meta.json"), encoding="utf-8"))
    return {k: os.path.join(folder, v) for k, v in meta["maps"].items()}, meta


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


def displaced_ground(name="GRAVEL", tex_id="gray_rocks", relief_m=0.12, shift_m=-0.049):
    """Gravel ground with true displacement.
    Displacement: Scale = relief_m, Midlevel = -shift_m / relief_m."""
    maps, meta = _ph_maps(tex_id)
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = G(mat)
    g.frame("Maps (BoxUV)", (0.20, 0.24, 0.30))
    g.frame("Displacement (GeomDisplacedMesh, 2D)", (0.30, 0.25, 0.18))
    F_MAP, F_DISP = list(g.frames)
    uv = g.uv("BoxUV", (-1300, 0), F_MAP)
    diff = g.img(maps["diff"], "sRGB", (-1050, 300), F_MAP, uv, "diffuse")
    arm = g.img(maps["arm"], "Non-Color", (-1050, 0), F_MAP, uv, "arm")
    nor = g.img(maps["nor_gl"], "Non-Color", (-1050, -300), F_MAP, uv, "normal (GL)")
    hgt = g.img(maps["disp"], "Non-Color", (-1050, -600), F_DISP, uv, "height")
    sep = g.node("ShaderNodeSeparateColor", (-750, 0), F_MAP)
    g.link(arm.outputs["Color"], sep.inputs["Color"])
    nmap = g.node("ShaderNodeNormalMap", (-750, -300), F_MAP)
    nmap.uv_map = "BoxUV"
    g.link(nor.outputs["Color"], nmap.inputs["Color"])
    bsdf = g.node("ShaderNodeBsdfPrincipled", (-400, 200))
    g.link(diff.outputs["Color"], bsdf.inputs["Base Color"])
    g.link(sep.outputs["Green"], bsdf.inputs["Roughness"])
    g.link(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    disp = g.node("ShaderNodeDisplacement", (-700, -600), F_DISP,
                  Midlevel=-shift_m / relief_m, Scale=relief_m)
    g.link(hgt.outputs["Color"], disp.inputs["Height"])
    out = g.node("ShaderNodeOutputMaterial", (0, 0))
    g.link(bsdf.outputs["BSDF"], out.inputs["Surface"])
    g.link(disp.outputs["Displacement"], out.inputs["Displacement"])
    mat.displacement_method = "BOTH"  # true displacement + bump for sub-dice detail
    return mat


def enable_true_displacement(obj, pixel_size=1.0):
    """Adaptive (camera-dicing) subdivision, the view-dependent
    edge_length in pixels."""
    mod = next((m for m in obj.modifiers if m.type == "SUBSURF"), None) or \
        obj.modifiers.new("Adaptive Subdivision", "SUBSURF")
    mod.subdivision_type = "SIMPLE"
    mod.use_adaptive_subdivision = True
    mod.adaptive_space = "PIXEL"
    mod.adaptive_pixel_size = pixel_size
    return mod


def solve_levels(path, target_rgb, gamma=0.5):
    """'Measured levels': per-channel gain that lands the map's
    mean linear colour, after a shared gamma, on a target albedo. Returns the gain."""
    import numpy as np
    img = bpy.data.images.load(path, check_existing=True)
    img.colorspace_settings.name = "sRGB"
    px = np.empty(len(img.pixels), dtype=np.float32)
    img.pixels.foreach_get(px)  # linear, since the image is tagged sRGB
    mean = (px.reshape(-1, 4)[:, :3] ** gamma).mean(axis=0)
    return tuple(float(t / max(m, 1e-4)) for t, m in zip(target_rgb, mean))


def coated_wood(name="COATED_PINE", tex_id="coated_pine", coat=0.2, coat_rough=0.04,
                rough_toward_matte=0.35, albedo_rgb=(0.52, 0.33, 0.17), levels_gamma=0.5,
                round_edge=0.002, normal_strength=1.0):
    """Coated pine: every map wired; levels solved to a natural pine albedo; satin
    varnish = LOW coat amount with TIGHT gloss (the coat trap); base roughness spread toward
    matte instead of cheating Fresnel; round edges combined with the normal map."""
    maps, meta = _ph_maps(tex_id)
    gain = solve_levels(maps["diff"], albedo_rgb, levels_gamma)
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = G(mat)
    g.frame("Maps (BoxUV)", (0.20, 0.24, 0.30))
    g.frame("Relief + round edges", (0.25, 0.22, 0.30))
    F_MAP, F_REL = list(g.frames)
    uv = g.uv("BoxUV", (-1300, 0), F_MAP)
    diff = g.img(maps["diff"], "sRGB", (-1050, 300), F_MAP, uv, "diffuse")
    arm = g.img(maps["arm"], "Non-Color", (-1050, 0), F_MAP, uv, "arm")
    nor = g.img(maps["nor_gl"], "Non-Color", (-1050, -300), F_MAP, uv, "normal (GL)")
    gam = g.node("ShaderNodeGamma", (-780, 400), F_MAP, label="levels: gamma", Gamma=levels_gamma)
    g.link(diff.outputs["Color"], gam.inputs["Color"])
    lv = g.node("ShaderNodeMix", (-600, 400), F_MAP, label="levels: gain (solved)")
    lv.data_type, lv.blend_type = "RGBA", "MULTIPLY"
    lv.inputs["Factor"].default_value = 1.0
    sock(lv.inputs, "B").default_value = (*gain, 1.0)
    g.link(gam.outputs["Color"], sock(lv.inputs, "A"))
    sep = g.node("ShaderNodeSeparateColor", (-750, 0), F_MAP)
    g.link(arm.outputs["Color"], sep.inputs["Color"])
    rmix = g.node("ShaderNodeMix", (-580, 0), F_MAP, label="roughness toward matte")
    rmix.data_type = "FLOAT"
    rmix.inputs["Factor"].default_value = rough_toward_matte
    sock(rmix.inputs, "B").default_value = 1.0
    g.link(sep.outputs["Green"], sock(rmix.inputs, "A"))
    nmap = g.node("ShaderNodeNormalMap", (-750, -300), F_REL, Strength=normal_strength)
    nmap.uv_map = "BoxUV"
    g.link(nor.outputs["Color"], nmap.inputs["Color"])
    relief = nmap.outputs["Normal"]
    if round_edge:  # Bevel node is invalid on MNEE caustic casters/receivers -- pass 0 there
        rnd = g.node("ShaderNodeBevel", (-550, -300), F_REL, label="Round edges", Radius=round_edge)
        g.link(nmap.outputs["Normal"], rnd.inputs["Normal"])
        relief = rnd.outputs["Normal"]
    bsdf = g.node("ShaderNodeBsdfPrincipled", (-250, 200), label="Pine + satin varnish coat")
    g.link(sock(lv.outputs, "Result"), bsdf.inputs["Base Color"])
    g.link(sock(rmix.outputs, "Result"), bsdf.inputs["Roughness"])
    g.link(relief, bsdf.inputs["Normal"])
    bsdf.inputs["Coat Weight"].default_value = coat
    bsdf.inputs["Coat Roughness"].default_value = coat_rough
    bsdf.inputs["Coat IOR"].default_value = 1.5
    out = g.node("ShaderNodeOutputMaterial", (100, 200))
    g.link(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def clear_glass(name="GLASS", ior=1.52):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = G(mat)
    b = g.node("ShaderNodeBsdfPrincipled", (-300, 0), label="Soda-lime glass", IOR=ior,
               Roughness=0.0)
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["Base Color"].default_value = (1, 1, 1, 1)
    out = g.node("ShaderNodeOutputMaterial", (0, 0))
    g.link(b.outputs["BSDF"], out.inputs["Surface"])
    return mat


def white_backdrop(name="WHITE_BACKDROP", albedo=0.85):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = G(mat)
    b = g.node("ShaderNodeBsdfPrincipled", (-300, 0), Roughness=0.9)
    b.inputs["Base Color"].default_value = (albedo, albedo, albedo, 1)
    out = g.node("ShaderNodeOutputMaterial", (0, 0))
    g.link(b.outputs["BSDF"], out.inputs["Surface"])
    return mat


def glazed_tiles(name="POOL_TILES", tile=0.10, grout=0.003, glaze=(0.60, 0.79, 0.83),
                 glaze_var=0.06, grout_col=(0.50, 0.51, 0.50), uv="BoxUV"):
    """Procedural glazed ceramic tiles (Poly Haven has no pool mosaic): Brick Texture with zero
    offset = square grid at real size (UVs in metres), per-tile colour variation, glossy glaze,
    rough grout, rounded tile edges as bump from the mortar mask."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = G(mat)
    g.frame("Tile grid (Brick Texture, offset 0)", (0.20, 0.24, 0.30))
    g.frame("Glaze / grout", (0.22, 0.28, 0.22))
    F_GRID, F_BRDF = list(g.frames)
    coords = g.uv(uv, (-1200, 0), F_GRID)
    br = g.node("ShaderNodeTexBrick", (-950, 0), F_GRID, label="tiles %d mm, grout %d mm" % (tile * 1000, grout * 1000),
                Scale=1.0)
    br.offset, br.squash = 0.0, 1.0
    br.inputs["Brick Width"].default_value = tile
    br.inputs["Row Height"].default_value = tile
    br.inputs["Mortar Size"].default_value = grout
    br.inputs["Mortar Smooth"].default_value = 0.35
    br.inputs["Bias"].default_value = 0.0
    lo = tuple(max(0.0, c - glaze_var) for c in glaze)
    br.inputs["Color1"].default_value = (*lo, 1)
    br.inputs["Color2"].default_value = (*glaze, 1)
    br.inputs["Mortar"].default_value = (*grout_col, 1)
    g.link(coords, br.inputs["Vector"])
    tile_b = g.node("ShaderNodeBsdfPrincipled", (-500, 200), F_BRDF, label="glaze", Roughness=0.05, IOR=1.52)
    g.link(br.outputs["Color"], tile_b.inputs["Base Color"])
    grout_b = g.node("ShaderNodeBsdfPrincipled", (-500, -200), F_BRDF, label="grout", Roughness=0.9)
    grout_b.inputs["Base Color"].default_value = (*grout_col, 1)
    bump = g.node("ShaderNodeBump", (-700, -400), F_BRDF, label="rounded tile edges", Distance=0.0015)
    inv = g.node("ShaderNodeMath", (-850, -400), F_BRDF)
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    g.link(br.outputs["Fac"], inv.inputs[1])
    g.link(inv.outputs[0], bump.inputs["Height"])
    g.link(bump.outputs["Normal"], tile_b.inputs["Normal"])
    g.link(bump.outputs["Normal"], grout_b.inputs["Normal"])
    mix = g.node("ShaderNodeMixShader", (-200, 0), F_BRDF, label="grout where mortar")
    g.link(br.outputs["Fac"], mix.inputs["Fac"])
    g.link(tile_b.outputs["BSDF"], mix.inputs[1])
    g.link(grout_b.outputs["BSDF"], mix.inputs[2])
    out = g.node("ShaderNodeOutputMaterial", (100, 0))
    g.link(mix.outputs["Shader"], out.inputs["Surface"])
    return mat
