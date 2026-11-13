"""Dispatch procedural patterns to their mechanism owners."""
from effects.wear.layer_names import canonical_layer
from effects.wear.dirt import grunge_field
from effects.wear.scratches import scratches_field
from effects.wear.water_marks import dried_marks_field
from effects.wear.chipping import chipping_field


def procedural_field(g, kind, vector, scale_m, scratch_width_m, frame, region=False):
    """Return a wear profile or a continuous deposit driver for a hybrid region."""
    kind = canonical_layer(kind)
    if kind == 'grunge':
        return grunge_field(g, vector, scale_m, frame)
    if kind == 'scratches':
        return scratches_field(g, vector, scale_m, scratch_width_m, frame)
    if kind == 'dried-marks':
        return dried_marks_field(g, vector, scale_m, frame, region)
    if kind == 'chipping':
        return chipping_field(g, vector, scale_m, frame)
    raise ValueError('Unknown wear layer: ' + kind)
