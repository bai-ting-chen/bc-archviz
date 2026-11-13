"""Iron specks and pinholes on the glaze: clustered, irregular, varied-size dots from a warped Voronoi.

Returns a dot mask and a pinhole mask. Iron spots darken the albedo; pinholes brighten it (tile_albedo).
"""
import math

from materials.tile.tile_finish import gate


def specks(graph, inputs):
    """Build clustered, irregular, varied-size iron spots and lighter pinhole masks."""
    m, v = graph.math, graph.vector_math
    fraction = m('MAXIMUM', m('MULTIPLY', inputs['Specks'], .01), 0)
    # Diameter ratio = .3 + .7*U^2: most dots small; E[ratio^2] = .328.
    # The symmetric smooth noise field retains half the candidate dots on average.
    # Compensate both area losses in center density, preserving mean percent coverage.
    base_threshold = m('SQRT', m('DIVIDE', fraction, math.pi * .328 * .5))
    radius = m('MAXIMUM', m('MULTIPLY', inputs['Speck Size'], .5), 1e-9)
    scale = m('DIVIDE', base_threshold, radius)
    surface = v('MULTIPLY', inputs['Tile UV'], graph.combine_xyz(inputs['Tile W'], inputs['Tile H'], 0))
    phase = graph.hash_noise(inputs['Cell'], (229, 251, 269), True)
    surface = v('ADD', surface, phase)
    warp_noise = graph.noise_texture(surface, m('DIVIDE', 1, m('MAXIMUM', inputs['Speck Size'], 1e-9)))
    channels = graph.separate_xyz(warp_noise.node.outputs['Color'])
    warp = []
    for channel in channels[:2]:
        signed = m('MINIMUM', m('MAXIMUM', m('DIVIDE', m('SUBTRACT', channel, .5), .1), -1), 1)
        warp.append(m('MULTIPLY', signed, m('MULTIPLY', inputs['Speck Size'], .3)))
    warped = v('ADD', surface, graph.combine_xyz(warp[0], warp[1], 0))
    xy = graph.separate_xyz(warped)
    vor = graph.node('ShaderNodeTexVoronoi', voronoi_dimensions='2D', feature='F1', distance='EUCLIDEAN')
    graph.link_or_set(graph.combine_xyz(xy[0], xy[1]), vor.inputs['Vector'])
    graph.link_or_set(scale, vor.inputs['Scale'])
    random = graph.separate_xyz(vor.outputs['Color'])
    diameter_ratio = m('ADD', .3, m('MULTIPLY', .7, m('MULTIPLY', random[0], random[0])))
    threshold = m('MULTIPLY', base_threshold, diameter_ratio)
    density = graph.smooth(graph.noise_texture(inputs['World'], 1/.15), .4, .6)
    # Thin whole dots with the independent blue hash: patchiness changes coverage,
    # rather than shrinking all dots in a sparse patch below their diameter range.
    retained = m('LESS_THAN', random[2], density)
    mask = gate(graph, inputs, 'specks', m('MULTIPLY', retained, m('LESS_THAN', vor.outputs['Distance'], threshold)))
    pinholes = m('MULTIPLY', mask, m('LESS_THAN', random[1], .2))
    return mask, pinholes
