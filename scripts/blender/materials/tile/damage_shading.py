"""Damage shading; canonical implementation behind tile_damage."""

def damage_shaders(graph, inputs, intact, color, height, damage_inputs):
    """Shade exposed clay, engobe and dirt independently of the coated glaze."""
    m, v = graph.math, graph.vector_math
    # The face Principled is the first input of tile_surface's face/grout mix.
    # Change only its pigment: all coat inputs and the grout shader stay intact.
    face = intact.node.inputs[1].links[0].from_node
    attenuation = m('SUBTRACT',1,damage_inputs['Dirt'])
    graph.link_or_set(v('MULTIPLY',color,graph.combine_xyz(attenuation,attenuation,attenuation)),face.inputs['Base Color'])
    grain = graph.amplitude(graph.vector_math('ADD', inputs['World'], graph.hash_noise(inputs['Cell'], (563, 569, 571), True)), 1/.00045)
    grog = m('GREATER_THAN', graph.noise_texture(inputs['World'], 1/.0005), .7)
    iron = m('LESS_THAN', graph.noise_texture(graph.vector_math('ADD', inputs['World'], (17, 23, 31)), 1/.0004), .28)
    tone = m('MULTIPLY', m('ADD', .85, m('MULTIPLY', .3, graph.hash_noise(inputs['Cell'], (521, 541, 557)))),
             m('ADD', 1, m('MULTIPLY', .2, grain)))
    # Red-firing body, linear; slip and body colours become knobs with the chip work (chips are WIP).
    clay_color = v('MULTIPLY', (.30, .17, .10), graph.combine_xyz(tone, tone, tone))
    specks = m('MULTIPLY', m('ADD', 1, m('MULTIPLY', .4, grog)), m('SUBTRACT', 1, m('MULTIPLY', .35, iron)))
    clay_color = v('MULTIPLY', clay_color, graph.combine_xyz(specks, specks, specks))
    # The existing dust colour is the same physical deposit inside the deepest bowls.
    deposit = m('MULTIPLY', m('MULTIPLY', inputs['Dust'], inputs['dust On']),
                m('MULTIPLY', .2, graph.smooth(damage_inputs['Chip Depth Out'], .0015, .0025)))
    clay_color = v('ADD', v('MULTIPLY', clay_color, graph.combine_xyz(m('SUBTRACT', 1, deposit), m('SUBTRACT', 1, deposit), m('SUBTRACT', 1, deposit))),
                   v('MULTIPLY', inputs['Grout Albedo'], graph.combine_xyz(deposit, deposit, deposit)))
    bump = graph.node('ShaderNodeBump'); bump.name = 'DamageBump'
    bump.inputs['Distance'].default_value = 1
    graph.link_or_set(height, bump.inputs['Height'])
    fine = graph.node('ShaderNodeBump'); fine.inputs['Distance'].default_value = .00003
    fine.name = 'ClayGrainBump'
    graph.link_or_set(graph.noise_texture(inputs['World'], 1/.0001), fine.inputs['Height']); graph.link_or_set(bump.outputs['Normal'], fine.inputs['Normal'])
    def material(base, rough, normal):
        bsdf = graph.node('ShaderNodeBsdfPrincipled')
        graph.link_or_set(base, bsdf.inputs['Base Color']); bsdf.inputs['Roughness'].default_value = rough
        bsdf.inputs['Coat Weight'].default_value = 0
        graph.link_or_set(normal, bsdf.inputs['Normal'])
        return bsdf.outputs['BSDF']
    def mix(mask, first, second):
        node = graph.node('ShaderNodeMixShader')
        for value, socket in zip((mask, first, second), node.inputs):
            graph.link_or_set(value, socket)
        return node.outputs[0]
    shader = mix(damage_inputs['Engobe'], intact, material((.70, .70, .70), .9, bump.outputs['Normal']))
    shader = mix(damage_inputs['Body'], shader, material(clay_color, .9, fine.outputs['Normal']))
    dark = v('MULTIPLY', color, (.25, .25, .25))
    return mix(damage_inputs['Crack'], shader, material(dark, .9, bump.outputs['Normal']))
