"""Wood damage; canonical implementation behind wood_wear."""

import math

import bpy

from materials.shared.nodes import sock

from effects.edge_wear import _GN

from effects.edge_chips import input_socket as _input

from effects.edge_chips import edge_field as _edge_field

from effects.edge_chips import chip_field as _chip_field

from effects.edge_chips import rejoin as _rejoin

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
    _input(ng, "Seed", "NodeSocketVector", seed)
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    b = _GN(ng)
    L = b.L
    gi = b.n("NodeGroupInput", (-1600, 0))
    go = b.n("NodeGroupOutput", (3000, 0))

    # 1. edge field
    g = _edge_field(b, gi, -1600)

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
    chip, prof = _chip_field(b, gi, rp, dd, 6.0, 70.0, 0.0006, 0.4)
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
    _rejoin(b, setp.outputs["Geometry"], sep, go, 2700, 1e-6)
    return ng
