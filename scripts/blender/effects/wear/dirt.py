"""Dust build-up and bordered grunge patterns."""
from types import SimpleNamespace
from materials.shared.node_graph import NodeGraph, layer_switch
from effects.wear.edge_profile import (LINE_WIDTH_M, DUST_WIDTH_M, LINE_AMOUNT, DUST_AMOUNT,
    GRIME_TINT, LINE_GAIN, DUST_SATURATION, LINE_ROUGHNESS, DUST_GAIN, CORNER_MASK_CAP,
    AO_REACH_M, EDGE_KINDS)
from effects.wear.edge_profile import _noise_context, _extent, _falloff, _finish_mask
from effects.wear.edge_line import _line_mask

RGB_LUMINANCE = (0.2126, 0.7152, 0.0722)  # scene-linear luminance

def _dust_mask(graph, context, fields, width, amount):
    frame, (x, y) = context.frame, context.location
    extent = _extent(graph, context, fields.width_noise, width, (0.65, 1.6), 'dust')
    band, lip = _falloff(graph, context, extent, 0.0, 0.002, 'dust')
    profile = graph.math('MULTIPLY', band, lip, (x + 1000, y), frame)
    patch = fields.presence
    if context.recipe['dust_floor'] is not None:
        patch = graph.math('ADD', context.recipe['dust_floor'], graph.math('MULTIPLY', fields.presence, context.recipe['dust_gain'],
                      (x + 1000, y - 1900), frame), (x + 1200, y - 1900), frame)
    broken = graph.math('MULTIPLY', profile, patch, (x + 1400, y), frame)
    broken = graph.math('MULTIPLY', broken, context.dust_orientation, (x + 1600, y), frame)
    return _finish_mask(graph, context, broken, amount, 'dust')


def edge_dirt_masks(graph, dist, line_width=LINE_WIDTH_M, dust_width=DUST_WIDTH_M, noise_vec=None,
                    line_amount=LINE_AMOUNT, dust_amount=DUST_AMOUNT,
                    noise_scale=9.0, frame=None, location=(0, 0), mask_cap=1.0, kind='outside'):
    """Return line, dust and the reusable outside-vertex join (None for AO corners)."""
    if line_width <= 0 or dust_width <= 0:
        raise ValueError('edge dirt widths must be positive')
    context = SimpleNamespace(dist=dist, frame=frame, location=location, recipe=EDGE_KINDS[kind], cap=mask_cap)
    context.recipe['context'](graph, context, line_width)
    fields = _noise_context(graph, context, context.position if noise_vec is None else noise_vec, noise_scale)
    line = _line_mask(graph, context, fields, line_width, line_amount)
    context.location = (location[0], location[1] - 300)
    dust = _dust_mask(graph, context, fields, dust_width, dust_amount)
    return line, dust, context.join


def corner_dirt_masks(graph, line_width=LINE_WIDTH_M, dust_width=DUST_WIDTH_M,
                      line_amount=LINE_AMOUNT, dust_amount=DUST_AMOUNT,
                      frame=None, location=(0, 0), corner_cap=CORNER_MASK_CAP):
    """Return shared masks using cross-object AO remapped to a distance-like metre field."""
    x, y = location
    ao = graph.node('ShaderNodeAmbientOcclusion', (x - 600, y), frame,
                label='Corner AO (cross-object)', Distance=AO_REACH_M)
    ao.inside = False
    ao.only_local = False
    ao.samples = 32  # cross-object occlusion rays
    # A perpendicular contact covers half the AO hemisphere.
    unit_dist = graph.map_range(ao.outputs['AO'], 0.5, 1.0, (x - 400, y), frame=frame,
                       label='corner distance-like 0..1')
    dist = graph.math('MULTIPLY', unit_dist, AO_REACH_M, (x - 200, y), frame)
    return edge_dirt_masks(graph, dist, line_width, dust_width, line_amount=line_amount,
                           dust_amount=dust_amount, frame=frame, location=location, mask_cap=corner_cap, kind='corner')[:2]


def _relative_dust_color(graph, color, dust, frame, location):
    """Desaturate and gently darken albedo through the independent dust term."""
    x, y = location
    luma = graph.vector_math('DOT_PRODUCT', color, RGB_LUMINANCE, (x - 220, y - 140), frame,
                   label='Dust source luminance')
    desat = graph.mix(color, luma, 1.0 - DUST_SATURATION, (x, y), frame,
                  label='Dust relative desaturation')
    gain = graph.mix(desat, (*DUST_GAIN, 1), 1.0, (x + 220, y), frame, blend='MULTIPLY',
                 label='Dust relative darkening')
    return graph.mix(color, gain, dust, (x + 440, y), frame, label='Dust relative albedo')


