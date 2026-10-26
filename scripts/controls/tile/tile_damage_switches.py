"""Probe: the damage switch in the rendered image (on, off, and fraction zero must agree)."""

import os as _os
import sys as _sys
_CONTROLS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in [_CONTROLS] + [_os.path.join(_CONTROLS, _t) for _t in ('archviz', 'tile', 'material', 'effects', 'water', 'lighting', 'environment', 'regression')]:
    if _d not in _sys.path:
        _sys.path.append(_d)
import numpy as np

import materials.tile.tile_surface as tile_surface
from tile_damage_rig import probe_rgb, render, setup


def check_onoff(folder):
    """Compare actual surface renders with the switch and fraction-zero paths."""
    # Cracks prove the switch; chips at zero-width joints leak one bump-sampled pixel into the neighbour (chip WIP).
    sc,ob,mat=setup(.3,.3,400,400,tile_w=.0375,tile_h=.25,joint=0,damage=.5,force_kind=1)
    sc.cycles.samples=4
    enabled=render(folder,'on')
    selected=probe_rgb(mat,folder,'on_selection',('Damaged',None,None))[...,0]>.5
    tile_surface.toggle(mat,'damage',False); disabled=render(folder,'off')
    tile_surface.set_param(mat,'damage',0); tile_surface.toggle(mat,'damage',True)
    zero=render(folder,'on_zero')
    assert np.max(np.abs(disabled-zero))<1e-6
    assert selected.any() and (~selected).any()
    assert np.max(np.abs(enabled-disabled)[~selected])<1e-6
    assert np.max(np.abs(enabled-disabled)[selected])>1e-5
