"""Tile relief height: rounded shoulders, tilt, waviness, lippage and pit relief, in metres.

Turning the profile, tilt, wave or lippage switch off removes that part of the relief.
"""
import math

from materials.tile.tile_finish import gate


def height(graph, inputs, pits, pinholes):
    """Combine metre-valued shoulders, tilt, wave and pit relief."""
    m, v = graph.math, graph.vector_math
    tile_size = graph.combine_xyz(inputs['Tile W'], inputs['Tile H'], 0)
    tilt = graph.hash_noise(inputs['Cell'], (113, 137, 157))
    direction = m('MULTIPLY', graph.hash_noise(inputs['Cell'], (179, 197, 211)), math.tau)
    # Round shoulder, clamped to the grout floor; turning profile off removes both.
    r = m('MAXIMUM', inputs['Edge Radius'], 0)
    e = m('MINIMUM', m('MAXIMUM', inputs['Edge'], 0), r)
    square = m('MULTIPLY', m('SUBTRACT', r, e), m('SUBTRACT', r, e))
    shoulder = m('SUBTRACT', m('SQRT', m('MAXIMUM', m('SUBTRACT', m('MULTIPLY', r, r), square), 0)), r)
    floor = m('MULTIPLY', inputs['Recess'], -1)
    shoulder = m('MAXIMUM', shoulder, floor)
    joint_mix = m('MAXIMUM', inputs['Joint'], m('SUBTRACT', 1, graph.smooth(inputs['Edge'], 0, .0003)))
    profile = gate(graph, inputs, 'profile', graph.mix(joint_mix, shoulder, floor))
    uv_center = v('MULTIPLY', v('SUBTRACT', inputs['Tile UV'], (.5, .5, 0)), tile_size)
    slope = m('TANGENT', m('MULTIPLY', inputs['Tilt Deg'], m('SUBTRACT', m('MULTIPLY', tilt, 2), 1)))
    tilt_height = gate(graph, inputs, 'tilt', m('MULTIPLY', v('DOT_PRODUCT', uv_center, graph.combine_xyz(m('COSINE', direction), m('SINE', direction))), slope))
    wave = gate(graph, inputs, 'wave', m('MULTIPLY', inputs['Wave Amp'], graph.amplitude(inputs['World'], m('DIVIDE', 1, inputs['Tile H']))))
    face_height = m('ADD', m('ADD', tilt_height, wave),
                    m('SUBTRACT', m('MULTIPLY', m('MULTIPLY', inputs['Face Height'], inputs['Face Contrast']), .0002), m('ADD', m('MULTIPLY', pits, .0001), m('MULTIPLY', pinholes, .00005))))
    lippage = gate(graph, inputs, 'tilt', m('MULTIPLY', inputs['Lippage'],
                   m('SUBTRACT', m('MULTIPLY', graph.hash_noise(inputs['Cell'], (457, 479, 499)), 2), 1)))
    # The rounded shoulder interpolates from the fixed grout floor to the shifted face.
    rise = m('MINIMUM', m('MAXIMUM', m('DIVIDE', m('SUBTRACT', shoulder, floor),
                     m('MAXIMUM', inputs['Recess'], 1e-9)), 0), 1)
    rise = m('MAXIMUM', rise, m('LESS_THAN', inputs['Recess'], 1e-9))
    lip_weight = graph.mix(inputs['profile On'], 1, rise)
    face_height = m('ADD', face_height, m('MULTIPLY', lippage, lip_weight))
    height = m('ADD', profile, m('MULTIPLY', m('SUBTRACT', 1, joint_mix), face_height))
    return height, joint_mix, face_height
