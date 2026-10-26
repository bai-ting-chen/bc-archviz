"""Weathering lab: whole-wall weathering multiplier in native shader nodes on a flat test wall (metres).

Design a look layer here (renders take seconds), then install the exact node graph in the scene
(references/effects/edge-wear.md > Runoff; references/review/validation.md > Flat-wall lab).
Factors, all multiplicative around 1 (RULES MAT_07):
  1 run-off streaks from the top: two widths, clustered, meandering, own length per streak
  2 dirt band under the top     3 damp base with an uneven edge
  4 large soft patches          5 medium blotches
  6 leaks under horizontal joints: short drips, a pattern per joint; a drip ends at the next
    joint below (j_len longer than board_h is cut there)
Defaults are a tuned, balanced set; override any of them as key=value.

Usage: blender -b --factory-startup --python weathering_lab.py -- <out_dir> <tag> [key=value ...]
Writes <out_dir>/lab_<tag>.png (8 x 4 m wall, joints drawn for scale, Standard view).
"""

import os as _os
import sys as _sys
_CONTROLS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in [_CONTROLS] + [_os.path.join(_CONTROLS, _t) for _t in ('archviz', 'tile', 'material', 'effects', 'water', 'lighting', 'environment', 'regression')]:
    if _d not in _sys.path:
        _sys.path.append(_d)
import bpy, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / 'blender'))
import core.archviz as archviz
from materials.shared.nodes import G
sys.path.insert(0, str(Path(__file__).resolve().parent))
from weathering_rig import scene, render
from weathering_shader import shader

def main():
    """Parse overrides and render the weathering lab."""
    argv = sys.argv[sys.argv.index('--') + 1:]; O = Path(argv[0]); TAG = argv[1]
    P = dict(board_h=.28, j_amp=.24, j_w=18.0, j_len_min=.10, j_len_span=.55, j_density=.55, j_thr=.46,
             wiggle=.06, cluster_scale=.45, cluster_thr=.28, topband_amp=.156, len_min=1.2, len_span=3.0,
             fade_pow=1.0, streak_amp=.37, streak_w=7.0, streak_len=.45, streak_thr=.44, base_amp=.286,
             base_h=.55, patch_amp=.195, patch_scale=.35, blot_amp=.065, blot_scale=2.5, show_joints=1.0)
    for kv in argv[2:]:
        k, v = kv.split('='); P[k] = float(v)
    sc, W, H, wall, m, b, em, sep = scene()
    shader(b, sep, H, P, em)
    wall.data.materials.append(m)
    render(sc, W, H, O, TAG)
    print('LAB_DONE', TAG, P)

if __name__ == '__main__':
    main()
