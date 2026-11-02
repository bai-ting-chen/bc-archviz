"""Shared offset lookups for image maps, with world-space blending."""
import random
from materials.shared.nodes import layer_frame, layer_switch, sock

MASK_MEAN = 0.5  # measured Noise Texture centre
MASK_HALF_RANGE = 0.12  # approximately two measured SDs; avoid a constant blend
OFFSET_SPAN = 32.0  # texture-coordinate units; decorrelate neighbouring lookups


def _lookup(g, tex, vector, frame, row):
    node = g.node('ShaderNodeTexImage', (-1200, -700*row), frame, label=tex.label)
    node.image = tex.image
    for prop in ('projection', 'projection_blend', 'interpolation', 'extension'):
        setattr(node, prop, getattr(tex, prop))
    g.link(vector, node.inputs['Vector'])
    return node


def _shift(g, vector, offset, frame, row):
    shifted = g.node('ShaderNodeVectorMath', (-1500, -700*row), frame)
    shifted.operation = 'ADD'
    g.link(vector, shifted.inputs[0])
    shifted.inputs[1].default_value = offset
    return shifted.outputs[0]


def _mix(g, a, b, weight, frame, column, row):
    mix = g.node('ShaderNodeMix', (-900+300*column, -700*row), frame)
    mix.data_type = 'RGBA'
    g.link(weight, mix.inputs[0])
    g.link(a, sock(mix.inputs, 'A'))
    g.link(b, sock(mix.inputs, 'B'))
    return sock(mix.outputs, 'Result')


def _relink(g, tex, copies, masks, switch, frame, row):
    consumers = [(link.from_socket.name, link.to_socket) for socket in tex.outputs
                 for link in list(socket.links)]
    results = {}
    for output_index, output in enumerate(tex.outputs):
        blended = output
        for column, (copy, mask) in enumerate(zip(copies, masks)):
            blended = _mix(g, blended, copy.outputs[output.name], mask, frame, column, row+output_index)
        results[output.name] = _mix(g, output, blended, switch, frame, len(copies), row+output_index)
    for name, consumer in consumers:
        g.link(results[name], consumer)
    return results


def _blend_masks(g, lookups, scale_m, amount, frame):
    world = g.node('ShaderNodeNewGeometry', (-1800, 0), frame).outputs['Position']
    field = g.noise(world, 1/scale_m, (-1500, 0), frame)
    field = g.range(field, MASK_MEAN-MASK_HALF_RANGE, MASK_MEAN+MASK_HALF_RANGE,
                    (-1200, 0), frame=frame)
    masks = [g.range(field, i/lookups, (i+1)/lookups, (-900, -700*(i+1)),
                     frame=frame, smooth=True) for i in range(lookups-1)]
    control = g.node('ShaderNodeValue', (-1800, 600), frame, label='anti_tile amount').outputs[0]
    control.default_value = amount
    remaining = 1
    for row, mask in enumerate(masks, 1):
        inverse = g.math('SUBTRACT', 1, mask, (-600, -700*row), frame)
        remaining = g.math('MULTIPLY', remaining, inverse, (-300, -700*row), frame)
    extent = g.math('SUBTRACT', 1, remaining, (0, -700*(len(masks)+1)), frame)
    layer_switch(g, 'anti_tile', extent, control, 0, frame)
    return masks, control


def anti_tile(g, texs, lookups=3, scale_m=1.5, seed=0, amount=1.0):
    """Relink image consumers to shared XYZ-offset lookups; amount zero is the original."""
    frame = layer_frame(g, 'VARIATION: TILING')
    rng = random.Random(seed)
    offsets = [tuple(rng.uniform(-OFFSET_SPAN, OFFSET_SPAN) for _ in range(3)) for _ in range(lookups-1)]
    masks, switch = _blend_masks(g, lookups, scale_m, amount, frame)
    default_uv = None
    shifted_vectors = {}
    results = []
    for index, tex in enumerate(texs):
        row = 8 + index*max(2, lookups-1)
        vector = tex.inputs['Vector']
        if not vector.is_linked:
            if default_uv is None:
                default_uv = g.node('ShaderNodeTexCoord', (-1800, -5600), frame).outputs['UV']
            g.link(default_uv, vector)
        vector = vector.links[0].from_socket
        key = vector.as_pointer()
        if key not in shifted_vectors:
            shifted_vectors[key] = [_shift(g, vector, offset, frame, 8+len(shifted_vectors)*(lookups-1)+i)
                                    for i, offset in enumerate(offsets)]
        copies = [_lookup(g, tex, shifted, frame, row+i)
                  for i, shifted in enumerate(shifted_vectors[key])]
        results.append(_relink(g, tex, copies, masks, switch, frame, row))
    return results
