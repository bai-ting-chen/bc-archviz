"""Procedural edge wear (dirty edges, shading only) and edge chips (real geometry).

Rhino meshes are too coarse for curvature methods (a beam arrives as 8 faces), so:
  1. dice()              -- subdivide in place until no edge is longer than `size`
  2. edge_wear_group()   -- Geometry Nodes modifier:
       edge field : Edge Angle (convex, sharper than threshold) -> Mesh to Curve -> Proximity
                    -> `edge_dist` = metres to the nearest arris, plus `rest_pos`
       chips      : only faces within `Band` of an arris are split off and subdivided; there
                    reach = Chip Reach x bite noise x segment noise, chip where edge_dist < reach,
                    depth = Chip Depth x profile x fracture noise, Set Position along -normal;
                    stored as `chip` (metres); band and interior are rejoined and welded
  3. weathered_concrete() -- shader: dirty-edge grime from edge_dist x noise (no geometry),
                    fresh-break material where `chip` > 0
"""
import math

import bmesh
import bpy

import study_materials as sm
from study_materials import G, sock


# --- geometry ---------------------------------------------------------------------------

def dice(obj, size=0.05):
    """Subdivide in place by repeated halving of over-long edges (grid fill keeps quads)."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    s = obj.matrix_world.to_scale()
    sc = max(abs(s.x), abs(s.y), abs(s.z))
    for _ in range(16):
        long_edges = [e for e in bm.edges if e.calc_length() * sc > size]
        if not long_edges:
            break
        bmesh.ops.subdivide_edges(bm, edges=long_edges, cuts=1, use_grid_fill=True)
    bm.to_mesh(obj.data)
    bm.free()
    return len(obj.data.polygons)


def _GN(ng):
    """Kept for existing scripts: study_materials.G on a node group."""
    return G(ng, clear=False)


def _input(ng, name, kind, default, subtype=None):
    it = ng.interface.new_socket(name, in_out="INPUT", socket_type=kind)
    it.default_value = default
    if subtype:
        it.subtype = subtype


def _edge_field(b, gi, x0):
    """Distance to the nearest convex arris -> `edge_dist`, and the rest position offset by the
    group's Seed -> `rest_pos` (noise lookups; a per-object Seed decorrelates repeated objects).
    Measured on outward-normal meshes: convex arrises give a POSITIVE signed angle, inner
    corners a negative one."""
    L = b.L
    ang = b.n("GeometryNodeInputMeshEdgeAngle", (x0, -300))
    cmp = b.n("FunctionNodeCompare", (x0 + 200, -300), data_type="FLOAT", operation="GREATER_THAN")
    L(ang.outputs["Signed Angle"], sock(cmp.inputs, "A"))
    L(gi.outputs["Sharp Angle"], sock(cmp.inputs, "B"))
    m2c = b.n("GeometryNodeMeshToCurve", (x0 + 400, -200))
    L(gi.outputs["Geometry"], m2c.inputs["Mesh"])
    L(cmp.outputs[0], m2c.inputs["Selection"])
    c2m = b.n("GeometryNodeCurveToMesh", (x0 + 600, -200))
    L(m2c.outputs["Curve"], c2m.inputs["Curve"])
    prox = b.n("GeometryNodeProximity", (x0 + 800, -200), target_element="EDGES")
    L(c2m.outputs["Mesh"], prox.inputs["Geometry"])
    pos = b.n("GeometryNodeInputPosition", (x0 + 800, -450))
    seed_v = b.n("ShaderNodeVectorMath", (x0 + 950, -450), operation="ADD")
    L(pos.outputs["Position"], seed_v.inputs[0])
    L(gi.outputs["Seed"], seed_v.inputs[1])
    g = b.store(gi.outputs["Geometry"], "edge_dist", "FLOAT", prox.outputs["Distance"], (x0 + 1050, 0))
    return b.store(g, "rest_pos", "FLOAT_VECTOR", seed_v.outputs["Vector"], (x0 + 1250, 0))


def _chip_field(b, gi, rp, dd, seg_scale, bite_scale, soft, prof_end):
    """Chips along the arris: segments of the edge chipped (share -> threshold; Noise clusters
    near 0.5, sd ~0.1), bite noise varies the reach. Returns (chip 0..1, depth profile)."""
    t = b.math("SUBTRACT", 0.5, gi.outputs["Chipped Share"], (500, -700))
    t = b.math("MULTIPLY", t, 0.35, (650, -700))
    t = b.math("ADD", t, 0.5, (750, -700))
    seg = b.range(b.noise(rp, seg_scale, (650, -500), detail=2), b.math("SUBTRACT", t, 0.04, (850, -650)),
                  b.math("ADD", t, 0.04, (850, -760)), (1000, -550))
    bite = b.range(b.noise(rp, bite_scale, (650, -900), detail=8, rough=0.7), 0.35, 0.75, (1000, -850))
    reach = b.math("MULTIPLY", b.math("MULTIPLY", bite, seg, (1200, -700)),
                   gi.outputs["Chip Reach"], (1380, -700))
    chip = b.range(b.math("SUBTRACT", reach, dd, (1550, -500)), 0.0, soft, (1720, -500))
    prof = b.range(dd, 0.0, gi.outputs["Chip Reach"], (1550, -800), 1.0, prof_end)
    return chip, prof


def _rejoin(b, moved, sep, go, x0, weld_dist):
    """Rejoin the displaced band with the untouched interior and weld the seam."""
    join = b.n("GeometryNodeJoinGeometry", (x0, 0))
    b.L(moved, join.inputs[0])
    b.L(sep.outputs["Inverted"], join.inputs[0])
    weld = b.n("GeometryNodeMergeByDistance", (x0 + 130, 0))
    weld.inputs["Distance"].default_value = weld_dist
    b.L(join.outputs[0], weld.inputs["Geometry"])
    b.L(weld.outputs["Geometry"], go.inputs["Geometry"])


def edge_wear_group(name="Edge Wear + Chips", band=0.08, level=3, chip_reach=0.045,
                    chip_depth=0.018, chipped_share=0.55, sharp_deg=30.0, chips=True,
                    bite_scale=22.0, segment_scale=2.2, seed=(0.0, 0.0, 0.0)):
    """Geometry Nodes modifier: edge field for every point, real chips in the arris band.
    Per object: add_edge_wear(obj, group, Seed=(x, y, z)) moves the chip pattern."""
    ng = bpy.data.node_groups.get(name)
    if ng:
        bpy.data.node_groups.remove(ng)
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    _input(ng, "Sharp Angle", "NodeSocketFloat", math.radians(sharp_deg), "ANGLE")
    _input(ng, "Band", "NodeSocketFloat", band, "DISTANCE")
    _input(ng, "Band Subdivisions", "NodeSocketInt", level)
    _input(ng, "Chip Reach", "NodeSocketFloat", chip_reach, "DISTANCE")
    _input(ng, "Chip Depth", "NodeSocketFloat", chip_depth if chips else 0.0, "DISTANCE")
    _input(ng, "Chipped Share", "NodeSocketFloat", chipped_share, "FACTOR")
    _input(ng, "Seed", "NodeSocketVector", seed)
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    b = _GN(ng)
    L = b.L
    gi = b.n("NodeGroupInput", (-1400, 0))
    go = b.n("NodeGroupOutput", (2700, 0))

    # 1. distance to the nearest convex arris
    g = _edge_field(b, gi, -1400)

    # 2. split off the arris band, densify only that
    in_band = b.n("FunctionNodeCompare", (50, -300), data_type="FLOAT", operation="LESS_THAN")
    L(b.named("edge_dist", "FLOAT", (-150, -300)), sock(in_band.inputs, "A"))
    L(gi.outputs["Band"], sock(in_band.inputs, "B"))
    sep = b.n("GeometryNodeSeparateGeometry", (250, 0), domain="FACE")
    L(g, sep.inputs["Geometry"])
    L(in_band.outputs[0], sep.inputs["Selection"])
    sub = b.n("GeometryNodeSubdivideMesh", (450, 100))
    L(sep.outputs["Selection"], sub.inputs["Mesh"])
    L(gi.outputs["Band Subdivisions"], sub.inputs["Level"])

    # 3. chip field on the dense band
    rp = b.named("rest_pos", "FLOAT_VECTOR", (450, -400))
    dd = b.named("edge_dist", "FLOAT", (450, -250))
    chip, prof = _chip_field(b, gi, rp, dd, segment_scale, bite_scale, 0.002, 0.35)
    frac = b.range(b.noise(rp, 140.0, (1380, -1000), detail=4), 0.3, 0.7, (1550, -1000), 0.6, 1.0)
    depth = b.math("MULTIPLY", b.math("MULTIPLY", chip, prof, (1900, -650)),
                   b.math("MULTIPLY", frac, gi.outputs["Chip Depth"], (1900, -900)), (2050, -750))
    nrm = b.n("GeometryNodeInputNormal", (1900, -350))
    off = b.n("ShaderNodeVectorMath", (2150, -400), operation="SCALE")
    L(nrm.outputs["Normal"], off.inputs[0])
    L(b.math("MULTIPLY", depth, -1.0, (2150, -600)), off.inputs["Scale"])
    band_geo = b.store(sub.outputs["Mesh"], "chip", "FLOAT", depth, (1300, 100))
    setp = b.n("GeometryNodeSetPosition", (2300, 100))
    L(band_geo, setp.inputs["Geometry"])
    L(off.outputs["Vector"], setp.inputs["Offset"])

    # 4. rejoin with the untouched interior and weld the seam
    _rejoin(b, setp.outputs["Geometry"], sep, go, 2450, 1e-5)
    return ng


def set_input(mod, name, value):
    """Blender 5.2: a Geometry Nodes modifier's own input values live at
    mod.properties.inputs.<identifier>.value. Those entries have EMPTY names, so resolve the
    identifier through the group interface. Group defaults are only copied in at creation."""
    ident = next(i.identifier for i in mod.node_group.interface.items_tree
                 if getattr(i, "in_out", "") == "INPUT" and i.name == name)
    getattr(mod.properties.inputs, ident).value = value


def add_edge_wear(obj, group, **inputs):
    """Add the modifier; per-object overrides by input name, e.g. add_edge_wear(o, g, Band=0.1)."""
    mod = obj.modifiers.new("Edge Wear + Chips", "NODES")
    mod.node_group = group
    for k, v in inputs.items():
        set_input(mod, k.replace("_", " "), v)
    return mod


# --- shading ----------------------------------------------------------------------------

def _attr(g, name, loc, frame, out="Fac"):
    return g.attr(name, loc, frame, out)


def _noise(g, vec, scale, loc, frame, detail=6.0, rough=0.6, label=None):
    return g.noise(vec, scale, loc, frame, detail, rough, label)


def _range(g, val, fmin, fmax, loc, frame, tmin=0.0, tmax=1.0, label=None, smooth=False):
    return g.range(val, fmin, fmax, loc, tmin, tmax, frame, label, smooth)


def _math(g, op, a, b, loc, frame, clamp=False):
    return g.math(op, a, b, loc, frame, clamp)


def weathered_concrete(name="CONCRETE_WEATHERED", dirt_band=0.035, dirt_amount=0.85,
                       dirt_noise_scale=9.0, stain=True, tex_id="concrete_wall_009"):
    """concrete_study base (tone, maps, round edges, leak stain) + procedural dirty edges from
    the GN `edge_dist` field + a fresh-break material where GN cut a chip (`chip` > 0)."""
    mat = sm.concrete_study(name=name, tex_id=tex_id, edge_dark=False, stain=stain, bevel_chips=False)
    g = G(mat.node_tree)                      # add to the existing tree
    nt = mat.node_tree
    mix = next(n for n in nt.nodes if n.label == "Wear Layered (BRDFLayered)")
    stain_node = next((n for n in nt.nodes if n.label == "stain (vertical faces)"), None)
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    clean = next(n for n in nt.nodes if n.label == "Concrete")

    g.frame("Edge field (from Geometry Nodes)", (0.22, 0.22, 0.32))
    g.frame("Dirty edges (shading only)", (0.32, 0.24, 0.16))
    g.frame("Chips (geometry cut by GN; shaded here)", (0.32, 0.18, 0.18))
    F_FLD, F_DIRT, F_CHIP = list(g.frames)
    x0, y0 = -1600, -2300
    d = _attr(g, "edge_dist", (x0, y0), F_FLD)
    rest = _attr(g, "rest_pos", (x0, y0 - 180), F_FLD, out="Vector")
    chip_m = _attr(g, "chip", (x0, y0 - 360), F_FLD)
    chip = _range(g, chip_m, 0.0, 0.0008, (x0 + 250, y0 - 600), F_CHIP, label="chip mask (break edge)")

    band = _range(g, d, 0.0, dirt_band, (x0 + 250, y0 + 300), F_DIRT, 1.0, 0.0,
                  label="edge band", smooth=True)
    blot = _range(g, _noise(g, rest, dirt_noise_scale, (x0 + 250, y0 + 80), F_DIRT, detail=10,
                            rough=0.65, label="grime breakup"),
                  0.36, 0.60, (x0 + 450, y0 + 80), F_DIRT)
    dirt = _math(g, "MULTIPLY", band, blot, (x0 + 650, y0 + 200), F_DIRT)
    dirt = _math(g, "MULTIPLY", dirt, dirt_amount, (x0 + 820, y0 + 200), F_DIRT)
    no_chip = _math(g, "SUBTRACT", 1.0, chip, (x0 + 820, y0 + 20), F_DIRT, clamp=True)
    dirt = _math(g, "MULTIPLY", dirt, no_chip, (x0 + 1000, y0 + 150), F_DIRT)  # fresh breaks are clean
    dirt.node.label = "dirty edge mask"
    mask = dirt
    if stain_node is not None:
        mask = _math(g, "MAXIMUM", mask, stain_node.outputs[0], (x0 + 1200, y0 + 150), F_DIRT)
    for l in list(mix.inputs["Fac"].links):
        nt.links.remove(l)
    g.link(mask, mix.inputs["Fac"])
    worn = next(n for n in nt.nodes if n.label == "Worn BRDF")
    worn.label = "Grime BRDF"
    worn.inputs["Base Color"].default_value = (0.105, 0.098, 0.088, 1)

    brk = g.node("ShaderNodeBsdfPrincipled", (x0 + 900, y0 - 500), F_CHIP,
                 label="Fresh break (lighter, rough)", Roughness=0.95)
    tint = g.node("ShaderNodeMix", (x0 + 650, y0 - 450), F_CHIP, label="break: lighter paste")
    tint.data_type, tint.blend_type = "RGBA", "MULTIPLY"
    tint.inputs["Factor"].default_value = 1.0
    sock(tint.inputs, "B").default_value = (1.16, 1.15, 1.13, 1)  # lighter paste, not chalk
    g.link(clean.inputs["Base Color"].links[0].from_socket, sock(tint.inputs, "A"))
    g.link(sock(tint.outputs, "Result"), brk.inputs["Base Color"])
    bump = g.node("ShaderNodeBump", (x0 + 650, y0 - 750), F_CHIP, label="fracture bump",
                  Distance=0.003)
    g.link(_noise(g, rest, 400.0, (x0 + 450, y0 - 750), F_CHIP, detail=6), bump.inputs["Height"])
    g.link(bump.outputs["Normal"], brk.inputs["Normal"])
    mix2 = g.node("ShaderNodeMixShader", (x0 + 1200, y0 - 300), F_CHIP, label="chips over surface")
    g.link(chip, mix2.inputs["Fac"])
    g.link(mix.outputs["Shader"], mix2.inputs[1])
    g.link(brk.outputs["BSDF"], mix2.inputs[2])
    g.link(mix2.outputs["Shader"], out.inputs["Surface"])
    mat.displacement_method = "BUMP"
    mat["recipe"] = "procedural dirty edges (shading) + GN-cut chips (geometry)"
    return mat


def mask_material(name, method, radius=0.035):
    """Emission view of one edge-detection method, for side-by-side comparison."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = G(mat)
    g.frame("mask", None)
    F = "mask"
    if method == "pointiness":
        geo = g.node("ShaderNodeNewGeometry", (-800, 0), F)
        val = _range(g, geo.outputs["Pointiness"], 0.5, 0.56, (-500, 0), F)
    elif method == "ao_inside":
        ao = g.node("ShaderNodeAmbientOcclusion", (-800, 0), F, Distance=radius)
        ao.inside, ao.only_local, ao.samples = True, True, 16
        val = _range(g, ao.outputs["AO"], 1.0, 0.6, (-500, 0), F)
    elif method == "bevel":
        val = sm._edge_mask(g, radius, (-500, 0), F, "bevel")
    elif method == "edge_dist":
        val = _range(g, _attr(g, "edge_dist", (-800, 0), F), 0.0, radius, (-500, 0), F, 1.0, 0.0)
    elif method == "chip":
        val = _range(g, _attr(g, "chip", (-800, 0), F), 0.0, 0.0003, (-500, 0), F)
    elif method == "damage":  # chips + breaks (wood)
        c = _range(g, _attr(g, "chip", (-800, 0), F), 0.0, 0.0003, (-600, 0), F)
        k = _range(g, _attr(g, "break", (-800, -200), F), 0.0, 0.00015, (-600, -200), F)
        val = _math(g, "MAXIMUM", c, k, (-450, -100), F)
    em = g.node("ShaderNodeEmission", (-200, 0))
    g.link(val, em.inputs["Color"])
    o = g.node("ShaderNodeOutputMaterial", (0, 0))
    g.link(em.outputs["Emission"], o.inputs["Surface"])
    return mat


