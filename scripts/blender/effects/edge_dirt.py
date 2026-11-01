"""Shared edge line and dust layers for convex distance fields and concave AO."""
from types import SimpleNamespace
from materials.shared.nodes import G, sock
from effects.wear_nodes import math_, noise, range_

LINE_WIDTH, DUST_WIDTH = 0.015, 0.150  # m, nominal line and dust widths
LINE_AMOUNT, DUST_AMOUNT = 1.70, 0.40  # line and dust mask gains
OUTSIDE_LINE_BOOST = 2.7  # gain balances the connected base, slow strength and fine spot contrast
OUTSIDE_LINE_PRESENCE = (0.28, 0.34)  # only rare low troughs interrupt the long outside run
OUTSIDE_LINE_WIDTH_LIMITS = (1.175, 1.675)  # multiples of the nominal line width
OUTSIDE_LINE_STRENGTH_FLOOR = 0.32  # carry more of the slow variation in darkness instead of width
GRIME_TINT = (0.105, 0.098, 0.088)  # absolute stain/run-off albedo
LINE_GAIN, DUST_SATURATION, LINE_ROUGHNESS = 0.50, 0.90, 0.93  # line albedo gain, retained dust saturation and line roughness
DUST_GAIN = (0.825, 0.825, 0.825)  # dust is between the clean surface and line
CORNER_MASK_CAP, AO_REACH = 0.50, 0.30  # contact mask ceiling and dust AO reach in metres
LINE_UP_WEIGHT, VERTEX_LINE_WEIGHT = 0.45, 0.65  # top-facing line and shared junction weights


def _vector(g, operation, a, b, loc, frame, label=None):
    node = g.node('ShaderNodeVectorMath', loc, frame, label=label)
    node.operation = operation
    g.link(a, node.inputs[0])
    if b is not None:
        g.link(b, node.inputs['Scale'] if operation == 'SCALE' else node.inputs[1])
    return node


def edge_vertex_join(g, line_width=LINE_WIDTH, frame=None, loc=(0, 0)):
    """Return a local outside-junction blend from clean-mesh vertex distance in metres."""
    x, y = loc
    distance = g.attr('edge_vertex_dist', (x, y), frame)
    valid = g.attr('edge_vertex_valid', (x, y - 180), frame)
    join = range_(g, distance, line_width, 4 * line_width, (x + 200, y), frame,
                  1.0, 0.0, label='Outside vertex fade', smooth=True)
    join = math_(g, 'MULTIPLY', join, valid, (x + 400, y), frame, clamp=True)
    join.node.label = 'Outside vertex join'
    return join


