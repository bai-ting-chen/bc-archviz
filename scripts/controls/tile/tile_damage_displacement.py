"""Probes: true displacement of the damage (crack pieces, chips, and damage-only), against the bump reference."""

import os as _os
import sys as _sys
_CONTROLS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in [_CONTROLS] + [_os.path.join(_CONTROLS, _t) for _t in ('archviz', 'tile', 'material', 'effects', 'water', 'lighting', 'environment', 'regression')]:
    if _d not in _sys.path:
        _sys.path.append(_d)
import json
import math

import numpy as np

import materials.tile.tile_damage as tile_damage
import materials.tile.tile_surface as tile_surface
from tile_damage_geometry import dilate
from tile_damage_rig import H, PX, W, probe_rgb, setup


def displacement_case(folder,kind,whole=False):
    """Compare positions and world normals in an 8 mm, <=20 um-edge diced window."""
    kw=dict(force_kind=kind,chip_depth=.0015,chip_share=0,spall_density=0,joint=0,recess=.006)
    sc,ob,mat=setup(3*W,H,round(3*W/PX),round(H/PX),**kw)
    data=probe_rgb(mat,folder,f'locate_{kind}',('Chip Depth Out','Crack','Piece Height'),(.001,1,.002))
    if kind==2:
        yy,xx=np.unravel_index(np.argmax(data[...,0]),data[...,0].shape)
        centre=((xx+.5)*PX,(yy+.5)*PX)
    else:
        yy,xx=np.nonzero(data[...,1]>.02)
        assert len(yy), 'no crack for window location'
        at=len(yy)//2
        centre=((xx[at]+.5)*PX,(yy[at]+.5)*PX)
    tile_x=math.floor(centre[0]/W)*W
    origin=(min(max(centre[0]-.004,tile_x),tile_x+W-.008),min(max(centre[1]-.004,0),H-.008))
    width,height=(W,H) if whole else (.008,.008)
    origin=(0,0) if whole else origin
    nx,ny=(240,1600) if whole else (400,400)
    sc,ob,mat=setup(width,height,nx,ny,origin=origin,**kw)
    prefix=('whole_' if whole else '')+('chip' if kind==2 else 'piece')
    before=probe_rgb(mat,folder,prefix+'_expected',('Total Height','Piece Height','Crack'),(.01,.002,1))
    normals_before=probe_rgb(mat,folder,prefix+'_bump_normals',('Normal X','Normal Y','Normal Z'),(2,2,2))
    tile_surface.use_displacement(mat,[ob],pixel_size=.125 if whole else .5)
    assert max(width/nx,height/ny)*(.125 if whole else .5)<=.00002
    assert mat.displacement_method=='BOTH'
    assert all(mat.node_tree.nodes[n].inputs['Strength'].default_value==0 for n in ('TileBump','DamageBump'))
    assert mat.node_tree.nodes['ClayGrainBump'].inputs['Strength'].default_value>0
    after=probe_rgb(mat,folder,prefix+'_positions',('World Z','Chip Depth Out','Piece'),(.02,.001,1))
    normals=probe_rgb(mat,folder,prefix+'_world_normals',('Normal X','Normal Y','Normal Z'),(2,2,2))
    ids=np.rint(after[...,2]*tile_damage.PIECE_BINS).astype(int)
    edges=np.zeros(ids.shape,bool)
    edges[1:]|=ids[1:]!=ids[:-1]; edges[:-1]|=ids[1:]!=ids[:-1]
    edges[:,1:]|=ids[:,1:]!=ids[:,:-1]; edges[:,:-1]|=ids[:,1:]!=ids[:,:-1]
    mask=(after[...,1]>.0006) if kind==2 else ~dilate((before[...,2]>.02)|edges,3)
    mask[:3]=mask[-3:]=False; mask[:,:3]=mask[:,-3:]=False
    assert mask.any(), prefix+': no interior samples'
    error=np.abs(after[...,0][mask]-before[...,0][mask])
    metrics={prefix+'_position_mean_m':float(error.mean()),prefix+'_position_max_m':float(error.max()),
             prefix+'_interior_pixels':int(mask.sum()),prefix+'_dicing_edge_m':max(width/nx,height/ny)*(.125 if whole else .5)}
    if not whole: assert error.mean()<5e-6 and error.max()<1e-4, metrics
    if kind==1:
        yy,xx=np.meshgrid(origin[1]+(np.arange(ny)+.5)*height/ny,origin[0]+(np.arange(nx)+.5)*width/nx,indexing='ij')
        errors=[]
        for value in np.unique(ids[mask]):
            m=mask&(ids==value)
            if m.sum()<10: continue
            A=np.c_[xx[m],yy[m],np.ones(m.sum())]
            coef=np.linalg.lstsq(A,before[...,1][m],rcond=None)[0]
            expected=np.array([-coef[0],-coef[1],1.]); expected/=np.linalg.norm(expected)
            actual=normals[m]; actual/=np.linalg.norm(actual,axis=1)[:,None]
            errors.extend(np.degrees(np.arccos(np.clip(actual@expected,-1,1))))
        median,p95=np.percentile(errors,(50,95))
        metrics.update(piece_normal_median_deg=float(median),piece_normal_p95_deg=float(p95))
        if not whole: assert median<.03 and p95<.1, metrics
    else:
        angle=lambda n: np.degrees(np.arccos(np.clip(n[...,2]/np.linalg.norm(n,axis=-1),-1,1)))
        delta=abs(np.mean(angle(normals)[mask])-np.mean(angle(normals_before)[mask]))
        metrics['chip_mean_normal_error_deg']=float(delta)
        if not whole: assert delta<3, metrics
    tile_surface.set_param(mat,'uv','TileUV')
    assert next(n for n in mat.node_tree.nodes if n.type=='OUTPUT_MATERIAL').inputs['Displacement'].is_linked
    tile_surface.use_bump(mat)
    assert all(mat.node_tree.nodes[n].inputs['Strength'].default_value==1 for n in ('TileBump','DamageBump'))
    return metrics