def dust_surface(graph, surface, dust, frame=None, location=(0, 0), line=None):
    """Apply relative dust/line albedos with line priority, preserving source textures and normals."""
    # Follow only shader links, so colour/bump subgraphs and other output branches stay intact.
    pending, seen, bases = [surface.node], set(), []
    while pending:
        node = pending.pop()
        if node in seen:
            continue
        seen.add(node)
        color = node.inputs.get('Base Color') or node.inputs.get('Color')
        if node.type.startswith('BSDF') and color is not None:
            bases.append(color)
        pending.extend(link.from_node for inp in node.inputs if inp.type == 'SHADER'
                       for link in inp.links)
    for i, target in enumerate(bases):
        if target.is_linked:
            color = target.links[0].from_socket
        else:
            value = graph.node('ShaderNodeRGB', (location[0] - 220, location[1] - i * 250), frame,
                           label='Dust original albedo')
            value.outputs[0].default_value = target.default_value
            color = value.outputs[0]
        adjusted = _relative_dust_color(graph, color, dust, frame, (location[0], location[1] - i * 250))
        if line is not None:
            gain = graph.mix(color, (LINE_GAIN, LINE_GAIN, LINE_GAIN, 1), 1.0,
                         (location[0] + 660, location[1] - i * 250), frame, blend='MULTIPLY',
                         label='Line relative darkening')
            adjusted = graph.mix(adjusted, gain, line, (location[0] + 880, location[1] - i * 250), frame,
                             label='Line relative albedo')
            roughness = target.node.inputs.get('Roughness')
            if roughness is not None:
                original = roughness.links[0].from_socket if roughness.is_linked else roughness.default_value
                rough = graph.mix(original, LINE_ROUGHNESS, line, (location[0] + 660, location[1] - i * 250 - 140),
                              frame, data_type='FLOAT', label='Line roughness (unchanged target)')
                graph.link(rough, roughness)
        graph.link(adjusted, target)
    return surface


def add_corner_dirt(mat, line_width=LINE_WIDTH_M, dust_width=DUST_WIDTH_M,
                    line_amount=LINE_AMOUNT, dust_amount=DUST_AMOUNT, corner_cap=CORNER_MASK_CAP):
    """Add independently switchable shared line/dust layers to a Cycles surface material."""
    g = NodeGraph(mat.node_tree)
    existing = {role: next((n.outputs[0] for n in g.tree.nodes
                           if n.label == 'Edge ' + role + ' strength'), None)
                for role in ('line', 'dust')}
    frame = 'Corner edge line and dust'
    g.frame(frame, (0.32, 0.24, 0.16))
    line, dust = corner_dirt_masks(g, line_width, dust_width, line_amount, dust_amount, frame,
                                  corner_cap=corner_cap)
    if all(existing.values()):
        # Reuse the outside BRDFs and chip exclusions instead of exceeding Cycles' closure limit.
        for i, (role, corner) in enumerate((('line', line), ('dust', dust))):
            old = existing[role]
            consumers = [link.to_socket for link in old.links]
            union = g.math('MAXIMUM', old, corner, (900, -i * 220), frame)
            union.node.label = 'Outside + corner ' + role
            for target in consumers:
                g.link(union, target)
        return mat
    out = next(n for n in g.tree.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output)
    surface = out.inputs['Surface'].links[0].from_socket
    result = dust_surface(g, surface, dust, frame, (1400, 0), line=line)
    g.link(result, out.inputs['Surface'])
    return mat


def grunge(graph, scale_m=0.5, target_sd=0.05, detail=6.0, rough=0.6, amount=1.0):
    """Return the legacy calibrated grunge multiplier, preserving existing callers exactly."""
    from effects.variation_macro_tone import _moments, _field
    mean, sd = _moments(detail, rough)
    noise, frame = _field(graph, 'grunge', scale_m, detail, rough)
    signed = graph.math('SUBTRACT', noise, mean, (-1200, 0), frame)
    gain = graph.math('MULTIPLY', signed, target_sd/sd, (-900, 0), frame)
    raw = graph.math('ADD', gain, 1, (-600, 0), frame)
    return layer_switch(graph, 'grunge', raw, amount, 1, frame)



def grunge_field(graph, vector, scale_m, frame=None):
    """Return the unchanged fine grunge times zero-reaching slow patch pattern."""
    noise = graph.noise_texture(vector, 1 / scale_m, (-1800, 0), frame, detail=3)
    fine = graph.map_range(noise, .35, .65, (-1500, 0), frame=frame)
    extent = graph.noise_texture(vector, 1 / (scale_m * 4), (-1800, -400), frame)
    extent = graph.map_range(extent, .43, .57, (-1500, -400), frame=frame)
    return graph.math('MULTIPLY', fine, extent, (-1200, 0), frame)
