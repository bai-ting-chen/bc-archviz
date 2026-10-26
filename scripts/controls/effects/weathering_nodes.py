"""Bind weathering graph operations to the canonical node builder."""

import os as _os
import sys as _sys
_CONTROLS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in [_CONTROLS] + [_os.path.join(_CONTROLS, _t) for _t in ('archviz', 'tile', 'material', 'effects', 'water', 'lighting', 'environment', 'regression')]:
    if _d not in _sys.path:
        _sys.path.append(_d)
def operations(b):
    """Return node operations bound to this material builder."""
    O0 = (0, 0)   # node locations are irrelevant here
    def math(op, a, b2=0.0, clamp=False):
        """G.math at the origin."""
        return b.math(op, a, b2, O0, clamp=clamp)

    def comb(x, y, z):
        """G.combine at the origin."""
        return b.combine(x, y, z, O0)

    def noise(vec, scale, detail=2.0, rough=.5):
        """G.noise (3D, no distortion) at the origin."""
        return b.noise(vec, scale, O0, detail=detail, rough=rough)

    def ramp(v, a, b2, smooth=True):
        """G.range from [a, b2] to [0, 1]; smoothstep unless smooth=False."""
        return b.range(v, a, b2, O0, smooth=smooth)
    return math, comb, noise, ramp
