"""Runoff: vertical streaks below drip edges, grunge patches and soil splash, all into the grime mask.

Needs the leak field (leak_field.add_leak_field) on the object. Works on a weathered_concrete material.
"""
from materials.shared.node_graph import frame_for

RUNOFF_DEFAULTS = dict(streak_frequency_per_m=14.0, streak_vertical_frequency_per_m=0.6, length_range_m=(0.8, 3.2), top_band=0.2, top=0.9, amount=1.0,
            streak_band=(0.42, 0.58), presence=(0.28, 0.5), fade_pow=1.15)


def add_runoff(mat, leak=None, grunge=(0.6, 9.0, 0.56, 0.62, 0.45), splash=(0.08, 0.35, 0.7), ground_z=0.0, amount=1.0):
    """On a weathered_concrete material: vertical runoff streaks below drip edges (needs add_leak_field), grunge patches, soil splash above ground_z (the wall foot); all into its grime mask."""
    L_ = dict(RUNOFF_DEFAULTS, **(leak or {}))
    g, F = frame_for(mat, "Runoff streaks, grunge, splash")
    nt = mat.node_tree
    geo = g.node("ShaderNodeNewGeometry", (-2600, -3400), F)
    sepn = g.node("ShaderNodeSeparateXYZ", (-2400, -3700), F); g.link(geo.outputs["Normal"], sepn.inputs[0])
    vert = g.map_range(g.math("ABSOLUTE", sepn.outputs["Z"], 0.0, (-2200, -3700), F), 0.25, 0.1, (-2000, -3700), frame=F)
    sepp = g.node("ShaderNodeSeparateXYZ", (-2400, -3950), F); g.link(geo.outputs["Position"], sepp.inputs[0])
    # metres along the wall: position . horizontal tangent (normal x Z) - any wall orientation
    tan = g.node_with_props("ShaderNodeVectorMath", (-2400, -4050), operation="CROSS_PRODUCT")
    g.link(geo.outputs["Normal"], tan.inputs[0]); tan.inputs[1].default_value = (0.0, 0.0, 1.0)
    tn = g.node_with_props("ShaderNodeVectorMath", (-2250, -4050), operation="NORMALIZE"); g.link(tan.outputs[0], tn.inputs[0])
    dot = g.node_with_props("ShaderNodeVectorMath", (-2100, -4050), operation="DOT_PRODUCT")
    g.link(geo.outputs["Position"], dot.inputs[0]); g.link(tn.outputs[0], dot.inputs[1])
    along = dot.outputs["Value"]
    sv = g.node("ShaderNodeCombineXYZ", (-2000, -4100), F)
    g.link(g.math("MULTIPLY", along, L_["streak_frequency_per_m"], (-2150, -4100), F), sv.inputs["X"])
    g.link(g.math("MULTIPLY", sepp.outputs["Z"], L_["streak_vertical_frequency_per_m"], (-2150, -4250), F), sv.inputs["Y"])
    streak = g.map_range(g.noise_texture(sv.outputs[0], 1.0, (-1850, -4100), F, detail=4, roughness=0.55), *L_["streak_band"],
                     (-1650, -4100), frame=F, smooth=True)
    lv = g.node("ShaderNodeCombineXYZ", (-2000, -4400), F)
    g.link(g.math("MULTIPLY", along, 2.5, (-2150, -4400), F), lv.inputs["X"])
    llen = g.map_range(g.noise_texture(lv.outputs[0], 1.0, (-1850, -4400), F, detail=2), 0.35, 0.65, (-1650, -4400),
                   L_["length_range_m"][0], L_["length_range_m"][1], F)
    d = g.attribute("leak_d", (-1850, -4650), F)
    ok = g.attribute("leak_ok", (-1850, -4800), F)
    fade = g.math("SUBTRACT", 1.0, g.math("DIVIDE", d, llen, (-1450, -4500), F), (-1300, -4500), F, clamp=True)
    fade = g.math("POWER", fade, L_["fade_pow"], (-1150, -4500), F)
    top = g.map_range(d, 0.0, L_["top_band"], (-1450, -4700), L_["top"], 0.0, F, smooth=True)
    pv = g.node("ShaderNodeCombineXYZ", (-2000, -4950), F)
    g.link(g.math("MULTIPLY", along, 0.7, (-2150, -4950), F), pv.inputs["X"])
    presence = g.map_range(g.noise_texture(pv.outputs[0], 1.0, (-1850, -4950), F, detail=3), *L_["presence"], (-1650, -4950), frame=F)
    leak = g.math("MAXIMUM", g.math("MULTIPLY", streak, fade, (-1000, -4300), F), top, (-850, -4400), F)
    leak = g.math("MULTIPLY", leak, presence, (-700, -4400), F)
    leak = g.math("MULTIPLY", leak, g.math("MULTIPLY", ok, vert, (-850, -4700), F), (-550, -4500), F)
    gate = g.map_range(d, -0.02, 0.0, (-1450, -4850), frame=F)
    leak = g.math("MULTIPLY", g.math("MULTIPLY", leak, gate, (-400, -4500), F), L_["amount"], (-250, -4500), F)
    leak.node.label = "leak streak mask"
    ps, hs, lo, hi, amt = grunge
    patch = g.math("ADD", g.noise_texture(geo.outputs["Position"], ps, (-1850, -5200), F, detail=3),
                   g.math("MULTIPLY", g.math("SUBTRACT", g.noise_texture(geo.outputs["Position"], hs, (-1850, -5400), F, detail=6), 0.5,
                                             (-1650, -5400), F), 0.35, (-1500, -5400), F), (-1350, -5250), F)
    grg = g.map_range(patch, lo, hi, (-1200, -5250), 0.0, amt, F)
    grg.node.label = "grunge patches"
    foot = g.math("ADD", g.math("SUBTRACT", sepp.outputs["Z"], ground_z, (-1500, -5750), F), g.math("MULTIPLY", g.math("SUBTRACT", g.noise_texture(geo.outputs["Position"], 6.0, (-1850, -5650), F), 0.5,
                                                                      (-1650, -5650), F), 0.25, (-1500, -5650), F), (-1350, -5600), F)
    spl = g.math("MULTIPLY", g.map_range(foot, splash[0], splash[1], (-1200, -5600), splash[2], 0.0, F, smooth=True), vert, (-1050, -5600), F)
    spl.node.label = "soil splash"
    mix = next(n for n in nt.nodes if n.label == "Wear Layered (BRDFLayered)")
    fac = mix.inputs["Fac"]
    old = fac.links[0].from_socket if fac.is_linked else fac.default_value
    layer = g.math('MAXIMUM', g.math('MAXIMUM', leak, grg, (-100, -4500), F), spl, (50, -4600), F)
    layer = g.math('MULTIPLY', layer, amount, (200, -4600), F)
    layer.node.label = 'Run-off strength'
    m = g.math('MAXIMUM', old, layer, (350, -4600), F)
    g.link(m, mix.inputs["Fac"])
    return mat