# --- runoff leaks, grunge, splash, cracks (on a weathered_concrete material) ------------------

def leak_field_group(name="LEAK FIELD", inset=0.02, reach=6.0):
    """GN: per point, metres below the first surface straight above it (raycast up from `inset` inside the wall) -> `leak_d`, `leak_ok`."""
    ng = bpy.data.node_groups.get(name)
    if ng:
        bpy.data.node_groups.remove(ng)
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.is_modifier = True
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    b = G(ng, clear=True)
    gi = b.n("NodeGroupInput", (-800, 0)); go = b.n("NodeGroupOutput", (900, 0))
    pos = b.n("GeometryNodeInputPosition", (-800, -300)).outputs[0]
    nrm = b.n("GeometryNodeInputNormal", (-800, -450)).outputs[0]
    ins = b.n("ShaderNodeVectorMath", (-600, -400), operation="SCALE")
    b.L(nrm, ins.inputs[0]); ins.inputs["Scale"].default_value = -inset
    src = b.n("ShaderNodeVectorMath", (-450, -350), operation="ADD")
    b.L(pos, src.inputs[0]); b.L(ins.outputs[0], src.inputs[1])
    ray = b.n("GeometryNodeRaycast", (-250, -250), data_type="FLOAT")
    b.L(gi.outputs[0], ray.inputs["Target Geometry"]); b.L(src.outputs[0], ray.inputs["Source Position"])
    ray.inputs["Ray Direction"].default_value = (0, 0, 1)
    ray.inputs["Ray Length"].default_value = reach
    hz = b.n("ShaderNodeSeparateXYZ", (-50, -300)); b.L(ray.outputs["Hit Position"], hz.inputs[0])
    pz = b.n("ShaderNodeSeparateXYZ", (-50, -450)); b.L(pos, pz.inputs[0])
    d = b.math("SUBTRACT", hz.outputs["Z"], pz.outputs["Z"], (150, -350))
    geo = b.store(gi.outputs[0], "leak_d", "FLOAT", d, (350, 0))
    geo = b.store(geo, "leak_ok", "FLOAT", ray.outputs["Is Hit"], (600, 0))
    b.L(geo, go.inputs[0])
    return ng