def _outside_context(g, context, line_width):
    """Project macro noise onto the nearby edge and derive orientation from the clean field."""
    dist, frame, (x, y) = context.dist, context.frame, context.loc
    geo = g.node('ShaderNodeNewGeometry', (x - 1200, y - 800), frame)
    bump = g.node('ShaderNodeBump', (x - 1000, y - 800), frame,
                  label='Field gradient only (not surface bump)', Distance=0.02)
    g.link(dist, bump.inputs['Height'])
    g.link(geo.outputs['True Normal'], bump.inputs['Normal'])
    delta = _vector(g, 'SUBTRACT', bump.outputs['Normal'], geo.outputs['True Normal'], (x - 800, y - 800), frame)
    toward = _vector(g, 'NORMALIZE', delta.outputs[0], None, (x - 600, y - 800), frame)
    offset = _vector(g, 'SCALE', toward.outputs[0], dist, (x - 400, y - 800), frame)
    edge = _vector(g, 'ADD', geo.outputs['Position'], offset.outputs[0], (x - 200, y - 800), frame, label='Nearest edge coordinates (field gradient)')
    sep = g.node('ShaderNodeSeparateXYZ', (x - 800, y - 1100), frame)
    g.link(geo.outputs['True Normal'], sep.inputs[0])
    gradient = g.node('ShaderNodeSeparateXYZ', (x - 600, y - 1100), frame)
    g.link(toward.outputs[0], gradient.inputs[0])
    down = range_(g, sep.outputs['Z'], -0.25, -0.9, (x - 400, y - 1100), frame,
                  label='Down-facing wrapback', smooth=True)
    up = range_(g, sep.outputs['Z'], 0.25, 0.9, (x - 400, y - 1300), frame, smooth=True)
    vertical = math_(g, 'SUBTRACT', 1.0, math_(g, 'MAXIMUM', down, up,
                     (x - 200, y - 1200), frame), (x, y - 1200), frame)
    below = range_(g, gradient.outputs['Z'], 0.10, 0.75, (x - 200, y - 1450), frame,
                   label='Vertical face below edge', smooth=True)
    side = math_(g, 'ADD', 0.25, math_(g, 'MULTIPLY', below, 0.55,
                  (x, y - 1450), frame), (x + 200, y - 1450), frame)
    line_side = math_(g, 'MULTIPLY', vertical, side, (x + 400, y - 1450), frame)
    line_orient = math_(g, 'MAXIMUM', down, line_side, (x + 600, y - 1300), frame)
    line_orient = math_(g, 'MAXIMUM', line_orient, math_(g, 'MULTIPLY', up, LINE_UP_WEIGHT,
                        (x + 400, y - 1600), frame), (x + 800, y - 1300), frame)
    line_orient.node.label = 'Line orientation'
    dust_orient = math_(g, 'MAXIMUM', down, math_(g, 'MULTIPLY', vertical, 0.65,
                        (x + 600, y - 1700), frame), (x + 800, y - 1700), frame)
    dust_orient = math_(g, 'MAXIMUM', dust_orient, math_(g, 'MULTIPLY', up, 0.08,
                        (x + 600, y - 1850), frame), (x + 1000, y - 1700), frame)
    dust_orient.node.label = 'Dust orientation'
    vars(context).update(position=geo.outputs['Position'], along_edge=edge.outputs[0],
                         line_orientation=line_orient, dust_orientation=dust_orient)
    _join_context(g, context, line_width)


def _join_context(g, context, line_width):
    frame, (x, y) = context.frame, context.loc
    vertex_join = edge_vertex_join(g, line_width, frame, (x - 1200, y - 2200))
    # All incident faces approach the same weight and world-space coordinate at the vertex.
    line_orient = math_(g, 'ADD', context.line_orientation, math_(g, 'MULTIPLY', vertex_join,
                        math_(g, 'SUBTRACT', VERTEX_LINE_WEIGHT, context.line_orientation,
                              (x - 400, y - 2100), frame),
                        (x - 200, y - 2100), frame), (x, y - 2100), frame)
    line_orient.node.label = 'Joined line orientation'
    delta = _vector(g, 'SUBTRACT', context.position, context.along_edge, (x - 800, y - 2500), frame)
    scale = _vector(g, 'SCALE', delta.outputs[0], vertex_join, (x - 600, y - 2500), frame)
    joined = _vector(g, 'ADD', context.along_edge, scale.outputs[0], (x - 400, y - 2500), frame, label='Joined line coordinates')
    context.line_orientation, context.join, context.coordinates = line_orient, vertex_join, joined.outputs[0]


def _corner_context(g, context, line_width):
    x, y = context.loc
    position = g.node('ShaderNodeNewGeometry', (x - 1200, y - 800), context.frame).outputs['Position']
    vars(context).update(position=position, along_edge=position, coordinates=position,
                         line_orientation=1.0, dust_orientation=1.0, join=None)


def _noise_context(g, context, noise_vec, scale):
    frame, (x, y) = context.frame, context.loc
    macro = noise(g, context.along_edge, scale / 6.0, (x, y - 500), frame,
                  detail=2, rough=0.55, label='Edge low-frequency patches')
    macro.node.noise_dimensions = '4D'
    macro.node.inputs['W'].default_value = 0.37  # stable fourth-coordinate phase
    presence = range_(g, macro, 0.48, 0.53, (x + 200, y - 500), frame,
                      label='Edge macro presence', smooth=True)
    width_noise = noise(g, context.along_edge, scale / 2.5, (x, y - 750), frame,
                        detail=2, rough=0.55, label='Edge width variation')
    fields = SimpleNamespace(presence=presence, width_noise=width_noise, width=width_noise, run=None, strength=None)
    if context.recipe['long_line']:
        fields.run = noise(g, context.coordinates, scale / 24.0, (x, y - 2200), frame,
                           detail=1, rough=0.4, label='Outside line long runs')
        fields.run.node.noise_dimensions = '4D'
        fields.run.node.inputs['W'].default_value = 0.37  # stable fourth-coordinate phase
        fields.width = noise(g, context.coordinates, scale / 18.0, (x, y - 2450), frame,
                             detail=1, rough=0.4, label='Outside line slow width')
        fields.strength = range_(g, fields.run, 0.20, 0.80, (x + 200, y - 2200), frame,
                                 OUTSIDE_LINE_STRENGTH_FLOOR, 1.0, label='Outside line slow strength', smooth=True)
    spots = g.node('ShaderNodeTexVoronoi', (x, y - 1000), frame,
                   label='Edge speckles (millimetres)', Scale=120.0)
    g.link(noise_vec, spots.inputs['Vector'])
    shape = range_(g, spots.outputs['Distance'], 0.12, 0.30, (x + 200, y - 1000), frame,
                   1.0, 0.0, label='Edge spot radius', smooth=True)
    cell = g.node('ShaderNodeSeparateXYZ', (x + 200, y - 1250), frame)
    g.link(spots.outputs['Color'], cell.inputs[0])
    fields.shape, fields.cell = shape, cell.outputs['X']
    return fields


