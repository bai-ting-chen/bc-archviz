"""Meadow graph; implementation for scatter."""
import math
import bpy


def meadow_layer_group(scatter_ng, name="MEADOW_LAYER", bare=None):
    """GN group: Scatter on Surface on a terrain object, masked by species patch noise, shared bare-soil noise, pad clearance and the camera frustum. Reused if it exists (layers point at it)."""
    from materials.shared.nodes import G
    from scene.environment.terrain import BARE_W
    ng = bpy.data.node_groups.get(name)
    if ng:
        return ng
    from scene.environment.terrain import BARE
    bare = bare or BARE
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.is_modifier = True
    it = ng.interface
    it.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    it.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    for nm, typ, dv in (("Terrain", "NodeSocketObject", None), ("Collection", "NodeSocketCollection", None),
                        ("Camera", "NodeSocketObject", None), ("Density", "NodeSocketFloat", 1.0),
                        ("Seed", "NodeSocketInt", 0), ("Patch Scale", "NodeSocketFloat", 0.2),
                        ("Patch Low", "NodeSocketFloat", -1.0), ("Patch High", "NodeSocketFloat", -0.5),
                        ("Use Bare", "NodeSocketBool", True), ("Bare Scale", "NodeSocketFloat", bare[0]),
                        ("Bare Low", "NodeSocketFloat", bare[1]), ("Bare High", "NodeSocketFloat", bare[2]),
                        ("Pad Clear", "NodeSocketFloat", 0.08), ("Scale", "NodeSocketFloat", 1.0),
                        ("Scale Random", "NodeSocketFloat", 0.3), ("Sink", "NodeSocketFloat", 0.01),
                        ("Tan X", "NodeSocketFloat", 0.5), ("Tan Y", "NodeSocketFloat", 0.6),
                        ("Max Distance", "NodeSocketFloat", 150.0), ("Viewport Fraction", "NodeSocketFloat", 0.05)):
        s_ = it.new_socket(nm, in_out="INPUT", socket_type=typ)
        if dv is not None:
            s_.default_value = dv
    g = G(ng, clear=True)
    gi = g.n("NodeGroupInput", (-1600, 0))
    go = g.n("NodeGroupOutput", (1600, 0))
    I = gi.outputs
    oi = g.n("GeometryNodeObjectInfo", (-1300, 300), transform_space="RELATIVE")
    g.link(I["Terrain"], oi.inputs["Object"])
    pos = g.n("GeometryNodeInputPosition", (-1300, -100)).outputs[0]
    # species patches: noise low..high -> 0..1 (Patch Low < 0 = everywhere)
    pn = g.n("ShaderNodeTexNoise", (-1100, -100), noise_dimensions="4D")
    pn.inputs["Detail"].default_value = 3.0
    g.link(pos, pn.inputs["Vector"]); g.link(I["Patch Scale"], pn.inputs["Scale"])
    g.link(g.math("MULTIPLY", I["Seed"], 1.618, (-1300, -250)), pn.inputs["W"])
    pm = g.n("ShaderNodeMapRange", (-900, -100), interpolation_type="SMOOTHSTEP")
    g.link(pn.outputs[0], pm.inputs["Value"]); g.link(I["Patch Low"], pm.inputs["From Min"])
    g.link(I["Patch High"], pm.inputs["From Max"])
    # bare soil: shared noise (materials.ground.ground.ground_material uses the same) thins the sward to nothing
    bn = g.n("ShaderNodeTexNoise", (-1100, -400), noise_dimensions="4D")
    bn.inputs["Detail"].default_value = 4.0
    bn.inputs["W"].default_value = BARE_W
    g.link(pos, bn.inputs["Vector"]); g.link(I["Bare Scale"], bn.inputs["Scale"])
    bm = g.n("ShaderNodeMapRange", (-900, -400), interpolation_type="SMOOTHSTEP")
    bm.inputs["To Min"].default_value, bm.inputs["To Max"].default_value = 1.0, 0.0
    g.link(bn.outputs[0], bm.inputs["Value"]); g.link(I["Bare Low"], bm.inputs["From Min"])
    g.link(I["Bare High"], bm.inputs["From Max"])
    bsw = g.n("GeometryNodeSwitch", (-700, -400), input_type="FLOAT")
    bsw.inputs["False"].default_value = 1.0
    g.link(I["Use Bare"], bsw.inputs["Switch"]); g.link(bm.outputs["Result"], bsw.inputs["True"])
    # pad clearance
    pad = g.named("pad_d", "FLOAT", (-1100, -700))
    pc = g.n("ShaderNodeMapRange", (-900, -700))
    g.link(pad, pc.inputs["Value"]); g.link(I["Pad Clear"], pc.inputs["From Min"])
    g.link(g.math("ADD", I["Pad Clear"], 0.3, (-1100, -850)), pc.inputs["From Max"])
    # camera frustum + distance: only what the camera can see is scattered
    ci = g.n("GeometryNodeObjectInfo", (-1300, -1000), transform_space="ORIGINAL")
    g.link(I["Camera"], ci.inputs["Object"])
    inv = g.n("FunctionNodeInvertMatrix", (-1100, -1000)); g.link(ci.outputs["Transform"], inv.inputs[0])
    tp = g.n("FunctionNodeTransformPoint", (-900, -1000))
    g.link(pos, tp.inputs["Vector"]); g.link(inv.outputs[0], tp.inputs["Transform"])
    cs = g.n("ShaderNodeSeparateXYZ", (-700, -1000)); g.link(tp.outputs[0], cs.inputs[0])
    depth = g.math("MAXIMUM", g.math("MULTIPLY", cs.outputs["Z"], -1.0, (-550, -1100)), 0.001, (-400, -1100))
    inx = g.math("LESS_THAN", g.math("ABSOLUTE", g.math("DIVIDE", cs.outputs["X"], depth, (-250, -950)), 0.0, (-100, -950)),
                 I["Tan X"], (50, -950))
    iny = g.math("LESS_THAN", g.math("ABSOLUTE", g.math("DIVIDE", cs.outputs["Y"], depth, (-250, -1050)), 0.0, (-100, -1050)),
                 I["Tan Y"], (50, -1050))
    ln = g.n("ShaderNodeVectorMath", (-550, -1250), operation="LENGTH"); g.link(tp.outputs[0], ln.inputs[0])
    near = g.math("LESS_THAN", ln.outputs["Value"], I["Max Distance"], (-400, -1250))
    front = g.math("GREATER_THAN", g.math("MULTIPLY", cs.outputs["Z"], -1.0, (-400, -1350)), 0.0, (-250, -1350))
    fr = g.math("MULTIPLY", g.math("MULTIPLY", inx, iny, (200, -1000)), g.math("MULTIPLY", near, front, (200, -1300)), (350, -1150))
    mask = g.math("MULTIPLY", g.math("MULTIPLY", pm.outputs["Result"], bsw.outputs[0], (400, -300)),
                  g.math("MULTIPLY", pc.outputs["Result"], fr, (400, -800)), (550, -500))
    sc = g.n("GeometryNodeGroup", (800, 0))
    sc.node_tree = scatter_ng
    S = sc.inputs
    g.link(oi.outputs["Geometry"], S["Mesh"]); g.link(I["Density"], S["Density"]); g.link(mask, S["Distribution Mask"])
    S["Keep Surface"].default_value = False
    g.link(I["Seed"], S["Seed"]); g.link(I["Seed"], S["Instance Seed"]); g.link(I["Seed"], S["Randomize Seed"])
    S["Input Type"].default_value = "Data-Block"
    S["Instance Type"].default_value = "Collection"
    g.link(I["Collection"], S["Collection"])
    S["Pick Instance"].default_value = True
    g.link(g.math("MULTIPLY", I["Sink"], -1.0, (600, -200)), S["Surface Offset"])
    S["Align Rotation"].default_value = False            # grass grows up, not along the slope normal
    sv = g.n("ShaderNodeCombineXYZ", (600, -350))
    for k in "XYZ":
        g.link(I["Scale"], sv.inputs[k])
    g.link(sv.outputs[0], S["Scale"])
    S["Randomize"].default_value = True
    S["Randomize Rotation"].default_value = (0.08, 0.08, 2 * math.pi)   # slight lean, any heading
    g.link(I["Scale Random"], [x for x in S if x.name == "Randomize Scale" and x.type == "VALUE"][0])
    g.link(I["Viewport Fraction"], S["Viewport Visibility"])
    g.link(sc.outputs[0], go.inputs[0])
    return ng