def add_leak_field(obj):
    """Add LEAK FIELD as the FIRST modifier: run after chips, rays slip through the chip-band seam and a wrong leak_d spreads over whole coarse triangles (light triangles under an arris)."""
    mod = obj.modifiers.new("LEAK FIELD", "NODES")
    mod.node_group = leak_field_group()
    obj.modifiers.move(obj.modifiers.find(mod.name), 0)
    return mod


LEAK = dict(streak_w=14.0, streak_len=0.6, max_len=(0.8, 3.2), top_band=0.2, top=0.9, amount=1.0,
            streak_band=(0.42, 0.58), presence=(0.28, 0.5), fade_pow=1.15)
CRACK = dict(core=0.005, halo=0.02, wobble=0.03, jag=0.006, len=(0.4, 1.0), jitter=14.0, seed=3,
             net_scale=1.6, net_dist=0.22, net_keep=0.4, net_patch=(0.52, 0.6), depth=0.003, halo_dirt=0.6)


def _frame(mat, label):
    g = G(mat.node_tree)
    g.frame(label, (0.18, 0.26, 0.30))
    return g, label


def add_runoff(mat, leak=None, grunge=(0.6, 9.0, 0.56, 0.62, 0.45), splash=(0.08, 0.35, 0.7)):
    """On a weathered_concrete material: vertical runoff streaks below drip edges (needs add_leak_field), grunge patches, soil splash at the foot; all into its grime mask."""
    L_ = dict(LEAK, **(leak or {}))
    g, F = _frame(mat, "Runoff streaks, grunge, splash")
    nt = mat.node_tree
    geo = g.node("ShaderNodeNewGeometry", (-2600, -3400), F)
    sepn = g.node("ShaderNodeSeparateXYZ", (-2400, -3700), F); g.link(geo.outputs["Normal"], sepn.inputs[0])
    vert = g.range(g.math("ABSOLUTE", sepn.outputs["Z"], 0.0, (-2200, -3700), F), 0.25, 0.1, (-2000, -3700), frame=F)
    sepp = g.node("ShaderNodeSeparateXYZ", (-2400, -3950), F); g.link(geo.outputs["Position"], sepp.inputs[0])
    along = g.math("ADD", sepp.outputs["X"], sepp.outputs["Y"], (-2200, -3950), F)
    sv = g.node("ShaderNodeCombineXYZ", (-2000, -4100), F)
    g.link(g.math("MULTIPLY", along, L_["streak_w"], (-2150, -4100), F), sv.inputs["X"])
    g.link(g.math("MULTIPLY", sepp.outputs["Z"], L_["streak_len"], (-2150, -4250), F), sv.inputs["Y"])
    streak = g.range(g.noise(sv.outputs[0], 1.0, (-1850, -4100), F, detail=4, rough=0.55), *L_["streak_band"],
                     (-1650, -4100), frame=F, smooth=True)
    lv = g.node("ShaderNodeCombineXYZ", (-2000, -4400), F)
    g.link(g.math("MULTIPLY", along, 2.5, (-2150, -4400), F), lv.inputs["X"])
    llen = g.range(g.noise(lv.outputs[0], 1.0, (-1850, -4400), F, detail=2), 0.35, 0.65, (-1650, -4400),
                   L_["max_len"][0], L_["max_len"][1], F)
    d = g.attr("leak_d", (-1850, -4650), F)
    ok = g.attr("leak_ok", (-1850, -4800), F)
    fade = g.math("SUBTRACT", 1.0, g.math("DIVIDE", d, llen, (-1450, -4500), F), (-1300, -4500), F, clamp=True)
    fade = g.math("POWER", fade, L_["fade_pow"], (-1150, -4500), F)
    top = g.range(d, 0.0, L_["top_band"], (-1450, -4700), L_["top"], 0.0, F, smooth=True)
    pv = g.node("ShaderNodeCombineXYZ", (-2000, -4950), F)
    g.link(g.math("MULTIPLY", along, 0.7, (-2150, -4950), F), pv.inputs["X"])
    presence = g.range(g.noise(pv.outputs[0], 1.0, (-1850, -4950), F, detail=3), *L_["presence"], (-1650, -4950), frame=F)
    leak = g.math("MAXIMUM", g.math("MULTIPLY", streak, fade, (-1000, -4300), F), top, (-850, -4400), F)
    leak = g.math("MULTIPLY", leak, presence, (-700, -4400), F)
    leak = g.math("MULTIPLY", leak, g.math("MULTIPLY", ok, vert, (-850, -4700), F), (-550, -4500), F)
    gate = g.range(d, -0.02, 0.0, (-1450, -4850), frame=F)
    leak = g.math("MULTIPLY", g.math("MULTIPLY", leak, gate, (-400, -4500), F), L_["amount"], (-250, -4500), F)
    leak.node.label = "leak streak mask"
    ps, hs, lo, hi, amt = grunge
    patch = g.math("ADD", g.noise(geo.outputs["Position"], ps, (-1850, -5200), F, detail=3),
                   g.math("MULTIPLY", g.math("SUBTRACT", g.noise(geo.outputs["Position"], hs, (-1850, -5400), F, detail=6), 0.5,
                                             (-1650, -5400), F), 0.35, (-1500, -5400), F), (-1350, -5250), F)
    grg = g.range(patch, lo, hi, (-1200, -5250), 0.0, amt, F)
    grg.node.label = "grunge patches"
    foot = g.math("ADD", sepp.outputs["Z"], g.math("MULTIPLY", g.math("SUBTRACT", g.noise(geo.outputs["Position"], 6.0, (-1850, -5650), F), 0.5,
                                                                      (-1650, -5650), F), 0.25, (-1500, -5650), F), (-1350, -5600), F)
    spl = g.math("MULTIPLY", g.range(foot, splash[0], splash[1], (-1200, -5600), splash[2], 0.0, F, smooth=True), vert, (-1050, -5600), F)
    spl.node.label = "soil splash"
    mix = next(n for n in nt.nodes if n.label == "Wear Layered (BRDFLayered)")
    old = mix.inputs["Fac"].links[0].from_socket
    m = g.math("MAXIMUM", g.math("MAXIMUM", g.math("MAXIMUM", old, leak, (-100, -4300), F), grg, (50, -4500), F), spl, (200, -4600), F)
    g.link(m, mix.inputs["Fac"])
    return mat


