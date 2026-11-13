"""Canonical wear layer names and their deprecated input alias."""
LAYERS = ('grunge', 'scratches', 'dried-marks', 'chipping')


def canonical_layer(kind):
    """Accept the deprecated coating-loss spelling while returning its mechanism name."""
    return 'chipping' if kind == 'worn-through' else kind
