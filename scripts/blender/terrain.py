"""Topography around a building pad, and the ground under a meadow (run in Blender).

    import terrain
    topo = terrain.landform_group(centre=(25, 25), pad_half=(3.5, 4), fall=6, run=40)
    ter = terrain.add_terrain(topo, materials.ground.ground_material("grass_ground", "forest_ground_05"))
    terrain.height(x, y, centre=..., pad_half=..., fall=..., run=...)   # no-noise twin (camera placing)

Landform grading (references/materials/README.md › Terrain): a flat pad just under the slab, an apron, then a fall
of `fall` m over `run` m as a smoothstep in the noise-warped distance from the pad - a rounded
crest *and* a rounded toe, contours that wander instead of a cone - plus a broad roll beyond and
pasture hummocks. Steepest slope = 1.5 * fall / run (keep < 0.25 = 4:1 for a gentle, mowable
hill). The group stores `pad_d` (signed plan distance to the pad, m) for scatter masks.
"""
import math

import bpy

from materials.nodes import G
from materials.nodes import sock

BARE_W = 11.0                   # 4D-noise W shared by the meadow's bare-soil mask and the ground shader
BARE = (0.35, 0.62, 0.69)       # that noise: scale (1/m), full sward below, bare soil above


def _sock(ng, name, typ, io="INPUT", default=None):
    s = ng.interface.new_socket(name, in_out=io, socket_type=typ)
    if default is not None:
        s.default_value = default
    return s


def _noise4(g, vec, scale, w, loc, detail=2.0, rough=0.5):
    n = g.n("ShaderNodeTexNoise", loc, noise_dimensions="4D")      # W exists only on a 4D noise
    for k, v in (("Scale", scale), ("W", w), ("Detail", detail), ("Roughness", rough)):
        n.inputs[k].default_value = v
    g.link(vec, n.inputs["Vector"])
    return n.outputs[0]


def _centred(g, v, amp, loc):
    """(noise - 0.5) * amp."""
    return g.math("MULTIPLY", g.math("SUBTRACT", v, 0.5, loc), amp, (loc[0] + 150, loc[1]))


def pad_distance(g, centre, pad_half, loc=(-1200, -400)):
    """Signed plan distance from a rectangle (negative inside): returns (distance, position)."""
    x, y = loc
    pos = g.n("GeometryNodeInputPosition", (x, y)).outputs[0]
    rel = g.n("ShaderNodeVectorMath", (x + 150, y), operation="SUBTRACT")
    g.link(pos, rel.inputs[0]); rel.inputs[1].default_value = (centre[0], centre[1], 0.0)
    flat = g.n("ShaderNodeVectorMath", (x + 300, y), operation="MULTIPLY")
    g.link(rel.outputs[0], flat.inputs[0]); flat.inputs[1].default_value = (1.0, 1.0, 0.0)
    ab = g.n("ShaderNodeVectorMath", (x + 450, y), operation="ABSOLUTE"); g.link(flat.outputs[0], ab.inputs[0])
    q = g.n("ShaderNodeVectorMath", (x + 600, y), operation="SUBTRACT")
    g.link(ab.outputs[0], q.inputs[0]); q.inputs[1].default_value = (pad_half[0], pad_half[1], 0.0)
    mx = g.n("ShaderNodeVectorMath", (x + 750, y), operation="MAXIMUM")
    g.link(q.outputs[0], mx.inputs[0]); mx.inputs[1].default_value = (0.0, 0.0, -1e9)
    ln = g.n("ShaderNodeVectorMath", (x + 900, y), operation="LENGTH"); g.link(mx.outputs[0], ln.inputs[0])
    sep = g.n("ShaderNodeSeparateXYZ", (x + 750, y - 200)); g.link(q.outputs[0], sep.inputs[0])
    inside = g.math("MINIMUM", g.math("MAXIMUM", sep.outputs[0], sep.outputs[1], (x + 900, y - 200)), 0.0, (x + 1050, y - 200))
    return g.math("ADD", ln.outputs["Value"], inside, (x + 1200, y - 100)), pos