def deposit_profile(graph, body, rim, tone, frame=None):
    """Keep a faint deposit body inside a stronger dark rim, with scan/noise tone variation."""
    variation=graph.map_range(tone,0,1,(-600,-18000),target_min=.32,target_max=.18,frame=frame)
    interior=graph.math('MULTIPLY',body,variation,(-300,-18000),frame)
    return graph.math('MAXIMUM',interior,rim,(0,-18000),frame)


def deposit_distance(graph,vector,scale_m,frame=None):
    """Return a continuous warped blob distance and tone, before body/rim plateaus are applied."""
    scale=graph.node('ShaderNodeVectorMath',(-3000,-18000),frame)
    scale.operation='SCALE'
    scale.inputs['Scale'].default_value=1/scale_m
    graph.link(vector,scale.inputs[0])
    warp=graph.node('ShaderNodeTexNoise',(-2800,-18000),frame,Scale=1.8,Detail=3.)
    graph.link(scale.outputs[0],warp.inputs['Vector'])
    offset=graph.node('ShaderNodeVectorMath',(-2500,-18000),frame)
    offset.operation='SUBTRACT'
    graph.link(warp.outputs['Color'],offset.inputs[0])
    offset.inputs[1].default_value=(.5,.5,.5)
    stretch=graph.node('ShaderNodeVectorMath',(-2300,-18000),frame)
    stretch.operation='SCALE'
    stretch.inputs['Scale'].default_value=1.6  # domain distortion relative to blob spacing
    graph.link(offset.outputs[0],stretch.inputs[0])
    warped=graph.node('ShaderNodeVectorMath',(-2000,-18000),frame)
    warped.operation='ADD'
    graph.link(scale.outputs[0],warped.inputs[0])
    graph.link(stretch.outputs[0],warped.inputs[1])
    field=graph.noise_texture(warped.outputs[0],1.,(-1800,-18000),frame,detail=3,roughness=.65)
    slow=graph.noise_texture(scale.outputs[0],.35,(-1800,-18600),frame,detail=2)
    threshold=graph.map_range(slow,0,1,(-1500,-18600),target_min=.49,target_max=.64,frame=frame)
    distance=graph.math('SUBTRACT',field,threshold,(-1200,-18000),frame)
    return distance,slow,warped.outputs[0]


def irregular_deposits(graph,vector,scale_m,frame=None):
    """Warp a multiscale noise domain into varied, sometimes merged blobs with broken rims."""
    distance,slow,warped=deposit_distance(graph,vector,scale_m,frame)
    body=graph.map_range(distance,-.008,.025,(-900,-18000),frame=frame,smooth=True)
    absolute=graph.math('ABSOLUTE',distance,0,(-1200,-18400),frame)
    rim=graph.map_range(absolute,.006,.025,(-900,-18400),target_min=1,target_max=0,frame=frame,smooth=True)
    broken=graph.noise_texture(warped,4.,(-1200,-19000),frame,detail=2)
    broken=graph.map_range(broken,.25,.75,(-900,-19000),target_min=.25,target_max=1,frame=frame)
    rim=graph.math('MULTIPLY',rim,broken,(-600,-18400),frame)
    return deposit_profile(graph,body,rim,slow,frame)



def dried_marks_field(graph, vector, scale_m, frame=None, region=False):
    """Return the continuous blob driver for regions or its dry body/rim profile."""
    if region:
        distance, _, _ = deposit_distance(graph, vector, scale_m, frame)
        return graph.map_range(distance, -.12, .12, (-900, -18000), frame=frame)
    return irregular_deposits(graph, vector, scale_m, frame)
