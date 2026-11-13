"""Crossing procedural scratches and their held legacy scan modulation."""
import math
from effects.wear.image_masks import asset_mask
from effects.wear.scan_sampling import stochastic_mask

def scratches_field(g, vector, length_m, width_m, frame):
    """Return four independently phased stroke orientations in metre coordinates."""
    fields = []
    # Independent phases and unequal lengths keep the four orientations from reading as a hatch.
    for i, (angle_deg, length_ratio) in enumerate(((13, .6), (61, 1.1), (112, .35), (157, .85))):
        y = -3500 * i
        rotate = g.node('ShaderNodeVectorRotate', (-3000, y), frame)
        rotate.rotation_type = 'AXIS_ANGLE'
        rotate.inputs['Axis'].default_value = (0, 0, 1)
        rotate.inputs['Angle'].default_value = math.radians(angle_deg)
        g.link(vector, rotate.inputs['Vector'])
        offset = g.node('ShaderNodeVectorMath', (-2800, y), frame)
        offset.operation = 'ADD'
        g.link(rotate.outputs[0], offset.inputs[0])
        offset.inputs[1].default_value = (i * 1.73, i * .91, i * .37)
        stretch = g.node('ShaderNodeVectorMath', (-2500, y), frame)
        stretch.operation = 'MULTIPLY'
        g.link(offset.outputs[0], stretch.inputs[0])
        stretch.inputs[1].default_value = (1 / (length_m * length_ratio), 1 / width_m, 1)
        lines = g.noise_texture(stretch.outputs[0], 1, (-2200, y), frame, detail=2)
        lines = g.map_range(lines, .65, .72, (-1900, y), frame=frame)
        extent = g.noise_texture(offset.outputs[0], 1 / length_m, (-2200, y - 700), frame, detail=2)
        extent = g.map_range(extent, .48, .6, (-1900, y - 700), frame=frame)
        fields.append(g.math('MULTIPLY', lines, extent, (-1600, y), frame))
    result = fields[0]
    for i, value in enumerate(fields[1:]):
        result = g.math('MAXIMUM', result, value, (-1200 + i * 200, -11000 - i * 300), frame)
    return result


def scratch_hybrid(g, layer, vector, frame=None):
    """Keep the held scratch hybrid's existing 0.7–1.0 scan modulation unchanged."""
    mask = layer.mask or asset_mask('vdekdjrc')
    if mask is None:
        from effects.wear.default_sources import report_missing
        report_missing('vdekdjrc', 'scratched metal')
        return scratches_field(g, vector, layer.scale_m, layer.scratch_width_m, frame)
    texture = stochastic_mask(g, [mask], vector, layer.hybrid, frame)
    shape = scratches_field(g, vector, layer.scale_m, layer.scratch_width_m, frame)
    modulation = g.math('MULTIPLY', texture, .3, (-900, -16000), frame)
    modulation = g.math('ADD', modulation, .7, (-600, -16000), frame)
    return g.math('MULTIPLY', shape, modulation, (-300, -16000), frame)
