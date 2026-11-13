"""Compose the weathering fields as independent look multipliers."""

import os as _os, sys as _sys
_sys.path.append(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import controls_import_paths  # noqa: E402,F401 -- every controls topic folder on sys.path
from weathering_nodes import operations
from weathering_fields import runoff, zones, joint_leaks

def shader(graph, position_components, wall_height_m, settings, emission_node):
    """Connect the original weathering shader to its emission output."""
    math, comb, noise, ramp = operations(graph)
    x, z = position_components.outputs['X'], position_components.outputs['Z']
    top = wall_height_m
    S = runoff(math, comb, noise, ramp, x, z, top, settings)
    B, C, D = zones(math, comb, noise, ramp, x, z, top, settings)
    T = ramp(math('SUBTRACT', top, z), .35, 0.0)  # dirt under the coping
    M = math('MULTIPLY', math('SUBTRACT', 1.0, math('MULTIPLY', T, settings['topband_amp'])), math('SUBTRACT', 1.0, math('MULTIPLY', S, settings['streak_amp'])))
    M = math('MULTIPLY', M, math('SUBTRACT', 1.0, math('MULTIPLY', B, settings['base_amp'])))
    M = math('MULTIPLY', M, math('ADD', 1.0, math('MULTIPLY', C, 2 * settings['patch_amp'])))
    M = math('MULTIPLY', M, math('ADD', 1.0, math('MULTIPLY', D, 2 * settings['blot_amp'])))
    J = joint_leaks(math, comb, noise, ramp, x, z, top, settings)
    M = math('MULTIPLY', M, math('SUBTRACT', 1.0, math('MULTIPLY', J, settings['j_amp'])))
    # board joints for scale only: dark line every 0.28 m.
    j = math('MULTIPLY', math('LESS_THAN', math('PINGPONG', math('SUBTRACT', top, z), settings['board_h'] / 2), .006), settings['show_joints'])
    col = math('MULTIPLY', math('MULTIPLY', M, .62), math('SUBTRACT', 1.0, math('MULTIPLY', j, .35)))
    graph.link(col, emission_node.inputs['Color']); emission_node.inputs['Strength'].default_value = 1.0
