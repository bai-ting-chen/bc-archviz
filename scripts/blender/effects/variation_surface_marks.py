"""World-space macro tone, calibrated grunge and patchy mark extents."""
import math
from statistics import NormalDist
from materials.shared.nodes import layer_frame, layer_switch

# One octave measured on variation_lab's 64 m XY plane at 512 x 512 pixels, Blender 5.2.
SD1 = 0.1174030453
NOISE_MEAN = 0.5


def _moments(detail, rough):
    octaves = math.floor(detail)
    amplitudes = [rough**i for i in range(octaves+1)]
    if detail != octaves:
        amplitudes[-1] *= detail-octaves
    sd = SD1 * math.sqrt(sum(a*a for a in amplitudes)) / sum(amplitudes)
    return NOISE_MEAN, sd


def _field(g, layer, scale_m, detail=6.0, rough=0.6):
    frame = layer_frame(g, 'VARIATION: ' + layer.upper().replace('_', ' '))
    world = g.node('ShaderNodeNewGeometry', (-1800, 0), frame).outputs['Position']
    return g.noise(world, 1/scale_m, (-1500, 0), frame, detail=detail, rough=rough), frame


def macro_tone(g, scale_m=4.0, albedo=0.075, roughness=0.05, amount=1.0):
    """Return world-space albedo multiplier and roughness addition with one switch."""
    noise, frame = _field(g, 'macro_tone', scale_m)
    mean, sd = _moments(6.0, 0.6)
    values = []
    for row, (name, span, neutral) in enumerate((('macro_tone', albedo, 1), ('macro_roughness', roughness, 0))):
        raw = g.range(noise, mean-2*sd, mean+2*sd, (-1200, -700*row), tmin=neutral-span, tmax=neutral+span, frame=frame)
        values.append(layer_switch(g, name, raw, amount, neutral, frame))
    return tuple(values)


def grunge(g, scale_m=0.5, target_sd=0.05, detail=6.0, rough=0.6, amount=1.0):
    """Return grunge normalised by measured noise moments for detail and roughness."""
    mean, sd = _moments(detail, rough)
    noise, frame = _field(g, 'grunge', scale_m, detail, rough)
    signed = g.math('SUBTRACT', noise, mean, (-1200, 0), frame)
    gain = g.math('MULTIPLY', signed, target_sd/sd, (-900, 0), frame)
    raw = g.math('ADD', gain, 1, (-600, 0), frame)
    return layer_switch(g, 'grunge', raw, amount, 1, frame)


def patchy_extent(g, coverage=0.5, scale_m=3.0, softness=0.1, amount=1.0):
    """Return a soft mark mask with a calibrated zero-area fraction of one minus coverage."""
    noise, frame = _field(g, 'patchy_extent', scale_m)
    mean, sd = _moments(6.0, 0.6)
    coverage = min(max(coverage, 1e-3), 1-1e-3)
    threshold = mean + sd * NormalDist().inv_cdf(1-coverage)
    mask = g.range(noise, threshold, threshold+softness, (-1200, 0), frame=frame, smooth=True)
    return layer_switch(g, 'patchy_extent', mask, amount, 0, frame)
