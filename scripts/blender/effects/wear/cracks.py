"""Cracks on a concrete wall: shrinkage cracks from the corners of openings, patchy map-cracking over the
rest, a dark core, a grime halo and a shallow groove. Works on a weathered_concrete material.
"""
import math
import random

from materials.shared.node_graph import frame_for
from effects.wear.crack_ribbon import crooked_ribbon_masks

CRACK = dict(core=0.005, halo=0.02, wobble=0.03, jag=0.006, len=(0.4, 1.0), jitter=14.0, seed=3,
             net_scale=1.6, net_dist=0.22, net_keep=0.4, net_patch=(0.52, 0.6), depth=0.003, halo_dirt=0.6)


def crack_masks(g, F, openings, C):
    """Core and halo masks for the shrinkage cracks from each opening's corners, plus map-cracking."""
    rnd = random.Random(C["seed"])
    geo = g.node("ShaderNodeNewGeometry", (-2600, -6200), F)
    pos = geo.outputs["Position"]
    sp = g.node("ShaderNodeSeparateXYZ", (-2400, -6200), F); g.link(pos, sp.inputs[0])
    wob = g.math("MULTIPLY", g.math("SUBTRACT", g.noise_texture(pos, 26.0, (-2400, -6450), F, detail=4, rough=0.6), 0.5, (-2250, -6450), F),
                 C["wobble"] * 2, (-2100, -6450), F)
    jag = g.math("MULTIPLY", g.math("SUBTRACT", g.noise_texture(pos, 180.0, (-2400, -6650), F, detail=2, rough=0.5), 0.5, (-2250, -6650), F),
                 C["jag"] * 2, (-2100, -6650), F)
    wob = g.math("ADD", wob, jag, (-1950, -6550), F)
    core = halo = None
    y = -6200
    corner_index = 0
    for op in openings:
        axis, plane, u0, u1, v0, v1, top_only = op[:7]
        keep = op[7] if len(op) > 7 else None
        dist = g.math("ABSOLUTE", g.math("SUBTRACT", sp.outputs["X" if axis == "x" else "Y"], plane, (-2200, y), F), 0.0, (-2050, y), F)
        on = g.map_range(dist, 0.03, 0.01, (-1900, y), frame=F)
        uu = sp.outputs["Y" if axis == "x" else "X"]
        corners = [(u0, v1, 135), (u1, v1, 45)] + ([] if top_only else [(u0, v0, 225), (u1, v0, 315)])
        for cu, cv, ang in corners:
            a = math.radians(ang + rnd.uniform(-C["jitter"], C["jitter"]))
            L = rnd.uniform(*C["len"])
            corner_index += 1
            if keep and ang not in keep:          # draws stay, so the other cracks don't move
                continue
            du = g.math("SUBTRACT", uu, cu, (-1900, y - 150), F)
            dv = g.math("SUBTRACT", sp.outputs["Z"], cv, (-1900, y - 300), F)
            along = g.math("ADD", g.math("MULTIPLY", du, math.cos(a), (-1750, y - 150), F),
                           g.math("MULTIPLY", dv, math.sin(a), (-1750, y - 300), F), (-1600, y - 200), F)
            perp = g.math("SUBTRACT", g.math("MULTIPLY", dv, math.cos(a), (-1750, y - 450), F),
                          g.math("MULTIPLY", du, math.sin(a), (-1750, y - 600), F), (-1600, y - 500), F)
            c, h = crooked_ribbon_masks(g, F, along, perp, wob, on, C, L, y,
                                       seed=C["seed"] * 1009 + corner_index)
            core = c if core is None else g.math("MAXIMUM", core, c, (-250, y - 400), F)
            halo = h if halo is None else g.math("MAXIMUM", halo, h, (-250, y - 600), F)
            y -= 800
    dis = g.node("ShaderNodeTexNoise", (-2400, y), F, Scale=2.0, Detail=3.0); g.link(pos, dis.inputs["Vector"])
    off = g.node_with_props("ShaderNodeVectorMath", (-2250, y), operation="MULTIPLY_ADD")
    g.link(dis.outputs["Color"], off.inputs[0]); off.inputs[1].default_value = (C["net_dist"],) * 3; g.link(pos, off.inputs[2])
    fine = g.node('ShaderNodeTexNoise', (-2250, y - 650), F, Scale=18.0, Detail=3.0)
    g.link(pos, fine.inputs['Vector'])
    bent = g.node_with_props('ShaderNodeVectorMath', (-2100, y - 650), operation='MULTIPLY_ADD')
    g.link(fine.outputs['Color'], bent.inputs[0])
    bent.inputs[1].default_value = (C['net_dist'] * 0.16,) * 3
    g.link(off.outputs[0], bent.inputs[2])
    ve = g.node("ShaderNodeTexVoronoi", (-2100, y), F, Scale=C["net_scale"]); ve.feature = "DISTANCE_TO_EDGE"
    g.link(bent.outputs[0], ve.inputs["Vector"])
    vc = g.node("ShaderNodeTexVoronoi", (-2100, y - 250), F, Scale=C["net_scale"]); g.link(bent.outputs[0], vc.inputs["Vector"])
    vcs = g.node("ShaderNodeSeparateColor", (-1950, y - 250), F); g.link(vc.outputs["Color"], vcs.inputs[0])
    keep_e = g.math("GREATER_THAN", vcs.outputs["Red"], C["net_keep"], (-1800, y - 250), F)
    patch = g.map_range(g.noise_texture(pos, 0.45, (-1950, y - 450), F, detail=3), *C["net_patch"], (-1800, y - 450), frame=F)
    pres = g.math("MULTIPLY", keep_e, patch, (-1650, y - 350), F)
    nc = g.math("MULTIPLY", g.math("SUBTRACT", 1.0, g.math("DIVIDE", ve.outputs["Distance"], C["core"] * 0.8, (-1800, y), F), (-1650, y), F, clamp=True), pres, (-1500, y), F)
    nh = g.math("MULTIPLY", g.math("SUBTRACT", 1.0, g.math("DIVIDE", ve.outputs["Distance"], C["halo"] * 0.7, (-1800, y - 100), F), (-1650, y - 100), F, clamp=True), pres, (-1500, y - 100), F)
    core = nc if core is None else g.math("MAXIMUM", core, nc, (-250, y), F)
    halo = nh if halo is None else g.math("MAXIMUM", halo, nh, (-250, y - 100), F)
    core.node.label = "crack core"; halo.node.label = "crack halo"
    return core, halo



