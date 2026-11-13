"""Narrow connected edge-line shading profile."""
from effects.wear.nodes import math_, range_
from effects.wear.edge_profile import (OUTSIDE_LINE_PRESENCE, _extent, _falloff, _finish_mask)

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
