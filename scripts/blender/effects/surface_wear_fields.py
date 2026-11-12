"""Procedural surface-wear factors in surface coordinates measured in metres."""
import math


def procedural_field(g, kind, vector, scale_m, scratch_width_m, frame, region=False):
    """Return a 0–1 wear profile, or the continuous pre-profile dried-mark driver for regions."""
    if kind in ('grunge', 'worn-through'):
        noise = g.noise(vector, 1 / scale_m, (-1800, 0), frame, detail=3)
    if kind == 'grunge':
        fine = g.range(noise, .35, .65, (-1500, 0), frame=frame)
        extent = g.noise(vector, 1 / (scale_m * 4), (-1800, -400), frame)
        extent = g.range(extent, .43, .57, (-1500, -400), frame=frame)
        return g.math('MULTIPLY', fine, extent, (-1200, 0), frame)
    if kind == 'scratches':
        return _scratches(g, vector, scale_m, scratch_width_m, frame)
    if kind == 'dried-marks':
        if region:
            from effects.surface_wear_deposits import deposit_distance
            distance,_,_=deposit_distance(g,vector,scale_m,frame)
            return g.range(distance,-.12,.12,(-900,-18000),frame=frame)
        from effects.surface_wear_deposits import irregular_deposits
        return irregular_deposits(g,vector,scale_m,frame)
    if kind == 'worn-through':
        return g.range(noise, .54, .57, (-1500, 0), frame=frame, smooth=True)
    raise ValueError('Unknown surface-wear layer: ' + kind)


def _scratches(g, vector, length_m, width_m, frame):
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
        lines = g.noise(stretch.outputs[0], 1, (-2200, y), frame, detail=2)
        lines = g.range(lines, .65, .72, (-1900, y), frame=frame)
        extent = g.noise(offset.outputs[0], 1 / length_m, (-2200, y - 700), frame, detail=2)
        extent = g.range(extent, .48, .6, (-1900, y - 700), frame=frame)
        fields.append(g.math('MULTIPLY', lines, extent, (-1600, y), frame))
    result = fields[0]
    for i, value in enumerate(fields[1:]):
        result = g.math('MAXIMUM', result, value, (-1200 + i * 200, -11000 - i * 300), frame)
    return result


