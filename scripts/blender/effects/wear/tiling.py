"""Shared stochastic scan sampling through the canonical loader and offset generator."""
from materials.shared.nodes import sock
from effects.wear.masks import image_mask
from effects.variation_tiling import randomized_vectors


def stochastic_mask(g, masks, vector, settings, frame=None):
    """Blend three rotated, offset, scale-jittered lookups with independent slow world noise."""
    values = []
    vectors = randomized_vectors(g, vector, 3, settings.seed, settings.scale_jitter, frame)
    uv_vectors = {}
    for index, coordinates in enumerate(vectors):
        mask=masks[index % len(masks)]
        if mask.mapping=='uv':
            if mask.uv_map not in uv_vectors:
                uv=g.uv(mask.uv_map,(-3600,-16000),frame)
                uv_vectors[mask.uv_map]=randomized_vectors(g,uv,3,settings.seed,settings.scale_jitter,frame)
            value=image_mask(g,mask,frame=frame,row=index+8,mapped_vector=uv_vectors[mask.uv_map][index])
        else:
            value=image_mask(g,mask,coordinates,frame,row=index+8)
        values.append(value)
    geo = g.node('ShaderNodeNewGeometry', (-3300, -15000), frame)
    noise = g.noise(geo.outputs['Position'], 1/settings.blend_scale_m, (-3000, -15000), frame, detail=2)
    weight = g.range(noise, .35, .65, (-2700, -15000), frame=frame, smooth=True)
    second = g.noise(geo.outputs['Position'], .71/settings.blend_scale_m, (-3000, -15500), frame, detail=3)
    weight_b = g.range(second, .35, .65, (-2700, -15500), frame=frame, smooth=True)
    def mix(a, b, factor, row):
        node = g.node('ShaderNodeMix', (-2300+row*300, -15000), frame)
        node.data_type = 'FLOAT'
        g.link(factor, node.inputs[0])
        g.link(a, sock(node.inputs, 'A'))
        g.link(b, sock(node.inputs, 'B'))
        return sock(node.outputs, 'Result')
    return mix(mix(values[0], values[1], weight, 0), values[2], weight_b, 1)
