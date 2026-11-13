"""Bind weathering graph operations to the canonical node builder."""

import os as _os, sys as _sys
_sys.path.append(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import controls_import_paths  # noqa: E402,F401 -- every controls topic folder on sys.path
def operations(graph):
    """Return node operations bound to this material builder."""
    O0 = (0, 0)   # node locations are irrelevant here
    def math(op, a, b2=0.0, clamp=False):
        """NodeGraph.math at the origin."""
        return graph.math(op, a, b2, O0, clamp=clamp)

    def comb(x, y, z):
        """NodeGraph.combine_xyz at the origin."""
        return graph.combine_xyz(x, y, z, O0)

    def noise(vec, scale, detail=2.0, rough=.5):
        """NodeGraph.noise_texture (3D, no distortion) at the origin."""
        return graph.noise_texture(vec, scale, O0, detail=detail, roughness=rough)

    def ramp(v, a, b2, smooth=True):
        """NodeGraph.map_range from [a, b2] to [0, 1]; smoothstep unless smooth=False."""
        return graph.map_range(v, a, b2, O0, smooth=smooth)
    return math, comb, noise, ramp