def _crack_masks(g, F, openings, C):
    import random
    rnd = random.Random(C["seed"])
    geo = g.node("ShaderNodeNewGeometry", (-2600, -6200), F)
    pos = geo.outputs["Position"]
    sp = g.node("ShaderNodeSeparateXYZ", (-2400, -6200), F); g.link(pos, sp.inputs[0])
    wob = g.math("MULTIPLY", g.math("SUBTRACT", g.noise(pos, 6.0, (-2400, -6450), F, detail=4, rough=0.6), 0.5, (-2250, -6450), F),
                 C["wobble"] * 2, (-2100, -6450), F)
    jag = g.math("MULTIPLY", g.math("SUBTRACT", g.noise(pos, 40.0, (-2400, -6650), F, detail=2, rough=0.5), 0.5, (-2250, -6650), F),
                 C["jag"] * 2, (-2100, -6650), F)
    wob = g.math("ADD", wob, jag, (-1950, -6550), F)
    core = halo = None
    y = -6200
    for op in openings:
        axis, plane, u0, u1, v0, v1, top_only = op[:7]
        keep = op[7] if len(op) > 7 else None
        dist = g.math("ABSOLUTE", g.math("SUBTRACT", sp.outputs["X" if axis == "x" else "Y"], plane, (-2200, y), F), 0.0, (-2050, y), F)
        on = g.range(dist, 0.03, 0.01, (-1900, y), frame=F)
        uu = sp.outputs["Y" if axis == "x" else "X"]
        corners = [(u0, v1, 135), (u1, v1, 45)] + ([] if top_only else [(u0, v0, 225), (u1, v0, 315)])
        for cu, cv, ang in corners:
            a = math.radians(ang + rnd.uniform(-C["jitter"], C["jitter"]))
            L = rnd.uniform(*C["len"])
            if keep and ang not in keep:          # draws stay, so the other cracks don't move
                continue
            du = g.math("SUBTRACT", uu, cu, (-1900, y - 150), F)
            dv = g.math("SUBTRACT", sp.outputs["Z"], cv, (-1900, y - 300), F)
            along = g.math("ADD", g.math("MULTIPLY", du, math.cos(a), (-1750, y - 150), F),
                           g.math("MULTIPLY", dv, math.sin(a), (-1750, y - 300), F), (-1600, y - 200), F)
            perp = g.math("SUBTRACT", g.math("MULTIPLY", dv, math.cos(a), (-1750, y - 450), F),
                          g.math("MULTIPLY", du, math.sin(a), (-1750, y - 600), F), (-1600, y - 500), F)
            perp = g.math("ABSOLUTE", g.math("ADD", perp, wob, (-1450, y - 500), F), 0.0, (-1300, y - 500), F)
            t = g.range(along, 0.0, L, (-1450, y - 200), 1.0, 0.0, F)
            t = g.math("MULTIPLY", t, g.math("GREATER_THAN", along, 0.0, (-1300, y - 300), F), (-1150, y - 250), F)
            tw = g.math("POWER", t, 0.5, (-1000, y - 250), F)
            wc = g.math("MAXIMUM", g.math("MULTIPLY", tw, C["core"], (-1000, y - 400), F), 1e-5, (-850, y - 400), F)
            c = g.math("MULTIPLY", g.math("SUBTRACT", 1.0, g.math("DIVIDE", perp, wc, (-700, y - 450), F), (-550, y - 450), F, clamp=True), on, (-400, y - 400), F)
            h = g.math("SUBTRACT", 1.0, g.math("DIVIDE", perp, C["halo"], (-700, y - 600), F), (-550, y - 600), F, clamp=True)
            h = g.math("MULTIPLY", h, g.math("MULTIPLY", tw, on, (-550, y - 700), F), (-400, y - 600), F)
            core = c if core is None else g.math("MAXIMUM", core, c, (-250, y - 400), F)
            halo = h if halo is None else g.math("MAXIMUM", halo, h, (-250, y - 600), F)
            y -= 800
    dis = g.node("ShaderNodeTexNoise", (-2400, y), F, Scale=2.0, Detail=3.0); g.link(pos, dis.inputs["Vector"])
    off = g.n("ShaderNodeVectorMath", (-2250, y), operation="MULTIPLY_ADD")
    g.link(dis.outputs["Color"], off.inputs[0]); off.inputs[1].default_value = (C["net_dist"],) * 3; g.link(pos, off.inputs[2])
    ve = g.node("ShaderNodeTexVoronoi", (-2100, y), F, Scale=C["net_scale"]); ve.feature = "DISTANCE_TO_EDGE"
    g.link(off.outputs[0], ve.inputs["Vector"])
    vc = g.node("ShaderNodeTexVoronoi", (-2100, y - 250), F, Scale=C["net_scale"]); g.link(off.outputs[0], vc.inputs["Vector"])
    vcs = g.node("ShaderNodeSeparateColor", (-1950, y - 250), F); g.link(vc.outputs["Color"], vcs.inputs[0])
    keep_e = g.math("GREATER_THAN", vcs.outputs["Red"], C["net_keep"], (-1800, y - 250), F)
    patch = g.range(g.noise(pos, 0.45, (-1950, y - 450), F, detail=3), *C["net_patch"], (-1800, y - 450), frame=F)
    pres = g.math("MULTIPLY", keep_e, patch, (-1650, y - 350), F)
    nc = g.math("MULTIPLY", g.math("SUBTRACT", 1.0, g.math("DIVIDE", ve.outputs["Distance"], C["core"] * 0.8, (-1800, y), F), (-1650, y), F, clamp=True), pres, (-1500, y), F)
    nh = g.math("MULTIPLY", g.math("SUBTRACT", 1.0, g.math("DIVIDE", ve.outputs["Distance"], C["halo"] * 0.7, (-1800, y - 100), F), (-1650, y - 100), F, clamp=True), pres, (-1500, y - 100), F)
    core = nc if core is None else g.math("MAXIMUM", core, nc, (-250, y), F)
    halo = nh if halo is None else g.math("MAXIMUM", halo, nh, (-250, y - 100), F)
    core.node.label = "crack core"; halo.node.label = "crack halo"
    return core, halo


