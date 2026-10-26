"""Caustic graph; implementation for gn_caustics."""
import bpy
from effects.edge_wear import _GN
from effects.edge_wear import _input
from materials.shared.nodes import sock


def caustic_sheet_group(name="Wavefront Caustics"):
    """GN group: refract water vertices, raycast to receivers and sun, store E = E_sun T A_perp / A_landed."""
    ng = bpy.data.node_groups.get(name)
    if ng:
        bpy.data.node_groups.remove(ng)
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    for nm, kind in (("Caster", "NodeSocketObject"), ("Receivers", "NodeSocketCollection"),
                     ("Occluders", "NodeSocketCollection")):
        ng.interface.new_socket(nm, in_out="INPUT", socket_type=kind)
    _input(ng, "Sun Direction", "NodeSocketVector", (0.0, 0.0, 1.0))
    _input(ng, "Sun Irradiance", "NodeSocketFloat", 100.0)
    _input(ng, "IOR Ratio", "NodeSocketFloat", 1 / 1.333)
    _input(ng, "Transmission", "NodeSocketFloat", 0.976)
    _input(ng, "Lift", "NodeSocketFloat", 0.001, "DISTANCE")
    _input(ng, "Sun Blur Iterations", "NodeSocketInt", 2)
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    b = _GN(ng)
    L = b.L
    gi = b.n("NodeGroupInput", (-1800, 0))
    go = b.n("NodeGroupOutput", (2600, 0))

    oi = b.n("GeometryNodeObjectInfo", (-1600, 200), transform_space="RELATIVE")
    L(gi.outputs["Caster"], oi.inputs["Object"])
    rcv = b.n("GeometryNodeCollectionInfo", (-1600, -300), transform_space="RELATIVE")
    L(gi.outputs["Receivers"], rcv.inputs["Collection"])
    rcv_r = b.n("GeometryNodeRealizeInstances", (-1400, -300))
    L(rcv.outputs[0], rcv_r.inputs[0])
    occ = b.n("GeometryNodeCollectionInfo", (-1600, -550), transform_space="RELATIVE")
    L(gi.outputs["Occluders"], occ.inputs["Collection"])
    occ_r = b.n("GeometryNodeRealizeInstances", (-1400, -550))
    L(occ.outputs[0], occ_r.inputs[0])

    S = b.n("ShaderNodeVectorMath", (-1400, -800), operation="NORMALIZE")
    L(gi.outputs["Sun Direction"], S.inputs[0])
    S = S.outputs["Vector"]
    inc = b.n("ShaderNodeVectorMath", (-1200, -800), operation="SCALE")
    L(S, inc.inputs[0]); inc.inputs["Scale"].default_value = -1.0
    nrm = b.n("GeometryNodeInputNormal", (-1200, -950))
    rf = b.n("ShaderNodeVectorMath", (-1000, -850), operation="REFRACT")
    L(inc.outputs["Vector"], rf.inputs[0]); L(nrm.outputs["Normal"], rf.inputs[1])
    L(gi.outputs["IOR Ratio"], rf.inputs["Scale"])
    R = b.n("ShaderNodeVectorMath", (-850, -850), operation="NORMALIZE")
    L(rf.outputs["Vector"], R.inputs[0])
    R = R.outputs["Vector"]
    pos = b.n("GeometryNodeInputPosition", (-1000, -1100))
    eps = b.n("ShaderNodeVectorMath", (-850, -1050), operation="MULTIPLY_ADD")
    L(R, eps.inputs[0]); eps.inputs[1].default_value = (1e-4, 1e-4, 1e-4); L(pos.outputs["Position"], eps.inputs[2])

    # 1. per face: the sun power that crosses it (before moving anything)
    fa0 = b.n("GeometryNodeInputMeshFaceArea", (-1000, 450))
    fn = b.n("GeometryNodeInputNormal", (-1000, 300))
    dot = b.n("ShaderNodeVectorMath", (-850, 350), operation="DOT_PRODUCT")
    L(fn.outputs["Normal"], dot.inputs[0]); L(S, dot.inputs[1])
    adot = b.math("ABSOLUTE", dot.outputs["Value"], 0.0, (-700, 350))
    aperp = b.math("MULTIPLY", fa0.outputs["Area"], adot, (-550, 400))
    cap = b.n("GeometryNodeCaptureAttribute", (-350, 200), domain="FACE")
    cap.capture_items.new("FLOAT", "A_perp")
    L(oi.outputs["Geometry"], cap.inputs["Geometry"])
    L(aperp, cap.inputs["A_perp"])   # by name: index 1 is the new Selection socket in 5.2

    # 2. where each wavefront vertex lands, and whether the sun reaches it at all
    rc = b.n("GeometryNodeRaycast", (-600, -500))
    L(rcv_r.outputs[0], rc.inputs["Target Geometry"]); L(eps.outputs["Vector"], rc.inputs["Source Position"])
    L(R, rc.inputs["Ray Direction"]); rc.inputs["Ray Length"].default_value = 10.0
    sh_src = b.n("ShaderNodeVectorMath", (-850, -1250), operation="MULTIPLY_ADD")
    L(S, sh_src.inputs[0]); sh_src.inputs[1].default_value = (1e-3, 1e-3, 1e-3); L(pos.outputs["Position"], sh_src.inputs[2])
    sh = b.n("GeometryNodeRaycast", (-600, -1100))
    L(occ_r.outputs[0], sh.inputs["Target Geometry"]); L(sh_src.outputs["Vector"], sh.inputs["Source Position"])
    L(S, sh.inputs["Ray Direction"]); sh.inputs["Ray Length"].default_value = 50.0
    lit = b.n("FunctionNodeBooleanMath", (-400, -1000), operation="NIMPLY")   # hit AND NOT shadowed
    L(rc.outputs["Is Hit"], lit.inputs[0]); L(sh.outputs["Is Hit"], lit.inputs[1])
    hn = b.n("ShaderNodeSeparateXYZ", (-400, -700))
    L(rc.outputs["Hit Normal"], hn.inputs[0])
    onfl = b.n("FunctionNodeCompare", (-250, -700), data_type="FLOAT", operation="GREATER_THAN")
    L(hn.outputs["Z"], sock(onfl.inputs, "A")); sock(onfl.inputs, "B").default_value = 0.5
    g = b.store(cap.outputs["Geometry"], "lit", "FLOAT", lit.outputs[0], (-100, 200))
    g = b.store(g, "onfloor", "FLOAT", onfl.outputs[0], (100, 200))
    land = b.n("ShaderNodeVectorMath", (-250, -450), operation="MULTIPLY_ADD")
    L(rc.outputs["Hit Normal"], land.inputs[0]); L(gi.outputs["Lift"], land.inputs[1])
    L(rc.outputs["Hit Position"], land.inputs[2])
    setp = b.n("GeometryNodeSetPosition", (300, 200))
    L(g, setp.inputs["Geometry"]); L(land.outputs["Vector"], setp.inputs["Position"])

    # 3. irradiance per landed face; drop faces that straddle floor/wall or left the pool
    fa1 = b.n("GeometryNodeInputMeshFaceArea", (300, -200))
    adst = b.math("MAXIMUM", fa1.outputs["Area"], 1e-10, (450, -200))
    pw = b.math("MULTIPLY", b.math("MULTIPLY", cap.outputs["A_perp"], gi.outputs["Sun Irradiance"], (450, -50)),
                gi.outputs["Transmission"], (600, -50))
    E = b.math("DIVIDE", pw, adst, (750, -100))
    litf = b.named("lit", "FLOAT", (600, -350))
    E = b.math("MULTIPLY", E, litf, (900, -150))
    E = b.math("MINIMUM", E, b.math("MULTIPLY", gi.outputs["Sun Irradiance"], 400.0, (900, -300)), (1050, -150))
    # sun-disc softening: a 0.53 deg sun blurs the caustic by ~depth * 0.0093 (~1.2 cm at 1.3 m);
    # Blur Attribute over the sheet's ~1 cm vertex spacing approximates that kernel
    blur = b.n("GeometryNodeBlurAttribute", (1100, -350), data_type="FLOAT")
    blur.label = "sun disc blur"
    L(E, blur.inputs["Value"])
    L(gi.outputs["Sun Blur Iterations"], blur.inputs["Iterations"])
    E = blur.outputs["Value"]
    # stored per POINT: face values average onto vertices, so brightness is smooth across the
    # sheet instead of stepping triangle to triangle (the "fingerprint" lines of per-face E)
    g = b.store(setp.outputs["Geometry"], "E", "FLOAT", E, (1250, 200))
    fl = b.named("onfloor", "FLOAT", (1250, -300))
    straddle = b.n("FunctionNodeCompare", (1450, -300), data_type="FLOAT", operation="NOT_EQUAL")
    L(fl, sock(straddle.inputs, "A")); sock(straddle.inputs, "B").default_value = 0.0
    straddle.inputs["Epsilon"].default_value = 0.0
    edge = b.n("FunctionNodeBooleanMath", (1600, -350), operation="AND")
    hi = b.n("FunctionNodeCompare", (1450, -450), data_type="FLOAT", operation="LESS_THAN")
    L(fl, sock(hi.inputs, "A")); sock(hi.inputs, "B").default_value = 0.999
    L(straddle.outputs[0], edge.inputs[0]); L(hi.outputs[0], edge.inputs[1])
    lt = b.n("FunctionNodeCompare", (1450, -600), data_type="FLOAT", operation="LESS_THAN")
    L(b.named("lit", "FLOAT", (1250, -600)), sock(lt.inputs, "A")); sock(lt.inputs, "B").default_value = 0.001
    drop = b.n("FunctionNodeBooleanMath", (1750, -450), operation="OR")
    L(edge.outputs[0], drop.inputs[0]); L(lt.outputs[0], drop.inputs[1])
    dele = b.n("GeometryNodeDeleteGeometry", (1950, 200), domain="FACE")
    L(g, dele.inputs["Geometry"]); L(drop.outputs[0], dele.inputs["Selection"])
    # Object Info geometry keeps the CASTER's material (the water glass!) -- override it
    setm = b.n("GeometryNodeSetMaterial", (2150, 200))
    setm.label = "caustic sheet material"
    L(dele.outputs["Geometry"], setm.inputs["Geometry"])
    L(setm.outputs["Geometry"], go.inputs["Geometry"])
    return ng
