"""Probes: how the damage follows the tile layout (square tiles, rotation and jitter, and the fraction rate)."""

import os as _os
import sys as _sys
_CONTROLS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in [_CONTROLS] + [_os.path.join(_CONTROLS, _t) for _t in ('archviz', 'tile', 'material', 'effects', 'water', 'lighting', 'environment', 'regression')]:
    if _d not in _sys.path:
        _sys.path.append(_d)
import numpy as np

import materials.tile.tile_surface as tile_surface
from tile_damage_rig import PX, probe_rgb, setup


def check_square(folder):
    """The network survives square tiles and fine chips remain inside mosaics."""
    pitch=.102
    sc,ob,mat=setup(4*pitch,5*pitch,round(4*pitch/PX),round(5*pitch/PX),tile_w=.1,tile_h=.1,
                    joint=.002,force_kind=1,chip_share=0,spall_density=0)
    data=probe_rgb(mat,folder,'square_20',('Crack','Piece Height',None),(1,.002,1))
    cells=0
    for row in range(5):
        for col in range(4):
            x0,y0=round((col*pitch+.001)/PX),round((row*pitch+.001)/PX)
            cells+=(data[y0:y0+400,x0:x0+400,0]>.02).any()
    assert cells>=10, f'Square crack occurrence {cells}/20'
    sc,ob,mat=setup(.033,.033,132,132,tile_w=.01,tile_h=.01,joint=.001,force_kind=2,chip_size=.008)
    data=probe_rgb(mat,folder,'mosaic',('Chip Depth Out','UV X','UV Y'),(.002,1,1))
    shell=data[...,0]>1e-6
    assert shell.any()
    assert np.all((data[...,1:][shell]>=0)&(data[...,1:][shell]<=1)), 'Mosaic chip outside tile'
    return {'square_crack_tiles':int(cells)}


def check_rotated(folder):
    """The same eligibility and containment hold after rotation, jitter and swapped axes."""
    sc,ob,mat=setup(.3,.3,1200,1200,tile_w=.25,tile_h=.0375,rotation=.43,
                    jitter_rotation_deg=.6,jitter_offset=.0003,force_kind=2)
    data=probe_rgb(mat,folder,'rotated_sites',('Chip Depth Out','Chip Site Edge','Chip Cell'),(.002,.01,.01))
    shell=data[...,0]>1e-6
    assert shell.any() and np.all(data[...,1][shell]<.6*data[...,2][shell]+1e-8)
    uv=probe_rgb(mat,folder,'rotated_uv',('Chip Depth Out','UV X','UV Y'),(.002,1,1))
    assert np.all((uv[...,1:][shell]>=0)&(uv[...,1:][shell]<=1)), 'Rotated chip outside tile'


def check_rate(folder):
    """Sample tile centres; zero fraction clears all physical outputs."""
    sc,ob,mat=setup(3,3,1200,1200,tile_w=.0375,tile_h=.25,damage=.05)
    data=probe_rgb(mat,folder,'rate',('Damaged',None,None))[...,0]
    cols=np.arange(int(3/.0405)); rows=np.arange(int(3/.253))
    ix=((cols*.0405+.0015+.0375/2)/3*1200).astype(int)
    iy=((rows*.253+.0015+.25/2)/3*1200).astype(int)
    rate=np.mean(data[np.ix_(iy,ix)]>.5)
    assert abs(rate-.05)<=.015, rate
    tile_surface.set_param(mat,'damage',0)
    for names in (('Chip Depth Out','Piece Height','Crack'),('Glaze Lip','Engobe','Body'),('Damaged','Kind','Crack Depth Out')):
        assert np.max(np.abs(probe_rgb(mat,folder,'zero_'+'_'.join(n.replace(' ','') for n in names),names)))<1e-8
    return {'fraction':float(rate)}
