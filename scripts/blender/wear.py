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


class _GN:
    """Small Geometry Nodes graph builder."""

    def __init__(self, ng):
        self.nt, self.L = ng, ng.links.new

    def n(self, kind, loc, **props):
        node = self.nt.nodes.new(kind)
        node.location = loc
        for k, v in props.items():
            setattr(node, k, v)
        return node

    def math(self, op, a, b, loc, clamp=False):
        node = self.n("ShaderNodeMath", loc, operation=op, use_clamp=clamp)
        for i, v in enumerate((a, b)):
            if isinstance(v, (int, float)):
                node.inputs[i].default_value = v
            else:
                self.L(v, node.inputs[i])
        return node.outputs[0]

    def range(self, v, fmin, fmax, loc, tmin=0.0, tmax=1.0):
        node = self.n("ShaderNodeMapRange", loc)
        for k, x in (("From Min", fmin), ("From Max", fmax), ("To Min", tmin), ("To Max", tmax)):
            if isinstance(x, (int, float)):
                node.inputs[k].default_value = x
            else:
                self.L(x, node.inputs[k])
        self.L(v, node.inputs["Value"])
        return node.outputs["Result"]

    def noise(self, vec, scale, loc, detail=6.0, rough=0.6):
        node = self.n("ShaderNodeTexNoise", loc)
        node.inputs["Scale"].default_value = scale
        node.inputs["Detail"].default_value = detail
        node.inputs["Roughness"].default_value = rough
        self.L(vec, node.inputs["Vector"])
        return node.outputs[0]

    def store(self, geo, name, dtype, val, loc):
        st = self.n("GeometryNodeStoreNamedAttribute", loc, data_type=dtype, domain="POINT")
        st.inputs["Name"].default_value = name
        self.L(geo, st.inputs["Geometry"])
        self.L(val, sock(st.inputs, "Value"))
        return st.outputs["Geometry"]

    def named(self, name, dtype, loc):
        node = self.n("GeometryNodeInputNamedAttribute", loc, data_type=dtype)
        node.inputs["Name"].default_value = name
        return node.outputs[0]


def _input(ng, name, kind, default, subtype=None):
    it = ng.interface.new_socket(name, in_out="INPUT", socket_type=kind)
    it.default_value = default
    if subtype:
        it.subtype = subtype


