"""World-space macro tone with independently switched albedo and roughness outputs."""
import math
from materials.shared.node_graph import layer_frame, layer_switch

# One octave measured on variation_lab's 64 m XY plane at 512 x 512 pixels.
SINGLE_OCTAVE_NOISE_SD = 0.1174030453
NOISE_MEAN = 0.5


def _moments(detail, rough):
    octaves = math.floor(detail)
    amplitudes = [rough**i for i in range(octaves+1)]
    if detail != octaves:
        amplitudes[-1] *= detail-octaves
    sd = SINGLE_OCTAVE_NOISE_SD * math.sqrt(sum(a*a for a in amplitudes)) / sum(amplitudes)
    return NOISE_MEAN, sd


def _field(graph, layer, scale_m, detail=6.0, rough=0.6):
    frame = layer_frame(graph, 'VARIATION: ' + layer.upper().replace('_', ' '))
    world = graph.node('ShaderNodeNewGeometry', (-1800, 0), frame).outputs['Position']
    return graph.noise_texture(world, 1/scale_m, (-1500, 0), frame, detail=detail, roughness=rough), frame


def macro_tone(graph, scale_m=4.0, albedo=0.075, roughness=0.05, amount=1.0):
    """Return world-space albedo multiplier and roughness addition with independent amount controls."""
    noise, frame = _field(graph, 'macro_tone', scale_m)
    mean, sd = _moments(6.0, 0.6)
    values = []
    for row, (name, span, neutral) in enumerate((('macro_tone', albedo, 1), ('macro_roughness', roughness, 0))):
        raw = graph.map_range(noise, mean-2*sd, mean+2*sd, (-1200, -700*row), target_min=neutral-span, target_max=neutral+span, frame=frame)
        values.append(layer_switch(graph, name, raw, amount, neutral, frame))
    return tuple(values)