def _extent(g, context, width_field, width, limits, role):
    frame, (x, y) = context.frame, context.loc
    extent = range_(g, width_field, 0.30, 0.70, (x + 400, y), frame,
                    *limits, label=role + ' width modulation', smooth=True)
    return math_(g, 'MULTIPLY', extent, width, (x + 600, y), frame)


def _falloff(g, context, extent, lip_start, lip_end, role):
    frame, (x, y) = context.frame, context.loc
    fade_end = math_(g, 'ADD', lip_end, extent, (x + 800, y - 500), frame)
    band = range_(g, context.dist, lip_end, fade_end, (x + 800, y), frame, 1.0, 0.0,
                  label='edge ' + role + ' falloff', smooth=True)
    lip = range_(g, context.dist, lip_start, lip_end, (x + 800, y - 150), frame,
                 label={'line': 'Light edge lip', 'dust': 'Dust light lip'}[role], smooth=True)
    return band, lip


def _line_mask(g, context, fields, width, amount):
    frame, (x, y) = context.frame, context.loc
    extent = _extent(g, context, fields.width, width, context.recipe['line_limits'], 'line')
    lip_end = math_(g, 'MINIMUM', 0.006, math_(g, 'MULTIPLY', extent, 0.45,
                    (x + 600, y - 220), frame), (x + 800, y - 220), frame)
    lip_start = math_(g, 'MINIMUM', 0.002, math_(g, 'MULTIPLY', lip_end, 0.5,
                      (x + 600, y - 350), frame), (x + 800, y - 350), frame)
    band, lip = _falloff(g, context, extent, lip_start, lip_end, 'line')
    if context.join is not None:
        lip = math_(g, 'MAXIMUM', lip, context.join, (x + 1000, y - 150), frame)
        lip.node.label = 'Vertex setback bridge'
    profile = math_(g, 'MULTIPLY', band, lip, (x + 1000, y), frame)
    density = math_(g, 'MULTIPLY', band, 0.85, (x + 400, y - 1700), frame)
    keep = math_(g, 'LESS_THAN', fields.cell, density, (x + 600, y - 1700), frame)
    keep.node.label = 'Spot density fades with distance'
    speckle = math_(g, 'MULTIPLY', fields.shape, keep, (x + 800, y - 1700), frame)
    stain = math_(g, 'ADD', 0.25, math_(g, 'MULTIPLY', speckle, context.recipe['spot_contrast'],
                  (x + 1000, y - 1700), frame), (x + 1200, y - 1700), frame)
    profile = math_(g, 'MULTIPLY', profile, stain, (x + 1200, y), frame)
    patch = fields.presence
    if context.recipe['long_line']:
        patch = range_(g, fields.run, *OUTSIDE_LINE_PRESENCE, (x + 1000, y - 2100), frame,
                       label='Outside line coverage', smooth=True)
        patch = math_(g, 'ADD', 0.25, math_(g, 'MULTIPLY', patch, 0.75,
                      (x + 800, y - 2350), frame), (x + 1000, y - 2350), frame)
        patch = math_(g, 'MULTIPLY', patch, fields.strength, (x + 1200, y - 2350), frame)
        patch = math_(g, 'MAXIMUM', patch, math_(g, 'MULTIPLY', context.join, 0.55,
                      (x + 1200, y - 2550), frame), (x + 1400, y - 2350), frame)
        patch.node.label = 'Vertex coverage bridge'
    if context.recipe['boost'] is not None:
        profile = math_(g, 'MULTIPLY', profile, context.recipe['boost'], (x + 1200, y - 2100), frame)
        profile.node.label = 'Outside line strength boost'
    broken = math_(g, 'MULTIPLY', profile, patch, (x + 1400, y), frame)
    orientation = context.line_orientation if context.recipe['line_orientation'] is None else context.recipe['line_orientation']
    broken = math_(g, 'MULTIPLY', broken, orientation, (x + 1600, y), frame)
    return _finish_mask(g, context, broken, amount, 'line')


