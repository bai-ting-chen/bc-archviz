"""Probes: chips (fine-cell chip counts, areas, containment, the glaze step), flakes and spalls.

Chip look is still in development: check_chips, check_flakes and the layer step report WIP warnings
through tile_damage_check (WIP), they do not fail the run.
"""

import os as _os
import sys as _sys
_CONTROLS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in [_CONTROLS] + [_os.path.join(_CONTROLS, _t) for _t in ('archviz', 'tile', 'material', 'effects', 'water', 'lighting', 'environment', 'regression')]:
    if _d not in _sys.path:
        _sys.path.append(_d)
import numpy as np

import materials.tile.tile_damage as tile_damage
import materials.tile.tile_surface as tile_surface
from tile_damage_geometry import boundary, dilate
from tile_damage_rig import ENGOBE, GLAZE, H, J, PX, W, grid_faces, grid_rig, probe_rgb, setup, tile_rig


def check_chip_layers(folder,origin):
    """Check positive lip coverage/order and a true 10 um glaze step in small windows."""
    sc,ob,mat=setup(.008,.008,160,160,origin=origin,force_kind=2)
    data=probe_rgb(mat,folder,'layers_50um',('Glaze Lip','Engobe','Body'))
    codes=np.argmax(data,axis=-1)+1; codes[np.max(data,axis=-1)<.5]=0
    assert (codes==1).any() and (codes==2).any(), 'Missing lip/slip'
    for image in (codes,codes.T):
        assert not (((image[:,:-1]==0)&(image[:,1:]>1))|((image[:,1:]==0)&(image[:,:-1]>1))).any(), 'Glaze skips Lip'
        assert not (((image[:,:-1]==1)&(image[:,1:]==3))|((image[:,1:]==1)&(image[:,:-1]==3))).any(), 'Lip skips Engobe'
    yy,xx=np.nonzero(boundary(codes>0))
    gx=origin[0]+(xx+.5)*.00005; gy=origin[1]+(yy+.5)*.00005
    lx=np.mod(gx,W+J)-J/2; ly=np.mod(gy,H+J)-J/2
    good=(xx>3)&(xx<156)&(yy>3)&(yy<156)&(lx>.0005)&(lx<W-.0005)&(ly>.0005)&(ly<H-.0005)
    candidates=np.flatnonzero(good)
    assert len(candidates), 'No interior glaze edge in layer window'
    at=candidates[len(candidates)//2]
    fine_origin=(gx[at]-.001,gy[at]-.001)
    sc,ob,mat=setup(.002,.002,200,200,origin=fine_origin,force_kind=2)
    depth=probe_rgb(mat,folder,'edge_10um',('Chip Depth Out',None,None),(.002,1,1))[...,0]
    widths=[]
    for line in list(depth)+list(depth.T):
        for values in (line,line[::-1]):
            for start in np.flatnonzero((values[:-1]<.1*GLAZE)&(values[1:]>=.1*GLAZE)):
                stops=np.flatnonzero(values[start+1:]>=.9*GLAZE)
                if len(stops): widths.append((stops[0]+1)*.00001)
    assert widths and max(widths)<=.00003+1e-12, f'Glaze transition {widths}'
    return max(widths)


def check_chips(folder):
    """Measure real fine-cell chips, their variety, containment and coating-only cases."""
    sc,ob,mat=grid_rig(20,10,force_kind=2)
    data=probe_rgb(mat,folder,'chips_20',('Chip Depth Out','Chip','Body'),(.002,1,1))
    layers=probe_rgb(mat,folder,'chip_layers_20',('Glaze Lip','Engobe','Body'))
    counts=[]; areas=[]; masks=[]; edge_chips=0; coating=0; lip_cover=[]; selected_origin=None
    outside=np.ones(data.shape[:2],bool)
    for (index,face,origin),(_,strata,_) in zip(grid_faces(data,20,10),grid_faces(layers,20,10)):
        ids=np.rint(face[...,1]*tile_damage.PIECE_BINS).astype(int)
        masks.append(face[...,0]>1e-6)
        values=np.unique(ids[ids>0]); counts.append(len(values))
        yy,xx=np.indices(ids.shape); xx=(xx+.5)*PX; yy=(yy+.5)*PX
        arris=np.minimum.reduce([xx,W-xx,yy,H-yy])
        for value in values:
            cell=ids==value; areas.append(int(cell.sum()))
            corner=(xx<2*PX)&(yy<2*PX)|(xx>W-2*PX)&(yy<2*PX)|(xx<2*PX)&(yy>H-2*PX)|(xx>W-2*PX)&(yy>H-2*PX)
            edge_chips+=not (cell&corner).any()
            coating+=not (face[...,2][cell]>.5).any() and face[...,0][cell].max()<=GLAZE+1e-8
            rim=boundary(cell)&(arris>2*PX)
            if rim.sum()>=3:
                lip_cover.append(float(np.mean(dilate(strata[...,0]>.5)[rim])))
        x0=round(origin[0]/PX); y0=round(origin[1]/PX)
        outside[y0:y0+ids.shape[0],x0:x0+ids.shape[1]]=False
        if selected_origin is None:
            candidates=np.argwhere(boundary(masks[-1])&(arris>.001))
            if len(candidates):
                y,x=candidates[len(candidates)//2]
                cx,cy=origin[0]+(x+.5)*PX,origin[1]+(y+.5)*PX
                selected_origin=(min(max(cx-.004,origin[0]),origin[0]+W-.008),min(max(cy-.004,origin[1]),origin[1]+H-.008))
    assert len(set(counts))>=3, f'Chip counts {counts}'
    ratio=max(areas)/min(areas)
    assert ratio>=6, f'Chip area ratio {ratio}'
    assert edge_chips and coating, 'Missing noncorner or glaze-only chips'
    assert np.max(data[...,0][outside])<1e-8, 'Chip outside tile face'
    assert lip_cover and min(lip_cover)>=.6, f'Lip coverage min {min(lip_cover) if lip_cover else 0}'
    ious=[]
    for index,mask in enumerate(masks):
        for other in masks[:index]:
            union=np.count_nonzero(mask|other)
            if union: ious.append(np.count_nonzero(mask&other)/union)
    assert ious and max(ious)<.5, f'Chip mask max IoU {max(ious)}'
    assert selected_origin is not None
    transition=check_chip_layers(folder,selected_origin)
    sc,ob,mat=tile_rig(force_kind=2,chip_depth=.0004)
    shallow=probe_rgb(mat,folder,'shallow',('Chip Depth Out','Body',None),(.002,1,1))
    shell=shallow[...,0]>1e-6
    assert shell.any() and np.mean(shallow[...,1][shell]>.5)<.05
    tile_surface.set_param(mat,'chip_depth',0)
    zero=probe_rgb(mat,folder,'zero_depth',('Chip Depth Out','Body',None),(.002,1,1))
    assert np.max(zero[...,0])<=GLAZE+1e-8 and np.max(zero[...,1])<1e-8
    return dict(chip_counts=counts,chip_area_ratio=ratio,chip_noncorner_cells=int(edge_chips),
                chip_glaze_only_cells=int(coating),chip_mask_max_iou=float(max(ious)),
                chip_lip_coverage_min=min(lip_cover),edge_transition_max_m=transition)


def check_flakes(folder):
    """Selected outline cells are glaze-only and satisfy the site-distance rule."""
    sc,ob,mat=tile_rig(force_kind=3)
    data=probe_rgb(mat,folder,'flakes',('Chip Depth Out','Chip Site Edge','Chip Cell'),(.002,.01,.01))
    shell=data[...,0]>1e-6
    assert shell.any() and data[...,0][shell].max()<=GLAZE+1e-8
    assert np.all(data[...,1][shell]<.6*data[...,2][shell]+1e-8)


def check_spalls(folder):
    """The allowed pixel-distance approximation stays on picked crack-cell walls."""
    sc,ob,mat=tile_rig(force_kind=1,chip_share=0,spall_density=1)
    data=probe_rgb(mat,folder,'spalls',('Chip Depth Out','Crack Distance','Picked'),(.002,.05,1))
    shell=data[...,0]>1e-6
    assert shell.any()
    assert np.all(data[...,1][shell]<.001+1e-8) and np.all(data[...,2][shell]>.5)
    assert data[...,0][shell].max()<=GLAZE+ENGOBE+1e-8
    tile_surface.set_param(mat,'spall_density',0)
    assert np.max(probe_rgb(mat,folder,'spalls_zero',('Chip Depth Out',None,None)))<1e-8
