"""Terrain graph; implementation for terrain."""
import bpy
from materials.shared.node_graph import NodeGraph


BARE_SOIL_NOISE_W = 11.0                   # 4D-noise W shared by the meadow's bare-soil mask and the ground shader


BARE_SOIL_NOISE_SETTINGS = (0.35, 0.62, 0.69)       # that noise: scale (1/m), full sward below, bare soil above


def _sock(ng, name, typ, io="INPUT", default=None):
    s = ng.interface.new_socket(name, in_out=io, socket_type=typ)
    if default is not None:
        s.default_value = default
    return s


def _noise4(graph, vec, scale, w, location, detail=2.0, rough=0.5):
    n = graph.node_with_props("ShaderNodeTexNoise", location, noise_dimensions="4D")      # W exists only on a 4D noise
    for k, v in (("Scale", scale), ("W", w), ("Detail", detail), ("Roughness", rough)):
        n.inputs[k].default_value = v
    graph.link(vec, n.inputs["Vector"])
    return n.outputs[0]


def _centred(graph, v, amp, location):
    """(noise - 0.5) * amp."""
    return graph.math("MULTIPLY", graph.math("SUBTRACT", v, 0.5, location), amp, (location[0] + 150, location[1]))


def pad_distance(graph, centre, pad_half_size_m, location=(-1200, -400)):
    """Signed plan distance from a rectangle (negative inside): returns (distance, position)."""
    x, y = location
    pos = graph.node_with_props("GeometryNodeInputPosition", (x, y)).outputs[0]
    rel = graph.node_with_props("ShaderNodeVectorMath", (x + 150, y), operation="SUBTRACT")
    graph.link(pos, rel.inputs[0]); rel.inputs[1].default_value = (centre[0], centre[1], 0.0)
    flat = graph.node_with_props("ShaderNodeVectorMath", (x + 300, y), operation="MULTIPLY")
    graph.link(rel.outputs[0], flat.inputs[0]); flat.inputs[1].default_value = (1.0, 1.0, 0.0)
    ab = graph.node_with_props("ShaderNodeVectorMath", (x + 450, y), operation="ABSOLUTE"); graph.link(flat.outputs[0], ab.inputs[0])
    q = graph.node_with_props("ShaderNodeVectorMath", (x + 600, y), operation="SUBTRACT")
    graph.link(ab.outputs[0], q.inputs[0]); q.inputs[1].default_value = (pad_half_size_m[0], pad_half_size_m[1], 0.0)
    mx = graph.node_with_props("ShaderNodeVectorMath", (x + 750, y), operation="MAXIMUM")
    graph.link(q.outputs[0], mx.inputs[0]); mx.inputs[1].default_value = (0.0, 0.0, -1e9)
    ln = graph.node_with_props("ShaderNodeVectorMath", (x + 900, y), operation="LENGTH"); graph.link(mx.outputs[0], ln.inputs[0])
    sep = graph.node_with_props("ShaderNodeSeparateXYZ", (x + 750, y - 200)); graph.link(q.outputs[0], sep.inputs[0])
    inside = graph.math("MINIMUM", graph.math("MAXIMUM", sep.outputs[0], sep.outputs[1], (x + 900, y - 200)), 0.0, (x + 1050, y - 200))
    return graph.math("ADD", ln.outputs["Value"], inside, (x + 1200, y - 100)), pos


def landform_group(name="LANDFORM", centre=(0.0, 0.0), pad_half_size_m=(4.0, 4.0), size=300.0, vertex_count=601,
                   pad_height_m=-0.03, crest_distance_m=1.5, fall_height_m=6.0, slope_run_m=40.0, warp=7.0, roll=2.5, hummock=0.12):
    """GN group: grid -> hill around a pad (landform grading), stores `pad_d`; plan metres."""
    ng = bpy.data.node_groups.get(name)
    if ng:
        bpy.data.node_groups.remove(ng)
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.is_modifier = True
    _sock(ng, "Geometry", "NodeSocketGeometry", "INPUT")
    _sock(ng, "Geometry", "NodeSocketGeometry", "OUTPUT")
    mat_s = _sock(ng, "Material", "NodeSocketMaterial")
    g = NodeGraph(ng, clear=True)
    gi = g.node_with_props("NodeGroupInput", (-1500, 300)); go = g.node_with_props("NodeGroupOutput", (2600, 0))
    grid = g.node_with_props("GeometryNodeMeshGrid", (-1300, 300))
    for k, v in (("Size X", size), ("Size Y", size), ("Vertices X", vertex_count), ("Vertices Y", vertex_count)):
        grid.inputs[k].default_value = v
    move = g.node_with_props("GeometryNodeTransform", (-1100, 300)); move.inputs["Translation"].default_value = (*centre, 0)
    g.link(grid.outputs["Mesh"], move.inputs["Geometry"])
    d, pos = pad_distance(g, centre, pad_half_size_m)
    warp_f = g.math("MULTIPLY", _centred(g, _noise4(g, pos, 0.025, 1.3, (0, -700)), warp * 2, (200, -700)),
                    g.map_range(d, 0.0, 12.0, (200, -850), smooth=True), (500, -750))
    dw = g.math("ADD", d, warp_f, (650, -600))
    fall_f = g.math("MULTIPLY", g.map_range(dw, crest_distance_m, crest_distance_m + slope_run_m, (800, -600), smooth=True), -fall_height_m, (950, -600))
    roll_f = g.math("MULTIPLY", _centred(g, _noise4(g, pos, 0.012, 7.1, (0, -1000)), roll * 2, (200, -1000)),
                    g.map_range(d, 6.0, 30.0, (200, -1150), smooth=True), (500, -1050))
    hum_f = g.math("MULTIPLY", _centred(g, _noise4(g, pos, 0.6, 3.7, (0, -1300), 4.0, 0.55), hummock * 2, (200, -1300)),
                   g.map_range(d, 0.5, 3.0, (200, -1450), smooth=True), (500, -1350))
    z = g.math("ADD", g.math("ADD", fall_f, roll_f, (1100, -700)), g.math("ADD", hum_f, pad_height_m, (1100, -900)), (1250, -800))
    comb = g.node_with_props("ShaderNodeCombineXYZ", (1400, -800)); g.link(z, comb.inputs["Z"])
    setp = g.node_with_props("GeometryNodeSetPosition", (1550, 300))
    g.link(move.outputs[0], setp.inputs["Geometry"]); g.link(comb.outputs[0], setp.inputs["Offset"])
    geo = g.store_attribute(setp.outputs[0], "pad_d", "FLOAT", d, (1750, 300))
    smooth = g.node_with_props("GeometryNodeSetShadeSmooth", (1950, 300)); g.link(geo, smooth.inputs["Geometry"])
    sm = g.node_with_props("GeometryNodeSetMaterial", (2150, 300))
    g.link(smooth.outputs[0], sm.inputs["Geometry"]); g.link(gi.outputs["Material"], sm.inputs["Material"])
    g.link(sm.outputs[0], go.inputs[0])
    ng["params"] = dict(centre=list(centre), pad_half_size_m=list(pad_half_size_m), pad_height_m=pad_height_m,
                        crest_distance_m=crest_distance_m, fall_height_m=fall_height_m, slope_run_m=slope_run_m)
    return ng