def _dust_mask(g, context, fields, width, amount):
    frame, (x, y) = context.frame, context.loc
    extent = _extent(g, context, fields.width_noise, width, (0.65, 1.6), 'dust')
    band, lip = _falloff(g, context, extent, 0.0, 0.002, 'dust')
    profile = math_(g, 'MULTIPLY', band, lip, (x + 1000, y), frame)
    patch = fields.presence
    if context.recipe['dust_floor'] is not None:
        patch = math_(g, 'ADD', context.recipe['dust_floor'], math_(g, 'MULTIPLY', fields.presence, context.recipe['dust_gain'],
                      (x + 1000, y - 1900), frame), (x + 1200, y - 1900), frame)
    broken = math_(g, 'MULTIPLY', profile, patch, (x + 1400, y), frame)
    broken = math_(g, 'MULTIPLY', broken, context.dust_orientation, (x + 1600, y), frame)
    return _finish_mask(g, context, broken, amount, 'dust')


def _finish_mask(g, context, broken, amount, role):
    frame, (x, y) = context.frame, context.loc
    if label := context.recipe['labels'][role]:
        broken.node.label = label
    if context.cap < 1.0:
        broken = math_(g, 'MINIMUM', broken, context.cap, (x + 1800, y), frame)
        broken.node.label = 'Corner ' + role + ' cap'
    mask = math_(g, 'MULTIPLY', broken, amount, (x + 2000, y), frame, clamp=True)
    mask.node.label = 'Edge ' + role + ' strength'
    return mask


EDGE_KINDS = {
    'outside': dict(context=_outside_context, long_line=True,
                    line_limits=OUTSIDE_LINE_WIDTH_LIMITS, spot_contrast=0.10,  # fine spot contrast
                    boost=OUTSIDE_LINE_BOOST, line_orientation=None, labels={'line': None, 'dust': None},
                    dust_floor=None, dust_gain=None),
    'corner': dict(context=_corner_context, long_line=False,
                   line_limits=(0.45, 2.4), spot_contrast=0.75,  # width multiples and spot contrast
                   boost=None, line_orientation=0.035, labels={'line': 'Corner line suppression', 'dust': None},  # weak line weight
                   dust_floor=0.35, dust_gain=0.65),  # connected dust pedestal and patch gain
}


def edge_dirt_masks(g, dist, line_width=LINE_WIDTH, dust_width=DUST_WIDTH, noise_vec=None,
                    line_amount=LINE_AMOUNT, dust_amount=DUST_AMOUNT,
                    noise_scale=9.0, frame=None, loc=(0, 0), mask_cap=1.0, kind='outside'):
    """Return line, dust and the reusable outside-vertex join (None for AO corners)."""
    if line_width <= 0 or dust_width <= 0:
        raise ValueError('edge dirt widths must be positive')
    context = SimpleNamespace(dist=dist, frame=frame, loc=loc, recipe=EDGE_KINDS[kind], cap=mask_cap)
    context.recipe['context'](g, context, line_width)
    fields = _noise_context(g, context, context.position if noise_vec is None else noise_vec, noise_scale)
    line = _line_mask(g, context, fields, line_width, line_amount)
    context.loc = (loc[0], loc[1] - 300)
    dust = _dust_mask(g, context, fields, dust_width, dust_amount)
    return line, dust, context.join


