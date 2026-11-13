"""Tile shading: coated clay face and grout, mixed by the joint mask, with a world-metre bump field.
"""
from materials.tile.tile_finish import gate


def surface_shader(graph, inputs, color, grout_color, dust, macro_delta, height, joint_mix):
    """Mix coated clay and grout using graph world-metre bump field."""
    m, v = graph.math, graph.vector_math
    bump = graph.node('ShaderNodeBump')
    bump.name = 'TileBump'
    bump.inputs['Strength'].default_value = 1; bump.inputs['Distance'].default_value = 1
    graph.link_or_set(height, bump.inputs['Height'])
    face = graph.node('ShaderNodeBsdfPrincipled')
    graph.link_or_set(color, face.inputs['Base Color'])
    graph.link_or_set(m('MINIMUM', m('MAXIMUM', m('ADD', .5, m('MULTIPLY', macro_delta, .5)), 0), 1), face.inputs['Roughness'])
    face.inputs['Specular IOR Level'].default_value = 0
    face.inputs['Coat Weight'].default_value = 1
    graph.link_or_set(inputs['Coat IOR'], face.inputs['Coat IOR'])
    rough = graph.hash_noise(inputs['Cell'], (59, 83, 101))
    gloss = m('ADD', inputs['Coat Rough'], gate(graph, inputs, 'variation', m('MULTIPLY', inputs['Rough Var'], m('SUBTRACT', m('MULTIPLY', rough, 2), 1))))
    gloss = m('ADD', gloss, m('MULTIPLY', m('MULTIPLY', m('SUBTRACT', inputs['Face Rough'], inputs['Rough Mean']), inputs['Face Contrast']), .3))
    gloss = m('ADD', gloss, m('MULTIPLY', macro_delta, .5))
    graph.link_or_set(m('MINIMUM', m('MAXIMUM', m('ADD', gloss, m('MULTIPLY', dust, .3)), 0), 1), face.inputs['Coat Roughness'])
    grout = graph.node('ShaderNodeBsdfPrincipled')
    graph.link_or_set(grout_color, grout.inputs['Base Color'])
    graph.link_or_set(m('MINIMUM', m('MAXIMUM', m('ADD', m('ADD', inputs['Grout Rough'], m('MULTIPLY', dust, .1)), m('MULTIPLY', macro_delta, .5)), 0), 1), grout.inputs['Roughness'])
    grout.inputs['Coat Weight'].default_value = 0
    for bsdf in (face, grout):
        graph.link_or_set(bump.outputs['Normal'], bsdf.inputs['Normal'])
    graph.link_or_set(bump.outputs['Normal'], face.inputs['Coat Normal'])
    mix = graph.node('ShaderNodeMixShader')
    for val, socket in zip((joint_mix, face.outputs['BSDF'], grout.outputs['BSDF']), mix.inputs):
        graph.link_or_set(val, socket)
    return mix.outputs[0]
