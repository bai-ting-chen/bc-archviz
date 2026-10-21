"""Grass and herb materials for modelled blades (no opacity cards): thin translucent blade,
per-instance tone and dryness, optional wet film and near-camera dew (run in Blender).

    import vegetation
    materials.vegetation.blade_material("GRASS_LEAF", tex=path)                         # dry
    materials.vegetation.blade_material("GRASS_LEAF", tex=path, wet=materials.vegetation.WET, dew=materials.vegetation.DEW_GRASS)
    materials.vegetation.blade_material("CLOVER_LEAF", tex=path, wet=..., dew=materials.vegetation.DEW_BROAD)

Physics (references/materials/vegetation.md):
- A green leaf reflects ~0.10-0.15 and transmits ~0.05-0.10 at 550 nm (Billings & Morris 1951;
  FIFE SE-590 grass leaves): Principled reflection + Translucent transmission added.
- Wet film: base pulled to dry^gamma (internal reflection in the water film, Lekner-Dorf),
  water coat IOR 1.33. At a low camera most of the lawn is seen at grazing angles, where the
  film's Fresnel sheen dominates and greys the lawn: a darker base keeps the "wet" reading.
- Dew beads are sub-pixel beyond a few metres; their sum is the film's sheen. Close to the
  camera, beads read only where large (broad waxy leaves hold 2-5 mm beads). Under an even
  overcast/fog sky a bead's brightness is refraction + total reflection inside it (a small bright
  mirror of the sky), not its ~4 % surface reflection - so a coat-only bead is invisible. Here:
  an effective-reflectance glossy bead (declared approximation; the refraction path is not
  traced), faded out with camera distance.
"""
import bpy

from .nodes import G
from .nodes import sock

BLADE = dict(rough=0.45, ior=1.45, trans_gain=0.8)        # waxy cuticle; T a little under R
WET = dict(gamma=1.7, coat=0.9, coat_rough=0.08, range=(0.75, 1.0), patch_scale=0.15)
DEW_GRASS = dict(cell=0.003, r=(0.2, 0.45), cover=0.5, reflect=0.85, rough=0.04, up=0.2, fade=(6.0, 14.0))
DEW_BROAD = dict(DEW_GRASS, cell=0.005)                   # clover-type leaves: 2-4.5 mm beads


def _wet(g, p, tone, oi, W):
    """Wet film: wetness in soft patches (instance location), base -> dry^gamma, water coat."""
    nz = g.n("ShaderNodeTexNoise", (-650, -650), noise_dimensions="4D")
    nz.inputs["Scale"].default_value = W["patch_scale"]; nz.inputs["W"].default_value = 3.3
    g.link(oi.outputs["Location"], nz.inputs["Vector"])
    wet = g.range(nz.outputs[0], 0.35, 0.65, (-450, -650), W["range"][0], W["range"][1], label="wetness")
    gm = g.n("ShaderNodeGamma", (100, 400)); gm.inputs["Gamma"].default_value = W["gamma"]
    g.link(tone, gm.inputs["Color"])
    mx = g.n("ShaderNodeMix", (250, 300), data_type="RGBA")
    g.link(wet, mx.inputs["Factor"]); g.link(tone, sock(mx.inputs, "A")); g.link(gm.outputs[0], sock(mx.inputs, "B"))
    g.link(sock(mx.outputs, "Result"), p.inputs["Base Color"])
    g.link(g.math("MULTIPLY", wet, W["coat"], (100, -650)), p.inputs["Coat Weight"])
    p.inputs["Coat IOR"].default_value = 1.33
    p.inputs["Coat Roughness"].default_value = W["coat_rough"]
    return sock(mx.outputs, "Result")


