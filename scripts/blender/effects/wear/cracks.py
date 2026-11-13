"""Cracks on a concrete wall: shrinkage cracks from the corners of openings, patchy map-cracking over the
rest, a dark core, a grime halo and a shallow groove. Works on a weathered_concrete material.
"""
import math
import random

from materials.shared.node_graph import frame_for
from effects.wear.crack_ribbon import crooked_ribbon_masks

CRACK_DEFAULTS = dict(core=0.005, halo=0.02, wobble=0.03, jaggedness_m=0.006, length_range_m=(0.4, 1.0), jitter=14.0, seed=3,
             net_scale=1.6, network_distortion_m=0.22, network_keep_share=0.4, net_patch=(0.52, 0.6), depth=0.003, halo_dirt=0.6)


def crack_masks(graph, frame, openings, settings):
    """Core and halo masks for the shrinkage cracks from each opening's corners, plus map-cracking."""
    rnd = random.Random(settings["seed"])
    geo = graph.node("ShaderNodeNewGeometry", (-2600, -6200), frame)
    pos = geo.outputs["Position"]
    sp = graph.node("ShaderNodeSeparateXYZ", (-2400, -6200), frame); graph.link(pos, sp.inputs[0])
    wob = graph.math("MULTIPLY", graph.math("SUBTRACT", graph.noise_texture(pos, 26.0, (-2400, -6450), frame, detail=4, roughness=0.6), 0.5, (-2250, -6450), frame),
                 settings["wobble"] * 2, (-2100, -6450), frame)
    jag = graph.math("MULTIPLY", graph.math("SUBTRACT", graph.noise_texture(pos, 180.0, (-2400, -6650), frame, detail=2, roughness=0.5), 0.5, (-2250, -6650), frame),
                 settings["jaggedness_m"] * 2, (-2100, -6650), frame)
    wob = graph.math("ADD", wob, jag, (-1950, -6550), frame)
    core = halo = None
    y = -6200
    corner_index = 0
    for op in openings:
        axis, plane, u0, u1, v0, v1, top_only = op[:7]
        keep = op[7] if len(op) > 7 else None
        dist = graph.math("ABSOLUTE", graph.math("SUBTRACT", sp.outputs["X" if axis == "x" else "Y"], plane, (-2200, y), frame), 0.0, (-2050, y), frame)
        on = graph.map_range(dist, 0.03, 0.01, (-1900, y), frame=frame)
        uu = sp.outputs["Y" if axis == "x" else "X"]
        corners = [(u0, v1, 135), (u1, v1, 45)] + ([] if top_only else [(u0, v0, 225), (u1, v0, 315)])
        for cu, cv, ang in corners:
            a = math.radians(ang + rnd.uniform(-settings["jitter"], settings["jitter"]))
            L = rnd.uniform(*settings["length_range_m"])
            corner_index += 1
            if keep and ang not in keep:          # draws stay, so the other cracks don't move
                continue
            du = graph.math("SUBTRACT", uu, cu, (-1900, y - 150), frame)
            dv = graph.math("SUBTRACT", sp.outputs["Z"], cv, (-1900, y - 300), frame)
            along = graph.math("ADD", graph.math("MULTIPLY", du, math.cos(a), (-1750, y - 150), frame),
                           graph.math("MULTIPLY", dv, math.sin(a), (-1750, y - 300), frame), (-1600, y - 200), frame)
            perp = graph.math("SUBTRACT", graph.math("MULTIPLY", dv, math.cos(a), (-1750, y - 450), frame),
                          graph.math("MULTIPLY", du, math.sin(a), (-1750, y - 600), frame), (-1600, y - 500), frame)
            c, h = crooked_ribbon_masks(graph, frame, along, perp, wob, on, settings, L, y,
                                       seed=settings["seed"] * 1009 + corner_index)
            core = c if core is None else graph.math("MAXIMUM", core, c, (-250, y - 400), frame)
            halo = h if halo is None else graph.math("MAXIMUM", halo, h, (-250, y - 600), frame)
            y -= 800
    dis = graph.node("ShaderNodeTexNoise", (-2400, y), frame, Scale=2.0, Detail=3.0); graph.link(pos, dis.inputs["Vector"])
    off = graph.node_with_props("ShaderNodeVectorMath", (-2250, y), operation="MULTIPLY_ADD")
    graph.link(dis.outputs["Color"], off.inputs[0]); off.inputs[1].default_value = (settings["network_distortion_m"],) * 3; graph.link(pos, off.inputs[2])
    fine = graph.node('ShaderNodeTexNoise', (-2250, y - 650), frame, Scale=18.0, Detail=3.0)
    graph.link(pos, fine.inputs['Vector'])
    bent = graph.node_with_props('ShaderNodeVectorMath', (-2100, y - 650), operation='MULTIPLY_ADD')
    graph.link(fine.outputs['Color'], bent.inputs[0])
    bent.inputs[1].default_value = (settings['network_distortion_m'] * 0.16,) * 3
    graph.link(off.outputs[0], bent.inputs[2])
    ve = graph.node("ShaderNodeTexVoronoi", (-2100, y), frame, Scale=settings["net_scale"]); ve.feature = "DISTANCE_TO_EDGE"
    graph.link(bent.outputs[0], ve.inputs["Vector"])
    vc = graph.node("ShaderNodeTexVoronoi", (-2100, y - 250), frame, Scale=settings["net_scale"]); graph.link(bent.outputs[0], vc.inputs["Vector"])
    vcs = graph.node("ShaderNodeSeparateColor", (-1950, y - 250), frame); graph.link(vc.outputs["Color"], vcs.inputs[0])
    keep_e = graph.math("GREATER_THAN", vcs.outputs["Red"], settings["network_keep_share"], (-1800, y - 250), frame)
    patch = graph.map_range(graph.noise_texture(pos, 0.45, (-1950, y - 450), frame, detail=3), *settings["net_patch"], (-1800, y - 450), frame=frame)
    pres = graph.math("MULTIPLY", keep_e, patch, (-1650, y - 350), frame)
    nc = graph.math("MULTIPLY", graph.math("SUBTRACT", 1.0, graph.math("DIVIDE", ve.outputs["Distance"], settings["core"] * 0.8, (-1800, y), frame), (-1650, y), frame, clamp=True), pres, (-1500, y), frame)
    nh = graph.math("MULTIPLY", graph.math("SUBTRACT", 1.0, graph.math("DIVIDE", ve.outputs["Distance"], settings["halo"] * 0.7, (-1800, y - 100), frame), (-1650, y - 100), frame, clamp=True), pres, (-1500, y - 100), frame)
    core = nc if core is None else graph.math("MAXIMUM", core, nc, (-250, y), frame)
    halo = nh if halo is None else graph.math("MAXIMUM", halo, nh, (-250, y - 100), frame)
    core.node.label = "crack core"; halo.node.label = "crack halo"
    return core, halo



