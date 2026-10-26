"""Probe: the piece planes (each picked F1 cell is planar; unpicked cells and grout stay at zero)."""

import os as _os
import sys as _sys
_CONTROLS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in [_CONTROLS] + [_os.path.join(_CONTROLS, _t) for _t in ('archviz', 'tile', 'material', 'effects', 'water', 'lighting', 'environment', 'regression')]:
    if _d not in _sys.path:
        _sys.path.append(_d)
import numpy as np

import materials.tile.tile_damage as tile_damage
from tile_damage_rig import PX, tile_rig, probe_rgb, tiles


def check_pieces(folder):
    """Each picked F1 cell is planar; unpicked cells and grout remain at zero."""
    sc,ob,mat=tile_rig(force_kind=1,chip_share=0,spall_density=0)
    data=probe_rgb(mat,folder,'piece_planes',('Piece Height','Piece','Crack Distance'),(.002,1,.05))
    ph=data[...,0]; ids=np.rint(data[...,1]*tile_damage.PIECE_BINS).astype(int)
    valid=data[...,2]>3*PX
    moved=0.; fitted=0; residual=0.
    for index,face,x0,X,Y in tiles(ph.shape):
        for value in np.unique(ids[face&valid]):
            mask=face&valid&(ids==value)
            if mask.sum()<10: continue
            A=np.c_[X[mask],Y[mask],np.ones(mask.sum())]
            coef=np.linalg.lstsq(A,ph[mask],rcond=None)[0]
            error=float(np.max(np.abs(A@coef-ph[mask])))
            assert error<2e-7, f'{index}/{value}: not planar {error}'
            residual=max(residual,error); fitted+=1
            moved=max(moved,float(np.max(np.abs(ph[mask]))))
        assert np.max(np.abs(ph[face&(ids==0)]))<1e-9, 'Unpicked area moved'
    assert fitted>=2 and moved>.3*.00015
    faces=np.logical_or.reduce([mask for _,mask,*_ in tiles(ph.shape)])
    assert np.max(np.abs(ph[~faces]))<1e-9, 'Height leaks into grout'
    return dict(piece_max_lift_m=moved,piece_plane_max_residual_m=residual,piece_cells_fitted=fitted)