def corner_dirt_masks(g, line_width=LINE_WIDTH, dust_width=DUST_WIDTH,
                      line_amount=LINE_AMOUNT, dust_amount=DUST_AMOUNT,
                      frame=None, loc=(0, 0), corner_cap=CORNER_MASK_CAP):
    """Return shared masks using cross-object AO remapped to a distance-like metre field."""
    x, y = loc
    ao = g.node('ShaderNodeAmbientOcclusion', (x - 600, y), frame,
                label='Corner AO (cross-object)', Distance=AO_REACH)
    ao.inside = False
    ao.only_local = False
    ao.samples = 32  # cross-object occlusion rays
    # A perpendicular contact covers half the AO hemisphere.
    unit_dist = range_(g, ao.outputs['AO'], 0.5, 1.0, (x - 400, y), frame,
                       label='corner distance-like 0..1')
    dist = math_(g, 'MULTIPLY', unit_dist, AO_REACH, (x - 200, y), frame)
    return edge_dirt_masks(g, dist, line_width, dust_width, line_amount=line_amount,
                           dust_amount=dust_amount, frame=frame, loc=loc, mask_cap=corner_cap, kind='corner')[:2]


def _mix_color(g, a, b, factor, frame, loc, label, blend='MIX', data_type='RGBA'):
    node = g.node('ShaderNodeMix', loc, frame, label=label)
    node.data_type, node.blend_type = data_type, blend
    g._in(node.inputs['Factor'], factor)
    g._in(sock(node.inputs, 'A'), a)
    g._in(sock(node.inputs, 'B'), b)
    return sock(node.outputs, 'Result')


RGB_LUMINANCE = (0.2126, 0.7152, 0.0722)  # shared Cycles/LuxCore scene-linear luminance


def _relative_dust_color(g, color, dust, frame, loc):
    """Desaturate and gently darken albedo through the independent dust term."""
    x, y = loc
    luma = _vector(g, 'DOT_PRODUCT', color, None, (x - 220, y - 140), frame, label='Dust source luminance')
    luma.inputs[1].default_value = RGB_LUMINANCE
    desat = _mix_color(g, color, luma.outputs['Value'], 1.0 - DUST_SATURATION,
                       frame, (x, y), 'Dust relative desaturation')
    gain = _mix_color(g, desat, (*DUST_GAIN, 1), 1.0, frame, (x + 220, y),
                      'Dust relative darkening', blend='MULTIPLY')
    return _mix_color(g, color, gain, dust, frame, (x + 440, y), 'Dust relative albedo')


def dust_surface(g, surface, dust, frame=None, loc=(0, 0), line=None):
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
            value = g.node('ShaderNodeRGB', (loc[0] - 220, loc[1] - i * 250), frame,
                           label='Dust original albedo')
            value.outputs[0].default_value = target.default_value
            color = value.outputs[0]
        adjusted = _relative_dust_color(g, color, dust, frame, (loc[0], loc[1] - i * 250))
        if line is not None:
            gain = _mix_color(g, color, (LINE_GAIN, LINE_GAIN, LINE_GAIN, 1), 1.0, frame,
                              (loc[0] + 660, loc[1] - i * 250), 'Line relative darkening', blend='MULTIPLY')
            adjusted = _mix_color(g, adjusted, gain, line, frame,
                                  (loc[0] + 880, loc[1] - i * 250), 'Line relative albedo')
            roughness = target.node.inputs.get('Roughness')
            if roughness is not None:
                original = roughness.links[0].from_socket if roughness.is_linked else roughness.default_value
                rough = _mix_color(g, original, LINE_ROUGHNESS, line, frame,
                                   (loc[0] + 660, loc[1] - i * 250 - 140),
                                   'Line roughness (unchanged target)', data_type='FLOAT')
                g.link(rough, roughness)
        g.link(adjusted, target)
    return surface


def add_corner_dirt(mat, line_width=LINE_WIDTH, dust_width=DUST_WIDTH,
                    line_amount=LINE_AMOUNT, dust_amount=DUST_AMOUNT, corner_cap=CORNER_MASK_CAP):
    """Add independently switchable shared line/dust layers to a Cycles surface material."""
    g = G(mat.node_tree)
    existing = {role: next((n.outputs[0] for n in g.nt.nodes
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
    out = next(n for n in g.nt.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output)
    surface = out.inputs['Surface'].links[0].from_socket
    result = dust_surface(g, surface, dust, frame, (1400, 0), line=line)
    g.link(result, out.inputs['Surface'])
    return mat