def add_cracks(mat, openings=(), crack=None, amount=1.0):
    """On a weathered_concrete material: shrinkage cracks from opening corners + patchy map-cracking; dark core over everything, grime halo, groove. openings: (axis 'x'|'y', plane, u0, u1, v0, v1, top_only[, keep_angles])."""
    C = dict(CRACK_DEFAULTS, **(crack or {}))
    g, F = frame_for(mat, "Cracks")
    core, halo = crack_masks(g, F, openings, C)
    return apply_crack_masks(mat, g, F, core, halo, C, amount, 'Opening cracks')


def apply_crack_masks(mat, graph, frame, core, halo, settings, amount, label):
    """Compose crack core, halo and groove under one independent amount."""
    nt = mat.node_tree
    strength = graph.node('ShaderNodeValue', (0, -5000), frame, label=label + ' strength')
    strength.outputs[0].default_value = amount
    core = graph.math('MULTIPLY', core, strength.outputs[0], (150, -5000), frame)
    halo = graph.math('MULTIPLY', halo, strength.outputs[0], (150, -5200), frame)
    mix = next(n for n in nt.nodes if n.label == "Wear Layered (BRDFLayered)")
    fac = mix.inputs["Fac"]
    old = fac.links[0].from_socket if fac.is_linked else fac.default_value
    graph.link(graph.math("MAXIMUM", old, graph.math("MULTIPLY", halo, settings["halo_dirt"], (350, -4700), frame), (500, -4650), frame), mix.inputs["Fac"])
    # Follow the current normal chain so rounding can be off and both crack layers compose.
    clean = next(n for n in nt.nodes if n.label == 'Concrete')
    normal = clean.inputs['Normal'].links[0].from_socket
    users = [link.to_socket for link in normal.links]
    cb = graph.node('ShaderNodeBump', (0, -5500), frame, label=label + ' groove')
    cb.invert = True
    cb.inputs['Distance'].default_value = settings['depth']
    graph.link(core, cb.inputs['Height'])
    graph.link(normal, cb.inputs['Normal'])
    for user in users:
        graph.link(cb.outputs['Normal'], user)
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    last = out.inputs["Surface"].links[0].from_socket
    dark = graph.node("ShaderNodeBsdfPrincipled", (out.location.x - 200, out.location.y - 300), frame, label="crack interior", Roughness=0.95)
    dark.inputs["Base Color"].default_value = (0.03, 0.03, 0.028, 1)
    mx = graph.node("ShaderNodeMixShader", (out.location.x - 100, out.location.y - 100), frame, label="cracks over surface")
    graph.link(graph.math("MULTIPLY", core, 0.9, (out.location.x - 300, out.location.y - 500), frame), mx.inputs["Fac"])
    graph.link(last, mx.inputs[1]); graph.link(dark.outputs[0], mx.inputs[2]); graph.link(mx.outputs[0], out.inputs["Surface"])
    return mat
