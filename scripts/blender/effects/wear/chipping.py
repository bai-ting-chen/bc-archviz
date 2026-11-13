"""Geometry chips, flaked coating fields and verified bare-substrate scans."""
import math

import bmesh
import bpy

from materials.shared.node_graph import NodeGraph
from materials.shared.node_graph import active_socket
from effects.wear.wear_locations import edge_field
from dataclasses import dataclass, replace
from effects.wear.masks import asset_mask


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




def chip_field(b, gi, rp, dd, seg_scale, bite_scale, soft, prof_end):
    """Chips along the arris: segments of the edge chipped (share -> threshold; Noise clusters
    near 0.5, sd ~0.1), bite noise varies the reach. Returns (chip 0..1, depth profile)."""
    t = b.math("SUBTRACT", 0.5, gi.outputs["Chipped Share"], (500, -700))
    t = b.math("MULTIPLY", t, 0.35, (650, -700))
    t = b.math("ADD", t, 0.5, (750, -700))
    seg = b.map_range(b.noise_texture(rp, seg_scale, (650, -500), detail=2), b.math("SUBTRACT", t, 0.04, (850, -650)),
                  b.math("ADD", t, 0.04, (850, -760)), (1000, -550))
    bite = b.map_range(b.noise_texture(rp, bite_scale, (650, -900), detail=8, rough=0.7), 0.35, 0.75, (1000, -850))
    reach = b.math("MULTIPLY", b.math("MULTIPLY", bite, seg, (1200, -700)),
                   gi.outputs["Chip Reach"], (1380, -700))
    chip = b.map_range(b.math("SUBTRACT", reach, dd, (1550, -500)), 0.0, soft, (1720, -500))
    prof = b.map_range(dd, 0.0, gi.outputs["Chip Reach"], (1550, -800), 1.0, prof_end)
    return chip, prof


def rejoin(b, moved, sep, go, x0, weld_dist):
    """Rejoin the displaced band with the untouched interior and weld the seam."""
    join = b.node_with_props("GeometryNodeJoinGeometry", (x0, 0))
    b.link(moved, join.inputs[0])
    b.link(sep.outputs["Inverted"], join.inputs[0])
    weld = b.node_with_props("GeometryNodeMergeByDistance", (x0 + 130, 0))
    weld.inputs["Distance"].default_value = weld_dist
    b.link(join.outputs[0], weld.inputs["Geometry"])
    b.link(weld.outputs["Geometry"], go.inputs["Geometry"])


@dataclass
class GrainBreaks:
    """Torn coat on up-facing faces, its outline stretched along the grain (wood).
    grain_stretch: noise scale per world axis; the small value is the grain axis."""
    share: float = 0.5
    depth_m: float = 0.0015
    grain_stretch: tuple = (35.0, 5.0, 35.0)


