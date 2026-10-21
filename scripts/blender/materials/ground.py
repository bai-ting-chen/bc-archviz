"""Ground material helpers; canonical implementations."""
import bpy
from .nodes import G, sock
from .pbr import _ph_maps
from terrain import BARE, BARE_W, _noise4


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


def ground_material(thatch_tex, soil_tex, name="GROUND", bare=BARE, wet_gamma=None, wet_rough=0.6):
    """Ground under a meadow: a dead-grass/thatch texture, soil only where the bare-soil noise
    (same 4D noise and W as scatter.meadow_layer_group) opens the sward. wet_gamma (e.g. 1.4):
    wet ground = dry^gamma (darker, more saturated) and roughness x wet_rough."""
    from materials.pbr import _ph_maps
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = G(mat)
    out = g.n("ShaderNodeOutputMaterial", (1300, 0))
    bsdf = g.n("ShaderNodeBsdfPrincipled", (1000, 0)); g.link(bsdf.outputs[0], out.inputs[0])
    geo = g.n("ShaderNodeNewGeometry", (-1200, 0))
    bn = _noise4(g, geo.outputs["Position"], bare[0], BARE_W, (-900, 600), 4.0, 0.5)
    bm = g.range(bn, bare[1], bare[2], (-700, 600), smooth=True, label="bare soil")
    sets = []
    for i, tex in enumerate((thatch_tex, soil_tex)):
        maps, meta = _ph_maps(tex)
        mp = g.n("ShaderNodeMapping", (-900, -400 * i))
        mp.inputs["Scale"].default_value = (1000 / meta["dimensions_mm"][0],) * 3
        g.link(geo.outputs["Position"], mp.inputs["Vector"])
        d = g.img(maps["diff"], "sRGB", (-600, -400 * i), None, mp.outputs[0])
        a = g.img(maps["arm"], "Non-Color", (-600, -400 * i - 200), None, mp.outputs[0])
        for n in (d, a):
            n.projection, n.projection_blend = "BOX", 0.2   # world-space box mapping, no UVs
        sep = g.n("ShaderNodeSeparateColor", (-300, -400 * i - 200)); g.link(a.outputs["Color"], sep.inputs[0])
        sets.append((d.outputs["Color"], sep.outputs["Green"]))
    mc = g.n("ShaderNodeMix", (300, 200), data_type="RGBA")
    g.link(bm, mc.inputs["Factor"]); g.link(sets[0][0], sock(mc.inputs, "A")); g.link(sets[1][0], sock(mc.inputs, "B"))
    mr = g.n("ShaderNodeMix", (300, -100), data_type="FLOAT")
    g.link(bm, mr.inputs["Factor"]); g.link(sets[0][1], sock(mr.inputs, "A")); g.link(sets[1][1], sock(mr.inputs, "B"))
    col, rough = sock(mc.outputs, "Result"), sock(mr.outputs, "Result")
    if wet_gamma:
        gm = g.n("ShaderNodeGamma", (600, 200)); gm.inputs["Gamma"].default_value = wet_gamma
        g.link(col, gm.inputs["Color"]); col = gm.outputs[0]
        rough = g.math("MULTIPLY", rough, wet_rough, (600, -100))
    g.link(col, bsdf.inputs["Base Color"]); g.link(rough, bsdf.inputs["Roughness"])
    return mat