def edge_wear_group(name="Edge Wear + Chips", band=0.08, level=3, chip_reach=0.045,
                    chip_depth=0.018, chipped_share=0.55, sharp_deg=30.0, chips=True,
                    bite_scale=22.0, segment_scale=2.2):
    """Geometry Nodes modifier: edge field for every point, real chips in the arris band."""
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
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    b = _GN(ng)
    L = b.L
    gi = b.n("NodeGroupInput", (-1400, 0))
    go = b.n("NodeGroupOutput", (2700, 0))

    # 1. distance to the nearest convex arris. Measured on these meshes (outward normals):
    #    convex arrises give a POSITIVE signed angle, the L-wall's inner corner a negative one.
    ang = b.n("GeometryNodeInputMeshEdgeAngle", (-1400, -300))
    cmp = b.n("FunctionNodeCompare", (-1200, -300), data_type="FLOAT", operation="GREATER_THAN")
    L(ang.outputs["Signed Angle"], sock(cmp.inputs, "A"))
    L(gi.outputs["Sharp Angle"], sock(cmp.inputs, "B"))
    m2c = b.n("GeometryNodeMeshToCurve", (-1000, -200))
    L(gi.outputs["Geometry"], m2c.inputs["Mesh"])
    L(cmp.outputs[0], m2c.inputs["Selection"])
    c2m = b.n("GeometryNodeCurveToMesh", (-800, -200))
    L(m2c.outputs["Curve"], c2m.inputs["Curve"])
    prox = b.n("GeometryNodeProximity", (-600, -200), target_element="EDGES")
    L(c2m.outputs["Mesh"], prox.inputs["Geometry"])
    pos = b.n("GeometryNodeInputPosition", (-600, -450))
    g = b.store(gi.outputs["Geometry"], "edge_dist", "FLOAT", prox.outputs["Distance"], (-350, 0))
    g = b.store(g, "rest_pos", "FLOAT_VECTOR", pos.outputs["Position"], (-150, 0))

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
    # Noise Texture clusters around 0.5 (sd ~0.1), so map the share to a threshold near 0.5
    t = b.math("SUBTRACT", 0.5, gi.outputs["Chipped Share"], (500, -700))
    t = b.math("MULTIPLY", t, 0.35, (650, -700))
    t = b.math("ADD", t, 0.5, (750, -700))
    seg = b.range(b.noise(rp, segment_scale, (650, -500), detail=2), b.math("SUBTRACT", t, 0.04, (850, -650)),
                  b.math("ADD", t, 0.04, (850, -760)), (1000, -550))
    bite = b.range(b.noise(rp, bite_scale, (650, -900), detail=8, rough=0.7), 0.35, 0.75, (1000, -850))
    reach = b.math("MULTIPLY", b.math("MULTIPLY", bite, seg, (1200, -700)),
                   gi.outputs["Chip Reach"], (1380, -700))
    chip = b.range(b.math("SUBTRACT", reach, dd, (1550, -500)), 0.0, 0.002, (1720, -500))
    prof = b.range(dd, 0.0, gi.outputs["Chip Reach"], (1550, -800), 1.0, 0.35)
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
    join = b.n("GeometryNodeJoinGeometry", (2450, 0))
    L(setp.outputs["Geometry"], join.inputs[0])
    L(sep.outputs["Inverted"], join.inputs[0])
    weld = b.n("GeometryNodeMergeByDistance", (2580, 0))
    weld.inputs["Distance"].default_value = 1e-5
    L(join.outputs[0], weld.inputs["Geometry"])
    L(weld.outputs["Geometry"], go.inputs["Geometry"])
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
    n = g.node("ShaderNodeAttribute", loc, frame, label="attr: " + name)
    n.attribute_name = name
    return n.outputs[out]


def _noise(g, vec, scale, loc, frame, detail=6.0, rough=0.6, label=None):
    n = g.node("ShaderNodeTexNoise", loc, frame, label=label, Scale=scale, Detail=detail,
               Roughness=rough)
    g.link(vec, n.inputs["Vector"])
    return n.outputs[0]


def _range(g, val, fmin, fmax, loc, frame, tmin=0.0, tmax=1.0, label=None, smooth=False):
    n = g.node("ShaderNodeMapRange", loc, frame, label=label)
    if smooth:
        n.interpolation_type = "SMOOTHSTEP"
    n.inputs["From Min"].default_value, n.inputs["From Max"].default_value = fmin, fmax
    n.inputs["To Min"].default_value, n.inputs["To Max"].default_value = tmin, tmax
    g.link(val, n.inputs["Value"])
    return n.outputs["Result"]


def _math(g, op, a, b, loc, frame, clamp=False):
    n = g.node("ShaderNodeMath", loc, frame)
    n.operation, n.use_clamp = op, clamp
    for i, v in enumerate((a, b)):
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            g.link(v, n.inputs[i])
    return n.outputs[0]


def weathered_concrete(name="CONCRETE_WEATHERED", dirt_band=0.035, dirt_amount=0.85,
                       dirt_noise_scale=9.0, stain=True):
    """concrete_study base (tone, maps, round edges, leak stain) + procedural dirty edges from
    the GN `edge_dist` field + a fresh-break material where GN cut a chip (`chip` > 0)."""
    mat = sm.concrete_study(name=name, edge_dark=False, stain=stain, bevel_chips=False)
    g = G.__new__(G)
    g.nt, g.frames = mat.node_tree, {}
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
