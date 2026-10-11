"""Weathered varnished wood: worn edges (shading), dents along arrises and torn-off varnished
skin on the top surface that exposes the pale inner wood (both real geometry).

Builds on wear.py (edge field, dicing, Blender 5.2 modifier inputs) and study_materials.coated_wood.

  round_arrises()  -- real 2.5 mm bevel (the Bevel *node* is invalid on MNEE caustic receivers)
  grain_uv()       -- alias of archviz.directional_uv (U along each piece's long axis)
  wood_wear_group()-- GN: edge_dist field; arris band + top faces subdivided; chips at arrises;
                      breaks on the top, stretched along the grain; stores `chip`, `break`
  weathered_wood() -- shader: varnish worn + grime at arrises; inner wood where chip/break > 0
"""
import math

import bmesh
import bpy

import study_materials as sm
from study_materials import sock
from wear import _GN, _input, _attr, _noise, _range, _math


# --- geometry ---------------------------------------------------------------------------

def round_arrises(obj, width=0.0025, segments=2, min_angle_deg=30.0):
    """Real rounded arrises. Two segments keep each new edge at 45 deg, so the GN edge field
    (threshold 30 deg) still finds them."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    edges = [e for e in bm.edges if e.is_manifold and e.calc_face_angle(0) > math.radians(min_angle_deg)]
    bmesh.ops.bevel(bm, geom=edges, offset=width, segments=segments, profile=0.5,
                    affect="EDGES", clamp_overlap=True)
    bm.to_mesh(obj.data)
    bm.free()


def grain_uv(obj, size, name="BoxUV", axis=None, along="U"):
    """Kept for existing scripts: archviz.directional_uv, which serves every directional texture
    (not only wood)."""
    import archviz
    return archviz.directional_uv(obj, size, name=name, axis=axis, along=along)


# --- Geometry Nodes ---------------------------------------------------------------------

def wood_wear_group(name="Wood Wear + Breaks", band=0.02, level=3,
                    chip_reach=0.006, chip_depth=0.0025, chipped_share=0.30,
                    break_share=0.5, break_depth=0.0015, grain_stretch=(35.0, 5.0, 35.0),
                    seed=(0.0, 0.0, 0.0), sharp_deg=30.0):
    """grain_stretch: noise scale per world axis for break outlines; the small value is the
    grain axis (the board's long axis), so breaks run long along the grain."""
    ng = bpy.data.node_groups.get(name)
    if ng:
        bpy.data.node_groups.remove(ng)
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    _input(ng, "Sharp Angle", "NodeSocketFloat", math.radians(sharp_deg), "ANGLE")
    _input(ng, "Band", "NodeSocketFloat", band, "DISTANCE")
    _input(ng, "Subdivisions", "NodeSocketInt", level)
    _input(ng, "Chip Reach", "NodeSocketFloat", chip_reach, "DISTANCE")
    _input(ng, "Chip Depth", "NodeSocketFloat", chip_depth, "DISTANCE")
    _input(ng, "Chipped Share", "NodeSocketFloat", chipped_share, "FACTOR")
    _input(ng, "Break Share", "NodeSocketFloat", break_share, "FACTOR")
    _input(ng, "Break Depth", "NodeSocketFloat", break_depth, "DISTANCE")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    b = _GN(ng)
    L = b.L
    gi = b.n("NodeGroupInput", (-1600, 0))
    go = b.n("NodeGroupOutput", (3000, 0))

    # 1. edge field (convex arrises are positive signed angles on these meshes)
    ang = b.n("GeometryNodeInputMeshEdgeAngle", (-1600, -300))
    cmp = b.n("FunctionNodeCompare", (-1400, -300), data_type="FLOAT", operation="GREATER_THAN")
    L(ang.outputs["Signed Angle"], sock(cmp.inputs, "A"))
    L(gi.outputs["Sharp Angle"], sock(cmp.inputs, "B"))
    m2c = b.n("GeometryNodeMeshToCurve", (-1200, -200))
    L(gi.outputs["Geometry"], m2c.inputs["Mesh"])
    L(cmp.outputs[0], m2c.inputs["Selection"])
    c2m = b.n("GeometryNodeCurveToMesh", (-1000, -200))
    L(m2c.outputs["Curve"], c2m.inputs["Curve"])
    prox = b.n("GeometryNodeProximity", (-800, -200), target_element="EDGES")
    L(c2m.outputs["Mesh"], prox.inputs["Geometry"])
    pos = b.n("GeometryNodeInputPosition", (-800, -450))
    seed_v = b.n("ShaderNodeVectorMath", (-650, -450), operation="ADD")
    L(pos.outputs["Position"], seed_v.inputs[0])
    seed_v.inputs[1].default_value = seed
    g = b.store(gi.outputs["Geometry"], "edge_dist", "FLOAT", prox.outputs["Distance"], (-550, 0))
    g = b.store(g, "rest_pos", "FLOAT_VECTOR", seed_v.outputs["Vector"], (-350, 0))

    # 2. densify the arris band and the up-facing faces only
    nrm0 = b.n("GeometryNodeInputNormal", (-350, -500))
    sepz = b.n("ShaderNodeSeparateXYZ", (-200, -500))
    L(nrm0.outputs["Normal"], sepz.inputs["Vector"])
    up = b.n("FunctionNodeCompare", (-50, -500), data_type="FLOAT", operation="GREATER_THAN")
    L(sepz.outputs["Z"], sock(up.inputs, "A"))
    sock(up.inputs, "B").default_value = 0.9
    in_band = b.n("FunctionNodeCompare", (-50, -300), data_type="FLOAT", operation="LESS_THAN")
    L(b.named("edge_dist", "FLOAT", (-250, -300)), sock(in_band.inputs, "A"))
    L(gi.outputs["Band"], sock(in_band.inputs, "B"))
    either = b.n("FunctionNodeBooleanMath", (120, -400), operation="OR")
    L(in_band.outputs[0], either.inputs[0])
    L(up.outputs[0], either.inputs[1])
    sep = b.n("GeometryNodeSeparateGeometry", (250, 0), domain="FACE")
    L(g, sep.inputs["Geometry"])
    L(either.outputs[0], sep.inputs["Selection"])
    sub = b.n("GeometryNodeSubdivideMesh", (450, 100))
    L(sep.outputs["Selection"], sub.inputs["Mesh"])
    L(gi.outputs["Subdivisions"], sub.inputs["Level"])

    rp = b.named("rest_pos", "FLOAT_VECTOR", (450, -400))
    dd = b.named("edge_dist", "FLOAT", (450, -250))

    # 3. dents along the arrises (same field as the concrete chips, wood-sized)
    t = b.math("ADD", b.math("MULTIPLY", b.math("SUBTRACT", 0.5, gi.outputs["Chipped Share"],
                                                (500, -700)), 0.35, (650, -700)), 0.5, (750, -700))
    seg = b.range(b.noise(rp, 6.0, (650, -500), detail=2), b.math("SUBTRACT", t, 0.04, (850, -650)),
                  b.math("ADD", t, 0.04, (850, -760)), (1000, -550))
    bite = b.range(b.noise(rp, 70.0, (650, -900), detail=8, rough=0.7), 0.35, 0.75, (1000, -850))
    reach = b.math("MULTIPLY", b.math("MULTIPLY", bite, seg, (1200, -700)),
                   gi.outputs["Chip Reach"], (1380, -700))
    chip = b.range(b.math("SUBTRACT", reach, dd, (1550, -500)), 0.0, 0.0006, (1720, -500))
    prof = b.range(dd, 0.0, gi.outputs["Chip Reach"], (1550, -800), 1.0, 0.4)
    chip_d = b.math("MULTIPLY", b.math("MULTIPLY", chip, prof, (1900, -650)),
                    gi.outputs["Chip Depth"], (2050, -700))

    # 4. torn varnished skin on the top: sparse patches x outline stretched along the grain
    nrm = b.n("GeometryNodeInputNormal", (650, -1150))
    sepn = b.n("ShaderNodeSeparateXYZ", (800, -1150))
    L(nrm.outputs["Normal"], sepn.inputs["Vector"])
    top = b.range(sepn.outputs["Z"], 0.85, 0.95, (1000, -1150))
    ts = b.math("ADD", b.math("MULTIPLY", b.math("SUBTRACT", 0.5, gi.outputs["Break Share"],
                                                 (500, -1300)), 0.35, (650, -1300)), 0.58, (750, -1300))
    sparse = b.range(b.noise(rp, 3.0, (650, -1450), detail=2), ts,
                     b.math("ADD", ts, 0.04, (850, -1400)), (1000, -1450))
    stretch = b.n("ShaderNodeVectorMath", (650, -1650), operation="MULTIPLY")
    L(rp, stretch.inputs[0])
    stretch.inputs[1].default_value = grain_stretch
    outline = b.range(b.noise(stretch.outputs["Vector"], 1.0, (800, -1650), detail=7, rough=0.72),
                      0.52, 0.545, (1000, -1650))
    fib_v = b.n("ShaderNodeVectorMath", (650, -1850), operation="MULTIPLY")
    L(rp, fib_v.inputs[0])
    fib_v.inputs[1].default_value = (grain_stretch[0] * 14, grain_stretch[1] * 3, grain_stretch[2] * 14)
    fibres = b.range(b.noise(fib_v.outputs["Vector"], 1.0, (800, -1850), detail=3), 0.3, 0.7,
                     (1000, -1850), 0.55, 1.0)
    brk = b.math("MULTIPLY", b.math("MULTIPLY", top, sparse, (1200, -1300)), outline, (1380, -1400))
    brk_d = b.math("MULTIPLY", b.math("MULTIPLY", brk, fibres, (1550, -1500)),
                   gi.outputs["Break Depth"], (1720, -1500))

    depth = b.math("MAXIMUM", chip_d, brk_d, (2200, -900))
    off = b.n("ShaderNodeVectorMath", (2350, -600), operation="SCALE")
    L(b.n("GeometryNodeInputNormal", (2200, -600)).outputs["Normal"], off.inputs[0])
    L(b.math("MULTIPLY", depth, -1.0, (2350, -800)), off.inputs["Scale"])
    gb = b.store(sub.outputs["Mesh"], "chip", "FLOAT", chip_d, (1300, 100))
    gb = b.store(gb, "break", "FLOAT", brk_d, (1500, 100))
    setp = b.n("GeometryNodeSetPosition", (2550, 100))
    L(gb, setp.inputs["Geometry"])
    L(off.outputs["Vector"], setp.inputs["Offset"])
    join = b.n("GeometryNodeJoinGeometry", (2700, 0))
    L(setp.outputs["Geometry"], join.inputs[0])
    L(sep.outputs["Inverted"], join.inputs[0])
    weld = b.n("GeometryNodeMergeByDistance", (2850, 0))
    weld.inputs["Distance"].default_value = 1e-6
    L(join.outputs[0], weld.inputs["Geometry"])
    L(weld.outputs["Geometry"], go.inputs["Geometry"])
    return ng


# --- shading ----------------------------------------------------------------------------

def weathered_wood(name="PINE_WEATHERED", wear_band=0.012, wear_amount=0.9,
                   inner_tint=(0.80, 0.60, 0.36), inner_mix=0.30, inner_gain=1.7):
    """coated_wood base (levels, satin coat trap) + worn varnish/grime at arrises + inner wood."""
    mat = sm.coated_wood(name=name, round_edge=0)
    g = sm.G.__new__(sm.G)
    g.nt, g.frames = mat.node_tree, {}
    nt = mat.node_tree
    coated = next(n for n in nt.nodes if n.label == "Pine + satin varnish coat")
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    col_src = coated.inputs["Base Color"].links[0].from_socket
    nrm_src = coated.inputs["Normal"].links[0].from_socket

    g.frame("Edge field + damage attributes (from GN)", (0.22, 0.22, 0.32))
    g.frame("Worn edges: varnish gone + hand grime (shading)", (0.32, 0.24, 0.16))
    g.frame("Inner wood where the skin broke (geometry from GN)", (0.30, 0.26, 0.16))
    F_FLD, F_WEAR, F_IN = list(g.frames)
    x0, y0 = -1500, -700
    d = _attr(g, "edge_dist", (x0, y0), F_FLD)
    rest = _attr(g, "rest_pos", (x0, y0 - 180), F_FLD, out="Vector")
    chip = _range(g, _attr(g, "chip", (x0, y0 - 360), F_FLD), 0.0, 0.0003, (x0 + 250, y0 - 360),
                  F_FLD, label="chip mask")
    brk = _range(g, _attr(g, "break", (x0, y0 - 540), F_FLD), 0.0, 0.00015, (x0 + 250, y0 - 540),
                 F_FLD, label="break mask")
    exposed = _math(g, "MAXIMUM", chip, brk, (x0 + 450, y0 - 450), F_FLD)
    exposed.node.label = "exposed inner wood"

    band = _range(g, d, 0.0, wear_band, (x0 + 250, y0 + 250), F_WEAR, 1.0, 0.0,
                  label="edge band", smooth=True)
    blot = _range(g, _noise(g, rest, 28.0, (x0 + 250, y0 + 50), F_WEAR, detail=10, rough=0.65,
                            label="wear breakup"), 0.38, 0.62, (x0 + 450, y0 + 50), F_WEAR)
    wear_m = _math(g, "MULTIPLY", _math(g, "MULTIPLY", band, blot, (x0 + 650, y0 + 150), F_WEAR),
                   wear_amount, (x0 + 800, y0 + 150), F_WEAR)
    wear_m = _math(g, "MULTIPLY", wear_m, _math(g, "SUBTRACT", 1.0, exposed, (x0 + 800, y0 - 20),
                                                F_WEAR, clamp=True), (x0 + 950, y0 + 100), F_WEAR)
    wear_m.node.label = "worn edge mask"
    grime = g.node("ShaderNodeMix", (x0 + 950, y0 + 350), F_WEAR, label="hand grime (darker)")
    grime.data_type, grime.blend_type = "RGBA", "MULTIPLY"
    grime.inputs["Factor"].default_value = 1.0
    sock(grime.inputs, "B").default_value = (0.55, 0.50, 0.44, 1)
    g.link(col_src, sock(grime.inputs, "A"))
    worn = g.node("ShaderNodeBsdfPrincipled", (x0 + 1150, y0 + 300), F_WEAR,
                  label="Worn edge: no varnish, grimy", Roughness=0.62)
    g.link(sock(grime.outputs, "Result"), worn.inputs["Base Color"])
    g.link(nrm_src, worn.inputs["Normal"])

    # Raw pine under the varnish: same grain, much lighter, slightly yellower -- not a flat tint
    lift = g.node("ShaderNodeMix", (x0 + 450, y0 - 800), F_IN, label="inner wood: lighter (no amber varnish)")
    lift.data_type, lift.blend_type = "RGBA", "MULTIPLY"
    lift.inputs["Factor"].default_value = 1.0
    sock(lift.inputs, "B").default_value = (inner_gain, inner_gain * 1.02, inner_gain * 1.08, 1)
    g.link(col_src, sock(lift.inputs, "A"))
    pale = g.node("ShaderNodeMix", (x0 + 650, y0 - 800), F_IN, label="inner wood: toward raw pine")
    pale.data_type = "RGBA"
    pale.inputs["Factor"].default_value = inner_mix
    sock(pale.inputs, "B").default_value = (*inner_tint, 1)
    g.link(sock(lift.outputs, "Result"), sock(pale.inputs, "A"))
    fib = g.node("ShaderNodeMapping", (x0 + 250, y0 - 1000), F_IN, label="fibres along grain (UV U)")
    fib.inputs["Scale"].default_value = (20.0, 900.0, 1.0)
    uvn = g.uv("BoxUV", (x0 + 50, y0 - 1000), F_IN)
    g.link(uvn, fib.inputs["Vector"])
    fbump = g.node("ShaderNodeBump", (x0 + 650, y0 - 1050), F_IN, label="torn fibres", Distance=0.0012)
    g.link(_noise(g, fib.outputs["Vector"], 1.0, (x0 + 450, y0 - 1050), F_IN, detail=4),
           fbump.inputs["Height"])
    g.link(nrm_src, fbump.inputs["Normal"])
    inner = g.node("ShaderNodeBsdfPrincipled", (x0 + 900, y0 - 850), F_IN,
                   label="Inner wood (raw)", Roughness=0.85)
    g.link(sock(pale.outputs, "Result"), inner.inputs["Base Color"])
    g.link(fbump.outputs["Normal"], inner.inputs["Normal"])

    m1 = g.node("ShaderNodeMixShader", (300, 100), label="worn edges over varnish")
    g.link(wear_m, m1.inputs["Fac"])
    g.link(coated.outputs["BSDF"], m1.inputs[1])
    g.link(worn.outputs["BSDF"], m1.inputs[2])
    m2 = g.node("ShaderNodeMixShader", (500, 0), label="inner wood where broken")
    g.link(exposed, m2.inputs["Fac"])
    g.link(m1.outputs["Shader"], m2.inputs[1])
    g.link(inner.outputs["BSDF"], m2.inputs[2])
    out.location = (700, 0)
    g.link(m2.outputs["Shader"], out.inputs["Surface"])
    mat["recipe"] = "weathered varnished pine: worn edges (shading) + GN dents/breaks (geometry)"
    return mat
