"""Tile shading: coated clay face and grout, mixed by the joint mask, with a world-metre bump field.
"""
from materials.tile.tile_finish import gate


def bsdfs(a, i, color, grout_color, dust, macro_delta, height, joint_mix):
    """Mix coated clay and grout using a world-metre bump field."""
    m, v = a.m, a.v
    bump = a.node('ShaderNodeBump')
    bump.name = 'TileBump'
    bump.inputs['Strength'].default_value = 1; bump.inputs['Distance'].default_value = 1
    a.put(height, bump.inputs['Height'])
    face = a.node('ShaderNodeBsdfPrincipled')
    a.put(color, face.inputs['Base Color'])
    a.put(m('MINIMUM', m('MAXIMUM', m('ADD', .5, m('MULTIPLY', macro_delta, .5)), 0), 1), face.inputs['Roughness'])
    face.inputs['Specular IOR Level'].default_value = 0
    face.inputs['Coat Weight'].default_value = 1
    a.put(i['Coat IOR'], face.inputs['Coat IOR'])
    rough = a.rand(i['Cell'], (59, 83, 101))
    gloss = m('ADD', i['Coat Rough'], gate(a, i, 'variation', m('MULTIPLY', i['Rough Var'], m('SUBTRACT', m('MULTIPLY', rough, 2), 1))))
    gloss = m('ADD', gloss, m('MULTIPLY', m('MULTIPLY', m('SUBTRACT', i['Face Rough'], i['Rough Mean']), i['Face Contrast']), .3))
    gloss = m('ADD', gloss, m('MULTIPLY', macro_delta, .5))
    a.put(m('MINIMUM', m('MAXIMUM', m('ADD', gloss, m('MULTIPLY', dust, .3)), 0), 1), face.inputs['Coat Roughness'])
    grout = a.node('ShaderNodeBsdfPrincipled')
    a.put(grout_color, grout.inputs['Base Color'])
    a.put(m('MINIMUM', m('MAXIMUM', m('ADD', m('ADD', i['Grout Rough'], m('MULTIPLY', dust, .1)), m('MULTIPLY', macro_delta, .5)), 0), 1), grout.inputs['Roughness'])
    grout.inputs['Coat Weight'].default_value = 0
    for bsdf in (face, grout):
        a.put(bump.outputs['Normal'], bsdf.inputs['Normal'])
    a.put(bump.outputs['Normal'], face.inputs['Coat Normal'])
    mix = a.node('ShaderNodeMixShader')
    for val, socket in zip((joint_mix, face.outputs['BSDF'], grout.outputs['BSDF']), mix.inputs):
        a.put(val, socket)
    return mix.outputs[0]