def check_displacement(folder,full=False):
    """Crack pieces: strict window case; the optional whole-tile comparison is evidence only."""
    metrics=displacement_case(folder,1)
    if full: metrics.update(displacement_case(folder,1,whole=True))
    return metrics


def check_chip_displacement(folder,full=False):
    """Chips: strict window case; the optional whole-tile comparison is evidence only."""
    metrics=displacement_case(folder,2)
    if full: metrics.update(displacement_case(folder,2,whole=True))
    return metrics


def check_damage_displacement(folder,full=False):
    """Damage-only displacement moves the mesh by the damage height alone, survives a rebuild, use_bump undoes it."""
    kw=dict(force_kind=1,chip_share=0,spall_density=0,joint=0,step_height=.0003)
    sc,ob,mat=setup(3*W,H,round(3*W/PX),round(H/PX),**kw)
    data=probe_rgb(mat,folder,'damage_locate',('Crack','Piece Height',None),(1,.002,1))
    yy,xx=np.nonzero(data[...,0]>.02); assert len(yy), 'no crack for window location'
    at=len(yy)//2; centre=((xx[at]+.5)*PX,(yy[at]+.5)*PX)
    tile_x=math.floor(centre[0]/W)*W
    origin=(min(max(centre[0]-.004,tile_x),tile_x+W-.008),min(max(centre[1]-.004,0),H-.008))
    sc,ob,mat=setup(.008,.008,400,400,origin=origin,**kw)
    before=probe_rgb(mat,folder,'damage_expected',('Damage Height','Crack',None),(.002,1,1))
    tile_surface.use_damage_displacement(mat,[ob],pixel_size=.5)
    nodes=mat.node_tree.nodes
    linked=lambda: [l.from_node.name for l in next(n for n in nodes if n.type=='OUTPUT_MATERIAL').inputs['Displacement'].links]
    assert linked()==['DamageDisplacement'] and nodes['DamageDisplacementOn'].outputs[0].default_value==1
    after=probe_rgb(mat,folder,'damage_positions',('World Z',None,None),(.02,1,1))[...,0]
    # Exclude steep steps (crack cuts and piece steps where the line has faded): dicing cannot follow a vertical wall.
    hgt=before[...,0]; step=np.zeros(hgt.shape,bool)
    step[1:]|=np.abs(np.diff(hgt,axis=0))>5e-6; step[:,1:]|=np.abs(np.diff(hgt,axis=1))>5e-6
    cut=dilate((before[...,1]>.02)|step,3); cut[:3]=cut[-3:]=True; cut[:,:3]=cut[:,-3:]=True   # also skip the border
    damaged=(np.abs(before[...,0])>1e-6)&~cut; still=(np.abs(before[...,0])<1e-9)&~cut
    assert damaged.any(), 'no displaced piece in window'
    err=np.abs(after-before[...,0])[~cut]
    metrics=dict(damage_disp_mean_m=float(err.mean()),damage_disp_max_m=float(err.max()),
                 damage_disp_still_max_m=float(np.abs(after[still]).max()) if still.any() else 0.)
    assert err.mean()<5e-6 and err.max()<1e-4, metrics
    assert metrics['damage_disp_still_max_m']<1e-6, metrics     # profile, joints and undamaged face stay put
    mat=tile_surface.set_param(mat,'uv','TileUV')                 # structural rebuild keeps mode and objects
    settings=json.loads(mat['tile_surface_settings'])
    assert settings['displacement']=='damage' and settings['displaced_objects']==[ob.name], settings
    assert linked()==['DamageDisplacement']
    tile_surface.use_bump(mat)
    assert linked()==[] and nodes['DamageDisplacementOn'].outputs[0].default_value==0
    assert json.loads(mat['tile_surface_settings'])['displacement'] is False
    return metrics
