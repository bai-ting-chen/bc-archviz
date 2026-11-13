"""Shared offset lookups for image maps, with world-space blending."""
import random
import math
from materials.shared.node_graph import layer_frame, layer_switch

MASK_MEAN = 0.5  # measured Noise Texture centre
MASK_HALF_RANGE = 0.12  # approximately two measured SDs; avoid a constant blend
OFFSET_SPAN = 32.0  # texture-coordinate units; decorrelate neighbouring lookups


def lookup_offsets(count, seed=0):
    """Return seeded XYZ lookup offsets shared by offset-only and rotated map sampling."""
    rng = random.Random(seed)
    return [tuple(rng.uniform(-OFFSET_SPAN, OFFSET_SPAN) for _ in range(3)) for _ in range(count)]


def randomized_vectors(graph, vector, count=3, seed=0, scale_jitter=.12, frame=None):
    """Rotate, slightly rescale and offset independent metre-space image lookups."""
    rng = random.Random(seed + 7919)
    result = []
    for row, offset in enumerate(lookup_offsets(count, seed)):
        rotation = graph.node('ShaderNodeVectorRotate', (-2100, -700*row), frame)
        rotation.rotation_type = 'AXIS_ANGLE'
        rotation.inputs['Axis'].default_value = (0, 0, 1)
        rotation.inputs['Angle'].default_value = rng.uniform(-math.pi, math.pi)
        graph.link(vector, rotation.inputs['Vector'])
        scale = graph.node('ShaderNodeVectorMath', (-1800, -700*row), frame)
        scale.operation = 'SCALE'
        scale.inputs['Scale'].default_value = rng.uniform(1-scale_jitter, 1+scale_jitter)
        graph.link(rotation.outputs[0], scale.inputs[0])
        result.append(_shift(graph, scale.outputs[0], (*offset[:2], 0), frame, row))
    return result


def _lookup(graph, tex, vector, frame, row):
    node = graph.node('ShaderNodeTexImage', (-1200, -700*row), frame, label=tex.label)
    node.image = tex.image
    for prop in ('projection', 'projection_blend', 'interpolation', 'extension'):
        setattr(node, prop, getattr(tex, prop))
    graph.link(vector, node.inputs['Vector'])
    return node


def _shift(graph, vector, offset, frame, row):
    shifted = graph.node('ShaderNodeVectorMath', (-1500, -700*row), frame)
    shifted.operation = 'ADD'
    graph.link(vector, shifted.inputs[0])
    shifted.inputs[1].default_value = offset
    return shifted.outputs[0]


def _relink(graph, tex, copies, masks, switch, frame, row):
    consumers = [(link.from_socket.name, link.to_socket) for socket in tex.outputs
                 for link in list(socket.links)]
    results = {}
    for output_index, output in enumerate(tex.outputs):
        blended = output
        for column, (copy, mask) in enumerate(zip(copies, masks)):
            blended = graph.mix(blended, copy.outputs[output.name], mask, (-900+300*column, -700*(row+output_index)), frame)
        results[output.name] = graph.mix(output, blended, switch, (-900+300*len(copies), -700*(row+output_index)), frame)
    for name, consumer in consumers:
        graph.link(results[name], consumer)
    return results


def _blend_masks(graph, lookups, scale_m, amount, frame):
    world = graph.node('ShaderNodeNewGeometry', (-1800, 0), frame).outputs['Position']
    field = graph.noise_texture(world, 1/scale_m, (-1500, 0), frame)
    field = graph.map_range(field, MASK_MEAN-MASK_HALF_RANGE, MASK_MEAN+MASK_HALF_RANGE,
                    (-1200, 0), frame=frame)
    masks = [graph.map_range(field, i/lookups, (i+1)/lookups, (-900, -700*(i+1)),
                     frame=frame, smooth=True) for i in range(lookups-1)]
    control = graph.node('ShaderNodeValue', (-1800, 600), frame, label='anti_tile amount').outputs[0]
    control.default_value = amount
    remaining = 1
    for row, mask in enumerate(masks, 1):
        inverse = graph.math('SUBTRACT', 1, mask, (-600, -700*row), frame)
        remaining = graph.math('MULTIPLY', remaining, inverse, (-300, -700*row), frame)
    extent = graph.math('SUBTRACT', 1, remaining, (0, -700*(len(masks)+1)), frame)
    layer_switch(graph, 'anti_tile', extent, control, 0, frame)
    return masks, control


def anti_tile(graph, textures, lookups=3, scale_m=1.5, seed=0, amount=1.0):
    """Relink image consumers to shared XYZ-offset lookups; amount zero is the original."""
    frame = layer_frame(graph, 'VARIATION: TILING')
    offsets = lookup_offsets(lookups-1, seed)
    masks, switch = _blend_masks(graph, lookups, scale_m, amount, frame)
    default_uv = None
    shifted_vectors = {}
    results = []
    for index, tex in enumerate(textures):
        row = 8 + index*max(2, lookups-1)
        vector = tex.inputs['Vector']
        if not vector.is_linked:
            if default_uv is None:
                default_uv = graph.node('ShaderNodeTexCoord', (-1800, -5600), frame).outputs['UV']
            graph.link(default_uv, vector)
        vector = vector.links[0].from_socket
        key = vector.as_pointer()
        if key not in shifted_vectors:
            shifted_vectors[key] = [_shift(graph, vector, offset, frame, 8+len(shifted_vectors)*(lookups-1)+i)
                                    for i, offset in enumerate(offsets)]
        copies = [_lookup(graph, tex, shifted, frame, row+i)
                  for i, shifted in enumerate(shifted_vectors[key])]
        results.append(_relink(graph, tex, copies, masks, switch, frame, row))
    return results