def _dew(g, shader, D):
    """Effective-reflectance dew beads mixed over `shader`: Voronoi beads in the object's own
    space (they stay on their blade), hemispherical lens normal, up-facing surfaces, near camera."""
    tc = g.n("ShaderNodeTexCoord", (-900, -1100))
    oi = g.n("ShaderNodeObjectInfo", (-1100, -1250))                 # per-instance offset (RULES MAT_06)
    off = g.n("ShaderNodeVectorMath", (-850, -1250), operation="MULTIPLY_ADD")
    g.link(oi.outputs["Random"], off.inputs[0]); off.inputs[1].default_value = (97.0, 61.0, 43.0)
    g.link(tc.outputs["Object"], off.inputs[2])
    vor = g.n("ShaderNodeTexVoronoi", (-700, -1100)); vor.inputs["Scale"].default_value = 1.0 / D["cell"]
    g.link(off.outputs[0], vor.inputs["Vector"])
    sep = g.n("ShaderNodeSeparateColor", (-500, -1250)); g.link(vor.outputs["Color"], sep.inputs[0])
    r = g.math("ADD", g.math("MULTIPLY", sep.outputs["Red"], D["r"][1] - D["r"][0], (-350, -1250)), D["r"][0], (-200, -1250))
    d = vor.outputs["Distance"]
    bead = g.math("MULTIPLY", g.math("LESS_THAN", d, r, (-350, -1100)),
                  g.math("LESS_THAN", sep.outputs["Green"], D["cover"], (-350, -1400)), (-200, -1100))
    under = g.math("SUBTRACT", g.math("MULTIPLY", r, r, (-50, -1000)), g.math("MULTIPLY", d, d, (-50, -1100)), (100, -1050))
    cap = g.math("DIVIDE", g.math("SQRT", g.math("MAXIMUM", under, 0.0, (250, -1050)), 0.0, (400, -1050)), r, (550, -1050))
    bump = g.n("ShaderNodeBump", (700, -1100)); bump.inputs["Distance"].default_value = D["cell"] * sum(D["r"]) / 2
    g.link(g.math("MULTIPLY", cap, bead, (600, -1200)), bump.inputs["Height"])
    gl = g.n("ShaderNodeBsdfGlossy", (900, -1100))
    gl.inputs["Color"].default_value = (D["reflect"],) * 3 + (1.0,)
    gl.inputs["Roughness"].default_value = D["rough"]
    g.link(bump.outputs["Normal"], gl.inputs["Normal"])
    geo = g.n("ShaderNodeNewGeometry", (-500, -1550))
    sn = g.n("ShaderNodeSeparateXYZ", (-350, -1550)); g.link(geo.outputs["Normal"], sn.inputs[0])
    up = g.math("GREATER_THAN", sn.outputs["Z"], D["up"], (-200, -1550))
    cam = g.n("ShaderNodeCameraData", (-500, -1700))
    near = g.range(cam.outputs["View Distance"], D["fade"][0], D["fade"][1], (-200, -1700), 1.0, 0.0, label="near camera")
    fac = g.math("MULTIPLY", g.math("MULTIPLY", bead, up, (50, -1500)), near, (200, -1550))
    mix = g.n("ShaderNodeMixShader", (1100, -200), label="dew beads")
    g.link(fac, mix.inputs["Fac"]); g.link(shader, mix.inputs[1]); g.link(gl.outputs[0], mix.inputs[2])
    return mix.outputs[0]


def blade_material(name, tex=None, colour=(0.12, 0.15, 0.05), wet=None, dew=None, dry_patch=0.55):
    """Thin blade: Principled + Translucent (Add); per-instance value 0.8-1.15 and a patchy straw mix; optional wet film / dew."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = G(mat)
    out = g.n("ShaderNodeOutputMaterial", (1300, 0))
    if tex:
        t = g.n("ShaderNodeTexImage", (-900, 200)); t.image = bpy.data.images.load(tex, check_existing=True)
        col = t.outputs["Color"]
    else:
        rgb = g.n("ShaderNodeRGB", (-900, 200)); rgb.outputs[0].default_value = (*colour, 1.0)
        col = rgb.outputs[0]
    # per-instance variation (RULES MAT_06) and dryness patches across the field (MAT_05)
    oi = g.n("ShaderNodeObjectInfo", (-900, -200))
    val = g.range(oi.outputs["Random"], 0.0, 1.0, (-650, -100), 0.8, 1.15)
    nz = g.n("ShaderNodeTexNoise", (-650, -350)); nz.inputs["Scale"].default_value = 0.08; nz.inputs["Detail"].default_value = 3.0
    g.link(oi.outputs["Location"], nz.inputs["Vector"])
    dry = g.range(nz.outputs[0], 0.5, 0.75, (-450, -350), 0.0, dry_patch)
    straw = g.n("ShaderNodeHueSaturation", (-450, 150))
    straw.inputs["Hue"].default_value = 0.455; straw.inputs["Saturation"].default_value = 0.75
    straw.inputs["Value"].default_value = 1.35
    g.link(col, straw.inputs["Color"])
    mix = g.n("ShaderNodeMix", (-200, 200), data_type="RGBA")
    g.link(dry, mix.inputs["Factor"]); g.link(col, sock(mix.inputs, "A")); g.link(straw.outputs[0], sock(mix.inputs, "B"))
    cmb = g.n("ShaderNodeCombineColor", (-200, -100))
    for i in range(3):
        g.link(val, cmb.inputs[i])
    tone = g.n("ShaderNodeMix", (0, 200), data_type="RGBA", blend_type="MULTIPLY")
    tone.inputs["Factor"].default_value = 1.0
    g.link(sock(mix.outputs, "Result"), sock(tone.inputs, "A")); g.link(cmb.outputs[0], sock(tone.inputs, "B"))
    p = g.n("ShaderNodeBsdfPrincipled", (500, 250))
    p.inputs["Roughness"].default_value = BLADE["rough"]; p.inputs["IOR"].default_value = BLADE["ior"]
    base = sock(tone.outputs, "Result")
    g.link(base, p.inputs["Base Color"])
    if wet:
        base = _wet(g, p, base, oi, wet)
    tg = g.n("ShaderNodeMix", (500, -150), data_type="RGBA", blend_type="MULTIPLY")
    tg.inputs["Factor"].default_value = 1.0; sock(tg.inputs, "B").default_value = (BLADE["trans_gain"],) * 3 + (1.0,)
    g.link(base, sock(tg.inputs, "A"))
    tl = g.n("ShaderNodeBsdfTranslucent", (750, -150)); g.link(sock(tg.outputs, "Result"), tl.inputs["Color"])
    add = g.n("ShaderNodeAddShader", (950, 0))
    g.link(p.outputs[0], add.inputs[0]); g.link(tl.outputs[0], add.inputs[1])
    shader = _dew(g, add.outputs[0], dew) if dew else add.outputs[0]
    g.link(shader, out.inputs[0])
    return mat
