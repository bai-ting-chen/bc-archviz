"""Thin shorthands for the wear shaders and Geometry Nodes: a frame for one wear layer, and the
attribute, noise, map range and math nodes with the argument order the wear builders use.

Each one forwards to the canonical builder (materials.shared.nodes.G), so the node graph is the same.
"""
from materials.shared.nodes import G


def frame_for(mat, label):
    """The material's node builder with one labelled frame for a wear layer; returns (builder, label)."""
    g = G(mat.node_tree)
    g.frame(label, (0.18, 0.26, 0.30))
    return g, label


def attr(g, name, loc, frame, out="Fac"):
    """Named attribute (edge_dist, chip, rest_pos, leak_d ...) at a location in a frame."""
    return g.attr(name, loc, frame, out)


def noise(g, vec, scale, loc, frame, detail=6.0, rough=0.6, label=None):
    """Noise texture on a vector, at a location in a frame."""
    return g.noise(vec, scale, loc, frame, detail, rough, label)


def range_(g, val, fmin, fmax, loc, frame, tmin=0.0, tmax=1.0, label=None, smooth=False):
    """Map Range from [fmin, fmax] to [tmin, tmax], at a location in a frame."""
    return g.range(val, fmin, fmax, loc, tmin, tmax, frame, label, smooth)


def math_(g, op, a, b, loc, frame, clamp=False):
    """Math node (op on a and b), at a location in a frame."""
    return g.math(op, a, b, loc, frame, clamp)
