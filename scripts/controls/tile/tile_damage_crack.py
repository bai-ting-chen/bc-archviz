"""Probe: the crack network (occurrence, direction spread, height reach, depth on the line, width)."""

import os as _os
import sys as _sys
_CONTROLS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in [_CONTROLS] + [_os.path.join(_CONTROLS, _t) for _t in ('archviz', 'tile', 'material', 'effects', 'water', 'lighting', 'environment', 'regression')]:
    if _d not in _sys.path:
        _sys.path.append(_d)
import json

import numpy as np

import materials.tile.tile_surface as tile_surface
from tile_damage_geometry import components, dilate, local_directions
from tile_damage_rig import PX, H, grid_faces, grid_rig, probe_rgb


def check_crack(folder):
    """Crack occurrence, local-direction spread, height coverage, depth on the line and width response."""
    # A network spans the whole tile, so per-tile centroid/PCA always reads 'mid-tile, along the tile':
    # variety is measured per crack pixel (local direction) and by the heights the cracks reach.
    sc,ob,mat=grid_rig(12,6,force_kind=1,chip_share=0,spall_density=0)
    data=probe_rgb(mat,folder,'network_12',('Crack','Dirt','Crack Distance'),(1,1,.05))
    directions=[]; heights=[]; multiple=0; present=0
    for index,face,_ in grid_faces(data,12,6):
        mask=face[...,0]>.02
        if mask.sum()<3: continue
        present+=1
        yy,xx=np.nonzero(mask)
        heights.extend((yy+.5)*PX/H)
        directions.extend(local_directions(mask)[mask])
        # Close subpixel raster gaps only, then count separated visible runs.
        runs=components(dilate(mask))
        multiple+=sum(n>=12 for n in runs)>=2
    hist=np.histogram(directions,bins=6,range=(0,180))[0]/max(len(directions),1)
    direction_bins=int((hist>=.05).sum())
    height_bands=int((np.histogram(heights,bins=10,range=(0,1))[0]>0).sum())
    summary=dict(crack_tiles_present=present,crack_direction_bins_of_6=direction_bins,
                 crack_height_bands_of_10=height_bands,crack_tiles_multiple_runs=int(multiple),
                 crack_direction_histogram=[round(float(h),3) for h in hist])
    (folder/'network_metrics.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print('TILE_DAMAGE_CRACK_METRICS',json.dumps(summary),flush=True)
    dirt=data[...,1]; crack=data[...,0]>.02
    assert not ((dirt>1e-6)&(data[...,2]>.004+PX)).any(), 'Dirt beyond network distance bound'
    assert (dirt[crack]<.1).any() and (dirt[crack]>.5).any(), 'Dirt is not patchy'
    tile_surface.set_param(mat,'crack_dirt',0)
    assert np.max(probe_rgb(mat,folder,'dirt_zero',('Dirt',None,None)))<1e-8
    assert present>=10 and direction_bins>=4 and height_bands>=7 and multiple>=1, summary
    # Depth on the line = glaze + slip + Crack Depth (defaults), and the drawn width follows Crack Width.
    tile_surface.set_param(mat,'crack_dirt',.85)
    depth=probe_rgb(mat,folder,'crack_depth',('Crack','Crack Depth Out',None),(1,.002,1))
    line=depth[...,0]>.2                                   # Crack fades with the patch mask; depth fades with it
    expected=.0003+.0002+.0008
    per_unit=np.median(depth[...,1][line]/depth[...,0][line])
    assert line.any() and abs(per_unit-expected)<.05*expected, float(per_unit)
    tile_surface.set_param(mat,'crack_width',.00054)
    wide=probe_rgb(mat,folder,'crack_wide',('Crack',None,None))[...,0]>.02
    ratio=wide.sum()/max(crack.sum(),1)
    assert ratio>1.8, f'crack width does not follow Crack Width (x3 -> pixels x{ratio:.2f})'
    summary['crack_width_x3_pixel_ratio']=float(ratio)
    return summary
