"""Tile colour: face and grout albedo, per-tile tint, dust in the corners, and the macro variation.

Works on the node-graph builder `a` (materials.tile.tile_nodes._TileGraph); every value here is a socket or
an expression of sockets, so the result stays in the shader.
"""
from materials.tile.tile_finish import gate


def desaturate(graph, color, saturation):
    """Mix RGB toward Rec.709 luminance without changing its measured luminance."""
    luminance = graph.vector_math('DOT_PRODUCT', color, (.2126, .7152, .0722))
    gray = graph.combine_xyz(luminance, luminance, luminance)
    amount = graph.combine_xyz(saturation, saturation, saturation)
    return graph.vector_math('ADD', gray, graph.vector_math('MULTIPLY', graph.vector_math('SUBTRACT', color, gray), amount))


def face_tone(graph, inputs):
    """Reduce scan contrast and saturation, then normalize its adjusted linear mean."""
    contrast = graph.combine_xyz(inputs['Face Contrast'], inputs['Face Contrast'], inputs['Face Contrast'])
    color = graph.vector_math('ADD', inputs['Face Mean'], graph.vector_math('MULTIPLY',
                   graph.vector_math('SUBTRACT', inputs['Face Color'], inputs['Face Mean']), contrast))
    color = desaturate(graph, color, inputs['Face Saturation'])
    mean = desaturate(graph, inputs['Face Mean'], inputs['Face Saturation'])
    return graph.vector_math('MULTIPLY', color, graph.vector_math('DIVIDE', inputs['Body Albedo'], mean))


def albedo(graph, inputs, dust, pits, pinholes):
    """Build normalized face and grout albedos plus signed macro variation."""
    m, v = graph.math, graph.vector_math
    cloud = m('ADD', 1, m('MULTIPLY', graph.amplitude(inputs['World'], 18), .03))
    normalized = face_tone(graph, inputs)
    normalized = v('MINIMUM', normalized, (.9, .9, .9))
    # Vector mix expressed as add/multiply to avoid hidden Mix sockets.
    color = v('ADD', v('MULTIPLY', normalized, graph.combine_xyz(inputs['Has Face'], inputs['Has Face'], inputs['Has Face'])),
              v('MULTIPLY', inputs['Body Albedo'], graph.combine_xyz(
                  m('MULTIPLY', m('SUBTRACT', 1, inputs['Has Face']), cloud),
                  m('MULTIPLY', m('SUBTRACT', 1, inputs['Has Face']), cloud),
                  m('MULTIPLY', m('SUBTRACT', 1, inputs['Has Face']), cloud))))
    # Sum of two independent uniforms gives a triangular, mean-centered lightness spread.
    tint = m('SUBTRACT', m('ADD', graph.hash_noise(inputs['Cell'], (17, 31, 47)),
                           graph.hash_noise(inputs['Cell'], (349, 367, 389))), 1)
    tint_factor = m('ADD', 1, gate(graph, inputs, 'variation', m('MULTIPLY', inputs['Tint Var'], tint)))
    warmth = gate(graph, inputs, 'variation', m('MULTIPLY', m('MULTIPLY', inputs['Tint Var'], .25),
                  m('SUBTRACT', m('MULTIPLY', graph.hash_noise(inputs['Cell'], (401, 419, 439)), 2), 1)))
    color = v('MULTIPLY', color, graph.combine_xyz(m('ADD', 1, warmth), 1, m('SUBTRACT', 1, warmth)))
    macro_delta = gate(graph, inputs, 'macro', m('MULTIPLY', inputs['Macro'], graph.amplitude(inputs['World'], 1/3)))
    macro = m('ADD', 1, macro_delta)
    darken = m('SUBTRACT', 1, m('MULTIPLY', dust, .5))
    # Iron spots darken; pinholes brighten instead, sharing the same final albedo cap.
    speck_tone = m('ADD', m('SUBTRACT', 1, m('MULTIPLY', m('SUBTRACT', pits, pinholes), .6)),
                   m('MULTIPLY', pinholes, .15))
    factor = m('MULTIPLY', m('MULTIPLY', tint_factor, macro), m('MULTIPLY', darken, speck_tone))
    color = v('MINIMUM', v('MULTIPLY', color, graph.combine_xyz(factor, factor, factor)), (.9, .9, .9))
    marker = graph.node('ShaderNodeVectorMath', operation='MULTIPLY')
    marker.name = 'TileFaceAlbedo'
    graph.link_or_set(color, marker.inputs[0]); marker.inputs[1].default_value = (1, 1, 1)
    grout_factor = m('MULTIPLY', darken, macro)
    grout_color = v('MULTIPLY', inputs['Grout Albedo'], graph.combine_xyz(grout_factor, grout_factor, grout_factor))
    return marker.outputs['Vector'], grout_color, macro_delta


def dust(graph, inputs):
    """Build patchy corner dust with independently varying physical width."""
    m, v = graph.math, graph.vector_math
    # Dust reaches zero in broad clean patches.
    patch_noise = graph.smooth(graph.noise_texture(inputs['World'], 2.5), .45, .65)
    width_noise = graph.amplitude(v('ADD', inputs['World'], (13, 29, 43)), 2.)
    width = m('MULTIPLY', inputs['Dust Width'], m('ADD', .9, m('MULTIPLY', .6, width_noise)))
    dust_band = m('SUBTRACT', 1, graph.smooth(m('ADD', inputs['Edge'], m('MULTIPLY', inputs['Joint Width'], .5)),
                                               0, m('MAXIMUM', width, 1e-9)))
    dust = gate(graph, inputs, 'dust', m('MULTIPLY', inputs['Dust'], m('MULTIPLY', dust_band, patch_noise)))
    return dust