def add_cracks(mat, openings=(), crack=None):
    """On a weathered_concrete material: shrinkage cracks from opening corners + patchy map-cracking; dark core over everything, grime halo, groove. openings: (axis 'x'|'y', plane, u0, u1, v0, v1, top_only[, keep_angles])."""
    C = dict(CRACK, **(crack or {}))
    g, F = _frame(mat, "Cracks")
    nt = mat.node_tree
    core, halo = _crack_masks(g, F, openings, C)
    mix = next(n for n in nt.nodes if n.label == "Wear Layered (BRDFLayered)")
    old = mix.inputs["Fac"].links[0].from_socket
    g.link(g.math("MAXIMUM", old, g.math("MULTIPLY", halo, C["halo_dirt"], (350, -4700), F), (500, -4650), F), mix.inputs["Fac"])
    bev = next(n for n in nt.nodes if n.label == "Round edges (TexEdges)")
    users = [l.to_socket for l in bev.outputs["Normal"].links]
    cb = g.node("ShaderNodeBump", (bev.location.x + 200, bev.location.y - 200), F, label="crack groove")
    cb.invert = True; cb.inputs["Distance"].default_value = C["depth"]
    g.link(core, cb.inputs["Height"]); g.link(bev.outputs["Normal"], cb.inputs["Normal"])
    for u in users:
        g.link(cb.outputs["Normal"], u)
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    last = out.inputs["Surface"].links[0].from_socket
    dark = g.node("ShaderNodeBsdfPrincipled", (out.location.x - 200, out.location.y - 300), F, label="crack interior", Roughness=0.95)
    dark.inputs["Base Color"].default_value = (0.03, 0.03, 0.028, 1)
    mx = g.node("ShaderNodeMixShader", (out.location.x - 100, out.location.y - 100), F, label="cracks over surface")
    g.link(g.math("MULTIPLY", core, 0.9, (out.location.x - 300, out.location.y - 500), F), mx.inputs["Fac"])
    g.link(last, mx.inputs[1]); g.link(dark.outputs[0], mx.inputs[2]); g.link(mx.outputs[0], out.inputs["Surface"])
    return mat
