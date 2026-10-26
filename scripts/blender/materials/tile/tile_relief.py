"""Tile relief height: rounded shoulders, tilt, waviness, lippage and pit relief, in metres.

Turning the profile, tilt, wave or lippage switch off removes that part of the relief.
"""
import math

from materials.tile.tile_finish import gate


def height(a, i, pits, pinholes):
    """Combine metre-valued shoulders, tilt, wave and pit relief."""
    m, v = a.m, a.v
    tile_size = a.xyz(i['Tile W'], i['Tile H'], 0)
    tilt = a.rand(i['Cell'], (113, 137, 157))
    direction = m('MULTIPLY', a.rand(i['Cell'], (179, 197, 211)), math.tau)
    # Round shoulder, clamped to the grout floor; turning profile off removes both.
    r = m('MAXIMUM', i['Edge Radius'], 0)
    e = m('MINIMUM', m('MAXIMUM', i['Edge'], 0), r)
    square = m('MULTIPLY', m('SUBTRACT', r, e), m('SUBTRACT', r, e))
    shoulder = m('SUBTRACT', m('SQRT', m('MAXIMUM', m('SUBTRACT', m('MULTIPLY', r, r), square), 0)), r)
    floor = m('MULTIPLY', i['Recess'], -1)
    shoulder = m('MAXIMUM', shoulder, floor)
    joint_mix = m('MAXIMUM', i['Joint'], m('SUBTRACT', 1, a.smooth(i['Edge'], 0, .0003)))
    profile = gate(a, i, 'profile', a.mix(joint_mix, shoulder, floor))
    uv_center = v('MULTIPLY', v('SUBTRACT', i['Tile UV'], (.5, .5, 0)), tile_size)
    slope = m('TANGENT', m('MULTIPLY', i['Tilt Deg'], m('SUBTRACT', m('MULTIPLY', tilt, 2), 1)))
    tilt_height = gate(a, i, 'tilt', m('MULTIPLY', v('DOT_PRODUCT', uv_center, a.xyz(m('COSINE', direction), m('SINE', direction))), slope))
    wave = gate(a, i, 'wave', m('MULTIPLY', i['Wave Amp'], a.amplitude(i['World'], m('DIVIDE', 1, i['Tile H']))))
    face_height = m('ADD', m('ADD', tilt_height, wave),
                    m('SUBTRACT', m('MULTIPLY', m('MULTIPLY', i['Face Height'], i['Face Contrast']), .0002), m('ADD', m('MULTIPLY', pits, .0001), m('MULTIPLY', pinholes, .00005))))
    lippage = gate(a, i, 'tilt', m('MULTIPLY', i['Lippage'],
                   m('SUBTRACT', m('MULTIPLY', a.rand(i['Cell'], (457, 479, 499)), 2), 1)))
    # The rounded shoulder interpolates from the fixed grout floor to the shifted face.
    rise = m('MINIMUM', m('MAXIMUM', m('DIVIDE', m('SUBTRACT', shoulder, floor),
                     m('MAXIMUM', i['Recess'], 1e-9)), 0), 1)
    rise = m('MAXIMUM', rise, m('LESS_THAN', i['Recess'], 1e-9))
    lip_weight = a.mix(i['profile On'], 1, rise)
    face_height = m('ADD', face_height, m('MULTIPLY', lippage, lip_weight))
    height = m('ADD', profile, m('MULTIPLY', m('SUBTRACT', 1, joint_mix), face_height))
    return height, joint_mix, face_height