def add_cracks(mat, openings=(), crack=None, amount=1.0):
    """On a weathered_concrete material: shrinkage cracks from opening corners + patchy map-cracking; dark core over everything, grime halo, groove. openings: (axis 'x'|'y', plane, u0, u1, v0, v1, top_only[, keep_angles])."""
    C = dict(CRACK, **(crack or {}))
    g, F = frame_for(mat, "Cracks")
    core, halo = crack_masks(g, F, openings, C)
    return apply_crack_masks(mat, g, F, core, halo, C, amount, 'Opening cracks')


def apply_crack_masks(mat, g, F, core, halo, C, amount, label):
    """Compose crack core, halo and groove under one independent amount."""
    nt = mat.node_tree
    strength = g.node('ShaderNodeValue', (0, -5000), F, label=label + ' strength')
    strength.outputs[0].default_value = amount
    core = g.math('MULTIPLY', core, strength.outputs[0], (150, -5000), F)
    halo = g.math('MULTIPLY', halo, strength.outputs[0], (150, -5200), F)
    mix = next(n for n in nt.nodes if n.label == "Wear Layered (BRDFLayered)")
    fac = mix.inputs["Fac"]
    old = fac.links[0].from_socket if fac.is_linked else fac.default_value
    g.link(g.math("MAXIMUM", old, g.math("MULTIPLY", halo, C["halo_dirt"], (350, -4700), F), (500, -4650), F), mix.inputs["Fac"])
    # Follow the current normal chain so rounding can be off and both crack layers compose.
    clean = next(n for n in nt.nodes if n.label == 'Concrete')
    normal = clean.inputs['Normal'].links[0].from_socket
    users = [link.to_socket for link in normal.links]
    cb = g.node('ShaderNodeBump', (0, -5500), F, label=label + ' groove')
    cb.invert = True
    cb.inputs['Distance'].default_value = C['depth']
    g.link(core, cb.inputs['Height'])
    g.link(normal, cb.inputs['Normal'])
    for user in users:
        g.link(cb.outputs['Normal'], user)
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    last = out.inputs["Surface"].links[0].from_socket
    dark = g.node("ShaderNodeBsdfPrincipled", (out.location.x - 200, out.location.y - 300), F, label="crack interior", Roughness=0.95)
    dark.inputs["Base Color"].default_value = (0.03, 0.03, 0.028, 1)
    mx = g.node("ShaderNodeMixShader", (out.location.x - 100, out.location.y - 100), F, label="cracks over surface")
    g.link(g.math("MULTIPLY", core, 0.9, (out.location.x - 300, out.location.y - 500), F), mx.inputs["Fac"])
    g.link(last, mx.inputs[1]); g.link(dark.outputs[0], mx.inputs[2]); g.link(mx.outputs[0], out.inputs["Surface"])
    return mat
