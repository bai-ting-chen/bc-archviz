"""Edge chips as real geometry: dice a mesh, then a Geometry Nodes modifier that cuts chips along arrises.

Rhino meshes are too coarse for curvature methods (a beam arrives as 8 faces), so:
  1. dice()              -- subdivide in place until no edge is longer than `size`
  2. edge_wear_group()   -- Geometry Nodes modifier:
       edge field : Edge Angle (convex, sharper than threshold) -> Mesh to Curve -> Proximity
                    -> `edge_dist` = metres to the nearest arris, plus `rest_pos`
       chips      : only faces within `Band` of an arris are split off and subdivided; there
                    reach = Chip Reach x bite noise x segment noise, chip where edge_dist < reach,
                    depth = Chip Depth x profile x fracture noise, Set Position along -normal;
                    stored as `chip` (metres); band and interior are rejoined and welded
"""
import math

import bmesh
import bpy

from materials.shared.nodes import G
from materials.shared.nodes import sock


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


def input_socket(ng, name, kind, default, subtype=None):
    """Add a group input with a default (and an optional unit subtype)."""
    it = ng.interface.new_socket(name, in_out="INPUT", socket_type=kind)
    it.default_value = default
    if subtype:
        it.subtype = subtype


def edge_field(b, gi, x0):
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


def chip_field(b, gi, rp, dd, seg_scale, bite_scale, soft, prof_end):
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


def rejoin(b, moved, sep, go, x0, weld_dist):
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
    input_socket(ng, "Sharp Angle", "NodeSocketFloat", math.radians(sharp_deg), "ANGLE")
    input_socket(ng, "Band", "NodeSocketFloat", band, "DISTANCE")
    input_socket(ng, "Band Subdivisions", "NodeSocketInt", level)
    input_socket(ng, "Chip Reach", "NodeSocketFloat", chip_reach, "DISTANCE")
    input_socket(ng, "Chip Depth", "NodeSocketFloat", chip_depth if chips else 0.0, "DISTANCE")
    input_socket(ng, "Chipped Share", "NodeSocketFloat", chipped_share, "FACTOR")
    input_socket(ng, "Seed", "NodeSocketVector", seed)
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    b = G(ng, clear=False)
    L = b.L
    gi = b.n("NodeGroupInput", (-1400, 0))
    go = b.n("NodeGroupOutput", (2700, 0))

    # 1. distance to the nearest convex arris
    g = edge_field(b, gi, -1400)

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
    chip, prof = chip_field(b, gi, rp, dd, segment_scale, bite_scale, 0.002, 0.35)
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
    rejoin(b, setp.outputs["Geometry"], sep, go, 2450, 1e-5)
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