def landform_group(name="LANDFORM", centre=(0.0, 0.0), pad_half=(4.0, 4.0), size=300.0, verts=601,
                   pad_z=-0.03, crest=1.5, fall=6.0, run=40.0, warp=7.0, roll=2.5, hummock=0.12):
    """GN group: grid -> hill around a pad (landform grading), stores `pad_d`; plan metres."""
    ng = bpy.data.node_groups.get(name)
    if ng:
        bpy.data.node_groups.remove(ng)
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.is_modifier = True
    _sock(ng, "Geometry", "NodeSocketGeometry", "INPUT")
    _sock(ng, "Geometry", "NodeSocketGeometry", "OUTPUT")
    mat_s = _sock(ng, "Material", "NodeSocketMaterial")
    g = G(ng, clear=True)
    gi = g.n("NodeGroupInput", (-1500, 300)); go = g.n("NodeGroupOutput", (2600, 0))
    grid = g.n("GeometryNodeMeshGrid", (-1300, 300))
    for k, v in (("Size X", size), ("Size Y", size), ("Vertices X", verts), ("Vertices Y", verts)):
        grid.inputs[k].default_value = v
    move = g.n("GeometryNodeTransform", (-1100, 300)); move.inputs["Translation"].default_value = (*centre, 0)
    g.link(grid.outputs["Mesh"], move.inputs["Geometry"])
    d, pos = pad_distance(g, centre, pad_half)
    warp_f = g.math("MULTIPLY", _centred(g, _noise4(g, pos, 0.025, 1.3, (0, -700)), warp * 2, (200, -700)),
                    g.range(d, 0.0, 12.0, (200, -850), smooth=True), (500, -750))
    dw = g.math("ADD", d, warp_f, (650, -600))
    fall_f = g.math("MULTIPLY", g.range(dw, crest, crest + run, (800, -600), smooth=True), -fall, (950, -600))
    roll_f = g.math("MULTIPLY", _centred(g, _noise4(g, pos, 0.012, 7.1, (0, -1000)), roll * 2, (200, -1000)),
                    g.range(d, 6.0, 30.0, (200, -1150), smooth=True), (500, -1050))
    hum_f = g.math("MULTIPLY", _centred(g, _noise4(g, pos, 0.6, 3.7, (0, -1300), 4.0, 0.55), hummock * 2, (200, -1300)),
                   g.range(d, 0.5, 3.0, (200, -1450), smooth=True), (500, -1350))
    z = g.math("ADD", g.math("ADD", fall_f, roll_f, (1100, -700)), g.math("ADD", hum_f, pad_z, (1100, -900)), (1250, -800))
    comb = g.n("ShaderNodeCombineXYZ", (1400, -800)); g.link(z, comb.inputs["Z"])
    setp = g.n("GeometryNodeSetPosition", (1550, 300))
    g.link(move.outputs[0], setp.inputs["Geometry"]); g.link(comb.outputs[0], setp.inputs["Offset"])
    geo = g.store(setp.outputs[0], "pad_d", "FLOAT", d, (1750, 300))
    smooth = g.n("GeometryNodeSetShadeSmooth", (1950, 300)); g.link(geo, smooth.inputs["Geometry"])
    sm = g.n("GeometryNodeSetMaterial", (2150, 300))
    g.link(smooth.outputs[0], sm.inputs["Geometry"]); g.link(gi.outputs["Material"], sm.inputs["Material"])
    g.link(sm.outputs[0], go.inputs[0])
    ng["params"] = dict(centre=list(centre), pad_half=list(pad_half), pad_z=pad_z, crest=crest, fall=fall, run=run)
    return ng


def height(x, y, centre, pad_half, pad_z=-0.03, crest=1.5, fall=6.0, run=40.0):
    """Python twin of landform_group without the noise terms (e.g. to set a camera's eye height)."""
    qx = abs(x - centre[0]) - pad_half[0]
    qy = abs(y - centre[1]) - pad_half[1]
    d = math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0)
    t = min(max((d - crest) / run, 0), 1)
    return pad_z - fall * t * t * (3 - 2 * t)


def add_terrain(group, material, name="TERRAIN", collection=None):
    """An empty mesh object carrying the landform modifier (the GN group makes the geometry)."""
    from materials.edge_wear import set_input
    ob = bpy.data.objects.new(name, bpy.data.meshes.new(name))
    (collection or bpy.context.scene.collection).objects.link(ob)
    mod = ob.modifiers.new("LANDFORM", "NODES"); mod.node_group = group
    set_input(mod, "Material", material)
    return ob
