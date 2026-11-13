"""Tile shading: coated clay face and grout, mixed by the joint mask, with a world-metre bump field.
"""
from materials.tile.tile_finish import gate


def surface_shader(a, i, color, grout_color, dust, macro_delta, height, joint_mix):
    """Mix coated clay and grout using a world-metre bump field."""
    m, v = a.math, a.vector_math
    bump = a.node('ShaderNodeBump')
    bump.name = 'TileBump'
    bump.inputs['Strength'].default_value = 1; bump.inputs['Distance'].default_value = 1
    a.link_or_set(height, bump.inputs['Height'])
    face = a.node('ShaderNodeBsdfPrincipled')
    a.link_or_set(color, face.inputs['Base Color'])
    a.link_or_set(m('MINIMUM', m('MAXIMUM', m('ADD', .5, m('MULTIPLY', macro_delta, .5)), 0), 1), face.inputs['Roughness'])
    face.inputs['Specular IOR Level'].default_value = 0
    face.inputs['Coat Weight'].default_value = 1
    a.link_or_set(i['Coat IOR'], face.inputs['Coat IOR'])
    rough = a.hash_noise(i['Cell'], (59, 83, 101))
    gloss = m('ADD', i['Coat Rough'], gate(a, i, 'variation', m('MULTIPLY', i['Rough Var'], m('SUBTRACT', m('MULTIPLY', rough, 2), 1))))
    gloss = m('ADD', gloss, m('MULTIPLY', m('MULTIPLY', m('SUBTRACT', i['Face Rough'], i['Rough Mean']), i['Face Contrast']), .3))
    gloss = m('ADD', gloss, m('MULTIPLY', macro_delta, .5))
    a.link_or_set(m('MINIMUM', m('MAXIMUM', m('ADD', gloss, m('MULTIPLY', dust, .3)), 0), 1), face.inputs['Coat Roughness'])
    grout = a.node('ShaderNodeBsdfPrincipled')
    a.link_or_set(grout_color, grout.inputs['Base Color'])
    a.link_or_set(m('MINIMUM', m('MAXIMUM', m('ADD', m('ADD', i['Grout Rough'], m('MULTIPLY', dust, .1)), m('MULTIPLY', macro_delta, .5)), 0), 1), grout.inputs['Roughness'])
    grout.inputs['Coat Weight'].default_value = 0
    for bsdf in (face, grout):
        a.link_or_set(bump.outputs['Normal'], bsdf.inputs['Normal'])
    a.link_or_set(bump.outputs['Normal'], face.inputs['Coat Normal'])
    mix = a.node('ShaderNodeMixShader')
    for val, socket in zip((joint_mix, face.outputs['BSDF'], grout.outputs['BSDF']), mix.inputs):
        a.link_or_set(val, socket)
    return mix.outputs[0]
