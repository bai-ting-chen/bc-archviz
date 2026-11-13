"""Shared stochastic scan sampling through the canonical loader and offset generator."""

from effects.wear.image_masks import image_mask
from effects.variation_tiling import randomized_vectors


def stochastic_mask(graph, masks, vector, settings, frame=None):
    """Blend three rotated, offset, scale-jittered lookups with independent slow world noise."""
    values = []
    vectors = randomized_vectors(graph, vector, 3, settings.seed, settings.scale_jitter, frame)
    uv_vectors = {}
    for index, coordinates in enumerate(vectors):
        mask=masks[index % len(masks)]
        if mask.mapping=='uv':
            if mask.uv_map not in uv_vectors:
                uv=graph.uv_map(mask.uv_map,(-3600,-16000),frame)
                uv_vectors[mask.uv_map]=randomized_vectors(graph,uv,3,settings.seed,settings.scale_jitter,frame)
            value=image_mask(graph,mask,frame=frame,row=index+8,mapped_vector=uv_vectors[mask.uv_map][index])
        else:
            value=image_mask(graph,mask,coordinates,frame,row=index+8)
        values.append(value)
    geo = graph.node('ShaderNodeNewGeometry', (-3300, -15000), frame)
    noise = graph.noise_texture(geo.outputs['Position'], 1/settings.blend_scale_m, (-3000, -15000), frame, detail=2)
    weight = graph.map_range(noise, .35, .65, (-2700, -15000), frame=frame, smooth=True)
    second = graph.noise_texture(geo.outputs['Position'], .71/settings.blend_scale_m, (-3000, -15500), frame, detail=3)
    weight_b = graph.map_range(second, .35, .65, (-2700, -15500), frame=frame, smooth=True)
    def mix(a, b, factor, row):
        return graph.mix(a, b, factor, (-2300+row*300, -15000), frame, data_type='FLOAT')
    return mix(mix(values[0], values[1], weight, 0), values[2], weight_b, 1)