def edge_wear_group(name="Edge Wear + Chips", band=0.08, level=3, chip_reach=0.045,
                    chip_depth=0.018, chipped_share=0.55, sharp_deg=30.0, chips=True,
                    bite_scale=22.0, segment_scale=2.2, seed=(0.0, 0.0, 0.0),
                    chip_soft=0.002, profile_end=0.35, fracture=0.4, breaks=None):
    """Geometry Nodes modifier: edge field for every point, real chips in the arris band, and
    optional grain breaks (GrainBreaks) on up-facing faces. fracture: chip-depth variation 0–1.
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
    if breaks:
        input_socket(ng, "Break Share", "NodeSocketFloat", breaks.share, "FACTOR")
        input_socket(ng, "Break Depth", "NodeSocketFloat", breaks.depth_m, "DISTANCE")
    input_socket(ng, "Seed", "NodeSocketVector", seed)
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    b = NodeGraph(ng, clear=False)
    L = b.link
    gi = b.node_with_props("NodeGroupInput", (-1400, 0))
    go = b.node_with_props("NodeGroupOutput", (2700, 0))

    # 1. distance to the nearest convex arris
    g = edge_field(b, gi, -1400, vertex_junctions=True)

    # 2. split off the arris band (and the up-facing faces for breaks), densify only that
    in_band = b.node_with_props("FunctionNodeCompare", (50, -300), data_type="FLOAT", operation="LESS_THAN")
    L(b.named_attribute("edge_dist", "FLOAT", (-150, -300)), active_socket(in_band.inputs, "A"))
    L(gi.outputs["Band"], active_socket(in_band.inputs, "B"))
    selected = in_band.outputs[0]
    if breaks:
        selected = _or_up_facing(b, selected)
    sep = b.node_with_props("GeometryNodeSeparateGeometry", (250, 0), domain="FACE")
    L(g, sep.inputs["Geometry"])
    L(selected, sep.inputs["Selection"])
    sub = b.node_with_props("GeometryNodeSubdivideMesh", (450, 100))
    L(sep.outputs["Selection"], sub.inputs["Mesh"])
    L(gi.outputs["Band Subdivisions"], sub.inputs["Level"])

    # 3. chip field on the dense band
    rp = b.named_attribute("rest_pos", "FLOAT_VECTOR", (450, -400))
    dd = b.named_attribute("edge_dist", "FLOAT", (450, -250))
    chip, prof = chip_field(b, gi, rp, dd, segment_scale, bite_scale, chip_soft, profile_end)
    chip_depth_in = gi.outputs["Chip Depth"]
    if fracture:
        frac = b.map_range(b.noise_texture(rp, 140.0, (1380, -1000), detail=4), 0.3, 0.7, (1550, -1000),
                       1.0 - fracture, 1.0)
        chip_depth_in = b.math("MULTIPLY", frac, chip_depth_in, (1900, -900))
    depth = b.math("MULTIPLY", b.math("MULTIPLY", chip, prof, (1900, -650)), chip_depth_in, (2050, -750))
    geo = b.store_attribute(sub.outputs["Mesh"], "chip", "FLOAT", depth, (1300, 100))

    # 4. grain breaks on the top, deepest of chip and break wins
    if breaks:
        brk = _grain_breaks(b, gi, rp, breaks.grain_stretch)
        geo = b.store_attribute(geo, "break", "FLOAT", brk, (1500, 100))
        depth = b.math("MAXIMUM", depth, brk, (2200, -900))
    nrm = b.node_with_props("GeometryNodeInputNormal", (1900, -350))
    off = b.node_with_props("ShaderNodeVectorMath", (2150, -400), operation="SCALE")
    L(nrm.outputs["Normal"], off.inputs[0])
    L(b.math("MULTIPLY", depth, -1.0, (2150, -600)), off.inputs["Scale"])
    setp = b.node_with_props("GeometryNodeSetPosition", (2300, 100))
    L(geo, setp.inputs["Geometry"])
    L(off.outputs["Vector"], setp.inputs["Offset"])

    # 5. rejoin with the untouched interior and weld the seam
    rejoin(b, setp.outputs["Geometry"], sep, go, 2450, 1e-5)
    return ng


def _or_up_facing(b, selected):
    """Add faces whose normal points up (Z > 0.9) to a face selection."""
    nrm = b.node_with_props("GeometryNodeInputNormal", (-350, -500))
    sepz = b.node_with_props("ShaderNodeSeparateXYZ", (-200, -500))
    b.link(nrm.outputs["Normal"], sepz.inputs["Vector"])
    up = b.node_with_props("FunctionNodeCompare", (-50, -500), data_type="FLOAT", operation="GREATER_THAN")
    b.link(sepz.outputs["Z"], active_socket(up.inputs, "A"))
    active_socket(up.inputs, "B").default_value = 0.9
    either = b.node_with_props("FunctionNodeBooleanMath", (120, -400), operation="OR")
    b.link(selected, either.inputs[0])
    b.link(up.outputs[0], either.inputs[1])
    return either.outputs[0]


def _grain_breaks(b, gi, rp, grain_stretch):
    """Break depth: sparse patches on top faces x an outline stretched along the grain x fibres."""
    nrm = b.node_with_props("GeometryNodeInputNormal", (650, -1150))
    sepn = b.node_with_props("ShaderNodeSeparateXYZ", (800, -1150))
    b.link(nrm.outputs["Normal"], sepn.inputs["Vector"])
    top = b.map_range(sepn.outputs["Z"], 0.85, 0.95, (1000, -1150))
    ts = b.math("ADD", b.math("MULTIPLY", b.math("SUBTRACT", 0.5, gi.outputs["Break Share"],
                                                 (500, -1300)), 0.35, (650, -1300)), 0.58, (750, -1300))
    sparse = b.map_range(b.noise_texture(rp, 3.0, (650, -1450), detail=2), ts,
                     b.math("ADD", ts, 0.04, (850, -1400)), (1000, -1450))
    stretch = b.node_with_props("ShaderNodeVectorMath", (650, -1650), operation="MULTIPLY")
    b.link(rp, stretch.inputs[0])
    stretch.inputs[1].default_value = grain_stretch
    outline = b.map_range(b.noise_texture(stretch.outputs["Vector"], 1.0, (800, -1650), detail=7, rough=0.72),
                      0.52, 0.545, (1000, -1650))
    fib_v = b.node_with_props("ShaderNodeVectorMath", (650, -1850), operation="MULTIPLY")
    b.link(rp, fib_v.inputs[0])
    fib_v.inputs[1].default_value = (grain_stretch[0] * 14, grain_stretch[1] * 3, grain_stretch[2] * 14)
    fibres = b.map_range(b.noise_texture(fib_v.outputs["Vector"], 1.0, (800, -1850), detail=3), 0.3, 0.7,
                     (1000, -1850), 0.55, 1.0)
    brk = b.math("MULTIPLY", b.math("MULTIPLY", top, sparse, (1200, -1300)), outline, (1380, -1400))
    return b.math("MULTIPLY", b.math("MULTIPLY", brk, fibres, (1550, -1500)),
                  gi.outputs["Break Depth"], (1720, -1500))


def set_input(mod, name, value):
    """A Geometry Nodes modifier's own input values live at
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

# Pale exposed substrate is rougher in the first scan; green substrate is smoother in the second.
WORN_SCAN_LEVELS={'tmulfghdy':('Roughness',.80,.85,False),
                  'ub1meemn':('Roughness',.65,.72,True)}


def flaked_paint_masks(asset_ids=tuple(WORN_SCAN_LEVELS),project=None):
    """Resolve per-scan Roughness polarity: white is exposed substrate, black is intact paint."""
    result=[]
    for asset_id in asset_ids:
        map_name,black,white,invert=WORN_SCAN_LEVELS[asset_id]
        mask=asset_mask(asset_id,map_name,project)
        result.append(replace(mask,black=black,white=white,invert=invert) if mask is not None else None)
    return result



def chipping_field(g, vector, scale_m, frame=None):
    """Return the unchanged smooth procedural coating-loss patches."""
    noise = g.noise_texture(vector, 1 / scale_m, (-1800, 0), frame, detail=3)
    return g.map_range(noise, .54, .57, (-1500, 0), frame=frame, smooth=True)
