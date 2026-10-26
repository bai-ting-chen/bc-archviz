"""Weathering look fields: runoff, base patches and board-joint leaks."""

import os as _os
import sys as _sys
_CONTROLS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in [_CONTROLS] + [_os.path.join(_CONTROLS, _t) for _t in ('archviz', 'tile', 'material', 'effects', 'water', 'lighting', 'environment', 'regression')]:
    if _d not in _sys.path:
        _sys.path.append(_d)
def runoff(math, comb, noise, ramp, x, z, top, P):
    """Build the top-fed clustered runoff field."""
    # 1. run-off streaks: narrow along x, long along z; start at the top, each streak with its own length.
    xw = math('ADD', x, math('MULTIPLY', math('SUBTRACT', noise(comb(math('MULTIPLY', x, .7), math('MULTIPLY', z, 2.2), 5.0), 1.0, detail=2.0), .5), P['wiggle']))  # meandering edges
    fine = ramp(noise(comb(math('MULTIPLY', xw, P['streak_w']), math('MULTIPLY', z, P['streak_len']), 0.0), 1.0, detail=3.0, rough=.55), P['streak_thr'], P['streak_thr'] + .18)
    wide = ramp(noise(comb(math('MULTIPLY', xw, P['streak_w'] * .4), math('MULTIPLY', z, P['streak_len'] * .7), 2.0), 1.0, detail=2.0, rough=.5), P['streak_thr'] + .02, P['streak_thr'] + .22)
    cluster = ramp(noise(comb(math('MULTIPLY', x, P['cluster_scale']), 0, 4.4), 1.0, detail=1.0), P['cluster_thr'], P['cluster_thr'] + .2)
    streak = math('MULTIPLY', math('MAXIMUM', fine, math('MULTIPLY', wide, .75)), cluster)
    length = math('ADD', P['len_min'], math('MULTIPLY', ramp(noise(comb(math('MULTIPLY', x, 1.6), 0, 7.3), 1.0, detail=1.0), .3, .7, False), P['len_span']))
    depth = math('SUBTRACT', top, z)
    fade = math('SUBTRACT', 1.0, math('DIVIDE', depth, length), True)   # 1 at top -> 0 at its length
    fade = math('POWER', fade, P['fade_pow'])
    S = math('MULTIPLY', streak, fade)
    return S

def zones(math, comb, noise, ramp, x, z, top, P):
    """Build base damp, broad patches and blotches."""
    # 2. base zone: dark at the foot, irregular top edge.
    edge = math('ADD', P['base_h'], math('MULTIPLY', math('SUBTRACT', noise(comb(math('MULTIPLY', x, .9), 3.1, 0), 1.0, detail=3.0), .5), .7))
    B = ramp(math('SUBTRACT', edge, z), -.15, .25)
    # 3. large soft patches (1-3 m), signed.
    C = math('SUBTRACT', ramp(noise(comb(x, 0, math('MULTIPLY', z, 1.3)), P['patch_scale'], detail=2.0, rough=.5), .3, .7, False), .5)
    # 4. medium blotches, signed.
    D = math('SUBTRACT', ramp(noise(comb(x, 11.0, z), P['blot_scale'], detail=4.0, rough=.6), .3, .7, False), .5)
    return B, C, D

def joint_leaks(math, comb, noise, ramp, x, z, top, P):
    """Build short leaks held at each horizontal joint."""
    # 6. small leaks from board joints: water held on each joint ledge drips below it.
    dj = math('MODULO', math('SUBTRACT', top, z), P['board_h'])                 # metres below the joint above
    row = math('FLOOR', math('DIVIDE', math('SUBTRACT', top, z), P['board_h']))  # joint index -> its own pattern
    jx = math('ADD', x, math('MULTIPLY', math('SUBTRACT', noise(comb(math('MULTIPLY', x, 1.5), math('MULTIPLY', z, 4.0), 9.0), 1.0, detail=2.0), .5), .015))
    jstreak = ramp(noise(comb(math('MULTIPLY', jx, P['j_w']), math('MULTIPLY', dj, 2.0), math('MULTIPLY', row, 3.7)), 1.0, detail=2.0, rough=.5), P['j_thr'], P['j_thr'] + .16)
    jpresent = ramp(noise(comb(math('MULTIPLY', x, 2.2), math('MULTIPLY', row, 5.1), 1.7), 1.0, detail=1.0), 1.0 - P['j_density'], 1.0 - P['j_density'] + .15)
    jlen = math('ADD', P['j_len_min'], math('MULTIPLY', ramp(noise(comb(math('MULTIPLY', x, 9.0), math('MULTIPLY', row, 2.3), 4.2), 1.0, detail=1.0), .3, .7, False), P['j_len_span']))
    jfade = math('POWER', math('SUBTRACT', 1.0, math('DIVIDE', dj, jlen), True), 1.4)
    J = math('MULTIPLY', math('MULTIPLY', jstreak, jpresent), jfade)
    return J
