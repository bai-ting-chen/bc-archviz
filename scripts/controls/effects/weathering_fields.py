"""Weathering look fields: runoff, base patches and board-joint leaks."""

import os as _os, sys as _sys
_sys.path.append(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import controls_import_paths  # noqa: E402,F401 -- every controls topic folder on sys.path
def runoff(math, comb, noise, ramp, x, z, top, settings):
    """Build the top-fed clustered runoff field."""
    # 1. run-off streaks: narrow along x, long along z; start at the top, each streak with its own length.
    xw = math('ADD', x, math('MULTIPLY', math('SUBTRACT', noise(comb(math('MULTIPLY', x, .7), math('MULTIPLY', z, 2.2), 5.0), 1.0, detail=2.0), .5), settings['wiggle']))  # meandering edges
    fine = ramp(noise(comb(math('MULTIPLY', xw, settings['streak_frequency_per_m']), math('MULTIPLY', z, settings['streak_vertical_frequency_per_m']), 0.0), 1.0, detail=3.0, rough=.55), settings['streak_thr'], settings['streak_thr'] + .18)
    wide = ramp(noise(comb(math('MULTIPLY', xw, settings['streak_frequency_per_m'] * .4), math('MULTIPLY', z, settings['streak_vertical_frequency_per_m'] * .7), 2.0), 1.0, detail=2.0, rough=.5), settings['streak_thr'] + .02, settings['streak_thr'] + .22)
    cluster = ramp(noise(comb(math('MULTIPLY', x, settings['cluster_scale']), 0, 4.4), 1.0, detail=1.0), settings['cluster_thr'], settings['cluster_thr'] + .2)
    streak = math('MULTIPLY', math('MAXIMUM', fine, math('MULTIPLY', wide, .75)), cluster)
    length = math('ADD', settings['len_min'], math('MULTIPLY', ramp(noise(comb(math('MULTIPLY', x, 1.6), 0, 7.3), 1.0, detail=1.0), .3, .7, False), settings['len_span']))
    depth = math('SUBTRACT', top, z)
    fade = math('SUBTRACT', 1.0, math('DIVIDE', depth, length), True)   # 1 at top -> 0 at its length
    fade = math('POWER', fade, settings['fade_pow'])
    S = math('MULTIPLY', streak, fade)
    return S

def zones(math, comb, noise, ramp, x, z, top, settings):
    """Build base damp, broad patches and blotches."""
    # 2. base zone: dark at the foot, irregular top edge.
    edge = math('ADD', settings['base_h'], math('MULTIPLY', math('SUBTRACT', noise(comb(math('MULTIPLY', x, .9), 3.1, 0), 1.0, detail=3.0), .5), .7))
    B = ramp(math('SUBTRACT', edge, z), -.15, .25)
    # 3. large soft patches (1-3 m), signed.
    C = math('SUBTRACT', ramp(noise(comb(x, 0, math('MULTIPLY', z, 1.3)), settings['patch_scale'], detail=2.0, rough=.5), .3, .7, False), .5)
    # 4. medium blotches, signed.
    D = math('SUBTRACT', ramp(noise(comb(x, 11.0, z), settings['blot_scale'], detail=4.0, rough=.6), .3, .7, False), .5)
    return B, C, D

def joint_leaks(math, comb, noise, ramp, x, z, top, settings):
    """Build short leaks held at each horizontal joint."""
    # 6. small leaks from board joints: water held on each joint ledge drips below it.
    dj = math('MODULO', math('SUBTRACT', top, z), settings['board_h'])                 # metres below the joint above
    row = math('FLOOR', math('DIVIDE', math('SUBTRACT', top, z), settings['board_h']))  # joint index -> its own pattern
    jx = math('ADD', x, math('MULTIPLY', math('SUBTRACT', noise(comb(math('MULTIPLY', x, 1.5), math('MULTIPLY', z, 4.0), 9.0), 1.0, detail=2.0), .5), .015))
    jstreak = ramp(noise(comb(math('MULTIPLY', jx, settings['j_w']), math('MULTIPLY', dj, 2.0), math('MULTIPLY', row, 3.7)), 1.0, detail=2.0, rough=.5), settings['j_thr'], settings['j_thr'] + .16)
    jpresent = ramp(noise(comb(math('MULTIPLY', x, 2.2), math('MULTIPLY', row, 5.1), 1.7), 1.0, detail=1.0), 1.0 - settings['j_density'], 1.0 - settings['j_density'] + .15)
    jlen = math('ADD', settings['j_len_min'], math('MULTIPLY', ramp(noise(comb(math('MULTIPLY', x, 9.0), math('MULTIPLY', row, 2.3), 4.2), 1.0, detail=1.0), .3, .7, False), settings['j_len_span']))
    jfade = math('POWER', math('SUBTRACT', 1.0, math('DIVIDE', dj, jlen), True), 1.4)
    J = math('MULTIPLY', math('MULTIPLY', jstreak, jpresent), jfade)
    return J
