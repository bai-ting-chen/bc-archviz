"""Shared distance falloffs and noise context for edge line and dust."""
from types import SimpleNamespace
from effects.wear.nodes import math_, noise, range_

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
