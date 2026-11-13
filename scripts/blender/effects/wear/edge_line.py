"""Narrow connected edge-line shading profile."""
from effects.wear.edge_profile import (OUTSIDE_LINE_PRESENCE, _extent, _falloff, _finish_mask)

def _line_mask(graph, context, fields, width, amount):
    frame, (x, y) = context.frame, context.loc
    extent = _extent(graph, context, fields.width, width, context.recipe['line_limits'], 'line')
    lip_end = graph.math('MINIMUM', 0.006, graph.math('MULTIPLY', extent, 0.45,
                    (x + 600, y - 220), frame), (x + 800, y - 220), frame)
    lip_start = graph.math('MINIMUM', 0.002, graph.math('MULTIPLY', lip_end, 0.5,
                      (x + 600, y - 350), frame), (x + 800, y - 350), frame)
    band, lip = _falloff(graph, context, extent, lip_start, lip_end, 'line')
    if context.join is not None:
        lip = graph.math('MAXIMUM', lip, context.join, (x + 1000, y - 150), frame)
        lip.node.label = 'Vertex setback bridge'
    profile = graph.math('MULTIPLY', band, lip, (x + 1000, y), frame)
    density = graph.math('MULTIPLY', band, 0.85, (x + 400, y - 1700), frame)
    keep = graph.math('LESS_THAN', fields.cell, density, (x + 600, y - 1700), frame)
    keep.node.label = 'Spot density fades with distance'
    speckle = graph.math('MULTIPLY', fields.shape, keep, (x + 800, y - 1700), frame)
    stain = graph.math('ADD', 0.25, graph.math('MULTIPLY', speckle, context.recipe['spot_contrast'],
                  (x + 1000, y - 1700), frame), (x + 1200, y - 1700), frame)
    profile = graph.math('MULTIPLY', profile, stain, (x + 1200, y), frame)
    patch = fields.presence
    if context.recipe['long_line']:
        patch = graph.map_range(fields.run, *OUTSIDE_LINE_PRESENCE, (x + 1000, y - 2100), frame=frame,
                       label='Outside line coverage', smooth=True)
        patch = graph.math('ADD', 0.25, graph.math('MULTIPLY', patch, 0.75,
                      (x + 800, y - 2350), frame), (x + 1000, y - 2350), frame)
        patch = graph.math('MULTIPLY', patch, fields.strength, (x + 1200, y - 2350), frame)
        patch = graph.math('MAXIMUM', patch, graph.math('MULTIPLY', context.join, 0.55,
                      (x + 1200, y - 2550), frame), (x + 1400, y - 2350), frame)
        patch.node.label = 'Vertex coverage bridge'
    if context.recipe['boost'] is not None:
        profile = graph.math('MULTIPLY', profile, context.recipe['boost'], (x + 1200, y - 2100), frame)
        profile.node.label = 'Outside line strength boost'
    broken = graph.math('MULTIPLY', profile, patch, (x + 1400, y), frame)
    orientation = context.line_orientation if context.recipe['line_orientation'] is None else context.recipe['line_orientation']
    broken = graph.math('MULTIPLY', broken, orientation, (x + 1600, y), frame)
    return _finish_mask(graph, context, broken, amount, 'line')
