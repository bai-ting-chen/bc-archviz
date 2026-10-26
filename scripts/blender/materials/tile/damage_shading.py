"""Damage shading; canonical implementation behind tile_damage."""

def damage_bsdfs(a, i, intact, color, height, d):
    """Shade exposed clay, engobe and dirt independently of the coated glaze."""
    m, v = a.m, a.v
    # The face Principled is the first input of tile_surface's face/grout mix.
    # Change only its pigment: all coat inputs and the grout shader stay intact.
    face = intact.node.inputs[1].links[0].from_node
    attenuation = m('SUBTRACT',1,d['Dirt'])
    a.put(v('MULTIPLY',color,a.xyz(attenuation,attenuation,attenuation)),face.inputs['Base Color'])
    grain = a.amplitude(a.v('ADD', i['World'], a.rand(i['Cell'], (563, 569, 571), True)), 1/.00045)
    grog = m('GREATER_THAN', a.noise(i['World'], 1/.0005), .7)
    iron = m('LESS_THAN', a.noise(a.v('ADD', i['World'], (17, 23, 31)), 1/.0004), .28)
    tone = m('MULTIPLY', m('ADD', .85, m('MULTIPLY', .3, a.rand(i['Cell'], (521, 541, 557)))),
             m('ADD', 1, m('MULTIPLY', .2, grain)))
    # Red-firing body, linear; slip and body colours become knobs with the chip work (chips are WIP).
    clay_color = v('MULTIPLY', (.30, .17, .10), a.xyz(tone, tone, tone))
    specks = m('MULTIPLY', m('ADD', 1, m('MULTIPLY', .4, grog)), m('SUBTRACT', 1, m('MULTIPLY', .35, iron)))
    clay_color = v('MULTIPLY', clay_color, a.xyz(specks, specks, specks))
    # The existing dust colour is the same physical deposit inside the deepest bowls.
    deposit = m('MULTIPLY', m('MULTIPLY', i['Dust'], i['dust On']),
                m('MULTIPLY', .2, a.smooth(d['Chip Depth Out'], .0015, .0025)))
    clay_color = v('ADD', v('MULTIPLY', clay_color, a.xyz(m('SUBTRACT', 1, deposit), m('SUBTRACT', 1, deposit), m('SUBTRACT', 1, deposit))),
                   v('MULTIPLY', i['Grout Albedo'], a.xyz(deposit, deposit, deposit)))
    bump = a.node('ShaderNodeBump'); bump.name = 'DamageBump'
    bump.inputs['Distance'].default_value = 1
    a.put(height, bump.inputs['Height'])
    fine = a.node('ShaderNodeBump'); fine.inputs['Distance'].default_value = .00003
    fine.name = 'ClayGrainBump'
    a.put(a.noise(i['World'], 1/.0001), fine.inputs['Height']); a.put(bump.outputs['Normal'], fine.inputs['Normal'])
    def material(base, rough, normal):
        bsdf = a.node('ShaderNodeBsdfPrincipled')
        a.put(base, bsdf.inputs['Base Color']); bsdf.inputs['Roughness'].default_value = rough
        bsdf.inputs['Coat Weight'].default_value = 0
        a.put(normal, bsdf.inputs['Normal'])
        return bsdf.outputs['BSDF']
    def mix(mask, first, second):
        node = a.node('ShaderNodeMixShader')
        for value, socket in zip((mask, first, second), node.inputs):
            a.put(value, socket)
        return node.outputs[0]
    shader = mix(d['Engobe'], intact, material((.70, .70, .70), .9, bump.outputs['Normal']))
    shader = mix(d['Body'], shader, material(clay_color, .9, fine.outputs['Normal']))
    dark = v('MULTIPLY', color, (.25, .25, .25))
    return mix(d['Crack'], shader, material(dark, .9, bump.outputs['Normal']))
