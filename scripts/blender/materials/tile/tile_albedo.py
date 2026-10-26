"""Tile colour: face and grout albedo, per-tile tint, dust in the corners, and the macro variation.

Works on the node-graph builder `a` (materials.tile.tile_nodes._Graph); every value here is a socket or
an expression of sockets, so the result stays in the shader.
"""
from materials.tile.tile_finish import gate


def desaturate(a, color, saturation):
    """Mix RGB toward Rec.709 luminance without changing its measured luminance."""
    luminance = a.v('DOT_PRODUCT', color, (.2126, .7152, .0722))
    gray = a.xyz(luminance, luminance, luminance)
    amount = a.xyz(saturation, saturation, saturation)
    return a.v('ADD', gray, a.v('MULTIPLY', a.v('SUBTRACT', color, gray), amount))


def face_tone(a, i):
    """Reduce scan contrast and saturation, then normalize its adjusted linear mean."""
    contrast = a.xyz(i['Face Contrast'], i['Face Contrast'], i['Face Contrast'])
    color = a.v('ADD', i['Face Mean'], a.v('MULTIPLY',
                   a.v('SUBTRACT', i['Face Color'], i['Face Mean']), contrast))
    color = desaturate(a, color, i['Face Saturation'])
    mean = desaturate(a, i['Face Mean'], i['Face Saturation'])
    return a.v('MULTIPLY', color, a.v('DIVIDE', i['Body Albedo'], mean))


def albedo(a, i, dust, pits, pinholes):
    """Build normalized face and grout albedos plus signed macro variation."""
    m, v = a.m, a.v
    cloud = m('ADD', 1, m('MULTIPLY', a.amplitude(i['World'], 18), .03))
    normalized = face_tone(a, i)
    normalized = v('MINIMUM', normalized, (.9, .9, .9))
    # Vector mix expressed as add/multiply to avoid hidden Mix sockets.
    color = v('ADD', v('MULTIPLY', normalized, a.xyz(i['Has Face'], i['Has Face'], i['Has Face'])),
              v('MULTIPLY', i['Body Albedo'], a.xyz(
                  m('MULTIPLY', m('SUBTRACT', 1, i['Has Face']), cloud),
                  m('MULTIPLY', m('SUBTRACT', 1, i['Has Face']), cloud),
                  m('MULTIPLY', m('SUBTRACT', 1, i['Has Face']), cloud))))
    # Sum of two independent uniforms gives a triangular, mean-centered lightness spread.
    tint = m('SUBTRACT', m('ADD', a.rand(i['Cell'], (17, 31, 47)),
                           a.rand(i['Cell'], (349, 367, 389))), 1)
    tint_factor = m('ADD', 1, gate(a, i, 'variation', m('MULTIPLY', i['Tint Var'], tint)))
    warmth = gate(a, i, 'variation', m('MULTIPLY', m('MULTIPLY', i['Tint Var'], .25),
                  m('SUBTRACT', m('MULTIPLY', a.rand(i['Cell'], (401, 419, 439)), 2), 1)))
    color = v('MULTIPLY', color, a.xyz(m('ADD', 1, warmth), 1, m('SUBTRACT', 1, warmth)))
    macro_delta = gate(a, i, 'macro', m('MULTIPLY', i['Macro'], a.amplitude(i['World'], 1/3)))
    macro = m('ADD', 1, macro_delta)
    darken = m('SUBTRACT', 1, m('MULTIPLY', dust, .5))
    # Iron spots darken; pinholes brighten instead, sharing the same final albedo cap.
    speck_tone = m('ADD', m('SUBTRACT', 1, m('MULTIPLY', m('SUBTRACT', pits, pinholes), .6)),
                   m('MULTIPLY', pinholes, .15))
    factor = m('MULTIPLY', m('MULTIPLY', tint_factor, macro), m('MULTIPLY', darken, speck_tone))
    color = v('MINIMUM', v('MULTIPLY', color, a.xyz(factor, factor, factor)), (.9, .9, .9))
    marker = a.node('ShaderNodeVectorMath', operation='MULTIPLY')
    marker.name = 'TileFaceAlbedo'
    a.put(color, marker.inputs[0]); marker.inputs[1].default_value = (1, 1, 1)
    grout_factor = m('MULTIPLY', darken, macro)
    grout_color = v('MULTIPLY', i['Grout Albedo'], a.xyz(grout_factor, grout_factor, grout_factor))
    return marker.outputs['Vector'], grout_color, macro_delta


def dust(a, i):
    """Build patchy corner dust with independently varying physical width."""
    m, v = a.m, a.v
    # Dust reaches zero in broad clean patches.
    patch_noise = a.smooth(a.noise(i['World'], 2.5), .45, .65)
    width_noise = a.amplitude(v('ADD', i['World'], (13, 29, 43)), 2.)
    width = m('MULTIPLY', i['Dust Width'], m('ADD', .9, m('MULTIPLY', .6, width_noise)))
    dust_band = m('SUBTRACT', 1, a.smooth(m('ADD', i['Edge'], m('MULTIPLY', i['Joint Width'], .5)),
                                               0, m('MAXIMUM', width, 1e-9)))
    dust = gate(a, i, 'dust', m('MULTIPLY', i['Dust'], m('MULTIPLY', dust_band, patch_noise)))
    return dust
