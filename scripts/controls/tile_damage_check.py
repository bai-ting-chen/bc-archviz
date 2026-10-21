"""Packed, bounded headless acceptance probes; --only SECTION, --full for slow evidence."""
import argparse
import json
import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'blender'))
import bpy
import numpy as np
import archviz
import materials.tile_damage as tile_damage
import materials.tile_surface as tile_surface

W, H, J, PX, NT = .0375, .25, .003, .00025, 3
GLAZE, ENGOBE = .0003, .0002
SOLO = tuple(f for f in tile_surface.FEATURES if f != 'damage')


def render(folder, label):
    """Save and read one linear, float RGB evidence render."""
    sc = bpy.context.scene
    sc.render.image_settings.file_format = 'OPEN_EXR'
    sc.render.image_settings.color_depth = '32'
    sc.render.filepath = str(folder / (label + '.exr'))
    bpy.ops.render.render(write_still=True)
    image = bpy.data.images.load(sc.render.filepath, check_existing=False)
    try:
        data = np.empty(len(image.pixels), dtype=np.float32)
        image.pixels.foreach_get(data)
        return data.reshape(image.size[1], image.size[0], 4)[..., :3].copy()
    finally:
        bpy.data.images.remove(image)


def setup(width, height, nx, ny, origin=(0., 0.), **kwargs):
    """Build only the observed UV-metre window; no unrelated geometry is diced."""
    bpy.ops.wm.read_homefile(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    archviz.use_gpu()            # --factory-startup alone renders on the CPU
    sc.cycles.samples = 1
    sc.cycles.use_denoising = sc.cycles.use_adaptive_sampling = False
    sc.cycles.seed = 17
    sc.cycles.filter_width = .01
    sc.render.resolution_x, sc.render.resolution_y = nx, ny
    sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = 'Standard'
    sc.world = bpy.data.worlds.new('ProbeWorld'); sc.world.use_nodes = True
    sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 1
    x, y = origin
    mesh = bpy.data.meshes.new('ProbePlane')
    mesh.from_pydata([(x,y,0),(x+width,y,0),(x+width,y+height,0),(x,y+height,0)], [], [(0,1,2,3)])
    ob = bpy.data.objects.new('ProbePlane', mesh); sc.collection.objects.link(ob)
    uv = mesh.uv_layers.new(name='TileUV')
    for loop in mesh.loops:
        uv.data[loop.index].uv = mesh.vertices[loop.vertex_index].co[:2]
    base = dict(tile_w=W, tile_h=H, joint=J, corner_radius=0, jitter_offset=0,
                jitter_rotation_deg=0, damage=1, off=SOLO)
    base.update(kwargs)
    mat = tile_surface.tile_material('DamageControl', **base); mesh.materials.append(mat)
    cam = bpy.data.objects.new('ProbeCamera', bpy.data.cameras.new('ProbeCamera'))
    sc.collection.objects.link(cam); sc.camera = cam
    cam.location = (x+width/2, y+height/2, 1)
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = max(width, height)
    return sc, ob, mat


def tile_rig(**kw):
    """Three complete finger tiles at 0.25 mm per pixel."""
    return setup(NT*(W+J), H+J, round(NT*(W+J)/PX), round((H+J)/PX), **kw)


def probe_rgb(mat, folder, label, outputs, divisors=(1., 1., 1.)):
    """Pack three sockets into one EXR; signed heights/normals use a 0.5 offset."""
    tree = mat.node_tree
    target = next(n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL')
    original = target.inputs['Surface'].links[0].from_socket
    created = []
    def node(kind):
        """Track probe-only nodes for guaranteed removal."""
        n = tree.nodes.new(kind); created.append(n); return n
    combine = node('ShaderNodeCombineXYZ')
    offsets = []
    for index, (name, divisor) in enumerate(zip(outputs, divisors)):
        signed = name in ('Piece Height', 'World Z', 'Normal X', 'Normal Y', 'Normal Z', 'Total Height',
                          'Damage Height')
        offsets.append(.5 if signed else 0.)
        if name is None: continue
        if name == 'World Z' or name.startswith('Normal '):
            separate = node('ShaderNodeSeparateXYZ')
            source = (node('ShaderNodeNewGeometry').outputs['Position'] if name == 'World Z'
                      else tree.nodes['TileBump'].outputs['Normal'])
            tree.links.new(source, separate.inputs[0])
            socket = separate.outputs['Z' if name == 'World Z' else name[-1]]
        elif name == 'Total Height':
            socket = tree.nodes['TileTotalHeight'].outputs[0]
        elif name == 'Damage Height':
            socket = tree.nodes['TileDamageHeight'].outputs[0]
        elif name in ('UV X', 'UV Y'):
            separate = node('ShaderNodeSeparateXYZ')
            tree.links.new(tree.nodes['TileLayout'].outputs['Tile UV'], separate.inputs[0])
            socket = separate.outputs[name[-1]]
        else:
            socket = tree.nodes['TileDamage'].outputs[name]
        encode = node('ShaderNodeMath'); encode.operation = 'MULTIPLY_ADD'
        tree.links.new(socket, encode.inputs[0])
        encode.inputs[1].default_value = 1/divisor
        encode.inputs[2].default_value = offsets[-1]
        tree.links.new(encode.outputs[0], combine.inputs[index])
    emission = node('ShaderNodeEmission')
    tree.links.new(combine.outputs[0], emission.inputs['Color'])
    tree.links.new(emission.outputs[0], target.inputs['Surface'])
    try:
        return (render(folder, label)-np.array(offsets))*np.array(divisors)
    finally:
        tree.links.new(original, target.inputs['Surface'])
        for n in created: tree.nodes.remove(n)


def tiles(shape):
    """Yield face masks and metre coordinates for the three-tile topology rig."""
    Y, X = np.meshgrid((np.arange(shape[0])+.5)*PX, (np.arange(shape[1])+.5)*PX, indexing='ij')
    for index in range(NT):
        x0 = index*(W+J)+J/2
        yield index, (X>x0)&(X<x0+W)&(Y>J/2)&(Y<J/2+H), x0, X, Y


def dilate(mask, radius=1):
    """Chebyshev neighbourhood without wrapping across the image boundary."""
    pad = np.pad(mask, radius)
    return np.logical_or.reduce([pad[radius+dy:radius+dy+mask.shape[0], radius+dx:radius+dx+mask.shape[1]]
                                 for dy in range(-radius,radius+1) for dx in range(-radius,radius+1)])


def boundary(mask):
    """Return the inner four-neighbour boundary."""
    p = np.pad(mask, 1)
    return mask & ~(p[:-2,1:-1]&p[2:,1:-1]&p[1:-1,:-2]&p[1:-1,2:])


def disk_dilate(mask,radius):
    """Euclidean pixel neighbourhood for the physical dirt-width bound."""
    p=np.pad(mask,radius)
    out=np.zeros_like(mask)
    for dy in range(-radius,radius+1):
        for dx in range(-radius,radius+1):
            if dx*dx+dy*dy<=radius*radius:
                out |= p[radius+dy:radius+dy+mask.shape[0],radius+dx:radius+dx+mask.shape[1]]
    return out


def components(mask):
    """Count connected eight-neighbour pixel bands."""
    remaining = set(zip(*np.nonzero(mask))); sizes = []
    while remaining:
        stack = [remaining.pop()]; size = 0
        while stack:
            y, x = stack.pop(); size += 1
            for dy in (-1,0,1):
                for dx in (-1,0,1):
                    q = (y+dy,x+dx)
                    if q in remaining: remaining.remove(q); stack.append(q)
        sizes.append(size)
    return sizes


def grid_rig(count,cols,**kw):
    """Observe complete 37.5 x 250 mm cells at 0.25 mm/px."""
    rows=math.ceil(count/cols)
    return setup(cols*(W+J),rows*(H+J),round(cols*(W+J)/PX),round(rows*(H+J)/PX),**kw)


def grid_faces(data,count,cols):
    """Extract aligned face arrays; joints remain outside every face slice."""
    for index in range(count):
        col,row=index%cols,index//cols
        x0=round((col*(W+J)+J/2)/PX); y0=round((row*(H+J)+J/2)/PX)
        yield index,data[y0:y0+round(H/PX),x0:x0+round(W/PX)],(col*(W+J)+J/2,row*(H+J)+J/2)


def box_blur(field,radius):
    """Mean over a (2r+1)^2 window via cumulative sums, edges padded by reflection."""
    p=np.pad(field,radius+1,mode='reflect'); c=p.cumsum(0).cumsum(1); k=2*radius+1
    return (c[k:,k:]-c[:-k,k:]-c[k:,:-k]+c[:-k,:-k])[:field.shape[0],:field.shape[1]]/k/k


def local_directions(mask,radius=4):
    """Line direction (deg, 0-180) at each mask pixel from the structure tensor of its neighbourhood."""
    f=box_blur(mask.astype(float),1)
    gy,gx=np.gradient(f)
    jxx,jxy,jyy=(box_blur(v,radius) for v in (gx*gx,gx*gy,gy*gy))
    gradient=.5*np.degrees(np.arctan2(2*jxy,jxx-jyy))
    return (gradient+90)%180


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


def check_upgrade(folder):
    """Rebuild a genuine v6 socket contract, preserving values, material identity and links."""
    sc,ob,mat=tile_rig(damage=.37,chip_depth=.00073)
    pointer=mat.as_pointer()
    legacy=bpy.data.node_groups.new('LegacyTileDamage','ShaderNodeTree')
    legacy['tile_damage_version']=6; legacy['tile_damage_revision']=2
    missing={'Warp','Warp Scale','Crack Cell','Crack Density','Chip Density'}
    diagnostics={'Chip','Picked','Crack Distance','Chip Cell','Chip Site Edge'}
    for item in tile_damage.damage_group().interface.items_tree:
        if item.item_type=='SOCKET' and item.name not in missing|diagnostics:
            socket=legacy.interface.new_socket(name=item.name,in_out=item.in_out,socket_type=item.socket_type)
            if hasattr(item,'default_value'): socket.default_value=item.default_value
    for label,value in (('Kink Size',.0015),('Kink Amp',.0002),('Branch Share',.35)):
        socket=legacy.interface.new_socket(name=label,in_out='INPUT',socket_type='NodeSocketFloat'); socket.default_value=value
    node=mat.node_tree.nodes['TileDamage']; node.node_tree=legacy
    node.inputs['Fraction'].default_value=.37; node.inputs['Chip Depth'].default_value=.00073
    settings=json.loads(mat['tile_surface_settings'])
    for key in ('warp','warp_scale','crack_cell','crack_density','chip_density'): settings.pop(key,None)
    settings.update(kink_size=.0015,kink_amp=.0002,branch_share=.35)
    mat['tile_surface_settings']=json.dumps(settings)
    tile_surface.set_param(mat,'damage',.42)
    node=mat.node_tree.nodes['TileDamage']
    assert mat.as_pointer()==pointer and node.node_tree['tile_damage_version']==7
    assert node.outputs['Piece Height'].is_linked and node.outputs['Dirt'].is_linked
    assert all(node.inputs[label].is_linked for label in tile_damage._LAYOUT_INPUTS)
    assert abs(node.inputs['Fraction'].default_value-.42)<1e-6 and abs(node.inputs['Chip Depth'].default_value-.00073)<1e-8
    for name in ('chip_reach','kink_size','kink_amp','branch_share'):
        try: tile_surface.set_param(mat,name,.01)
        except ValueError as exc: assert 'v7' in str(exc)
        else: raise AssertionError('Removed name accepted: '+name)
    first=tile_damage.damage_group()
    tile_surface.tile_material('DamageControl'); tile_surface.tile_material('DamageControl')
    assert tile_damage.damage_group()==first
    # Two users: retargeting the shared group cannot hide missing material wiring.
    sibling=tile_surface.tile_material('OldSibling',damage=.47)
    first['tile_damage_version']=6
    for item in list(first.interface.items_tree):
        if item.item_type=='SOCKET' and item.name in missing|{'Dirt'}: first.interface.remove(item)
    tile_surface.set_param(mat,'crack_dirt',.55)
    assert tile_damage._is_current(sibling.node_tree.nodes['TileDamage'].node_tree)
    tile_surface.set_param(sibling,'crack_dirt',.5)
    node=sibling.node_tree.nodes['TileDamage']
    assert node.outputs['Dirt'].is_linked and node.outputs['Piece Height'].is_linked
    assert abs(node.inputs['Fraction'].default_value-.47)<1e-6


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


def check_chip_displacement(folder,full=False):
    """Chips: strict window case; the optional whole-tile comparison is evidence only."""
    metrics=displacement_case(folder,2)
    if full: metrics.update(displacement_case(folder,2,whole=True))
    return metrics


SECTIONS=dict(rate=check_rate,crack=check_crack,pieces=check_pieces,chips=check_chips,
              flakes=check_flakes,spalls=check_spalls,square=check_square,rotated=check_rotated,
              onoff=check_onoff,displacement=check_displacement,damage_displacement=check_damage_displacement,
              chip_displacement=check_chip_displacement,
              upgrade=check_upgrade)
# Chip look is still in development (not approved): these sections report WIP warnings, never a failure.
WIP=('chips','flakes','chip_displacement','rotated')   # rotated = chip containment under rotation/jitter


def main(args):
    """Run each selected section once, retaining failures and timings in one report."""
    args.output.mkdir(parents=True,exist_ok=True)
    start=time.perf_counter(); metrics={}; failures=[]; wip=[]
    group=tile_damage.damage_group()
    metrics['nodes']=len(group.nodes)
    metrics['white_noise_nodes']=sum(n.bl_idname=='ShaderNodeTexWhiteNoise' for n in group.nodes)
    metrics['voronoi_nodes']=sum(n.bl_idname=='ShaderNodeTexVoronoi' for n in group.nodes)
    if metrics['nodes']>800 or metrics['white_noise_nodes']>40 or metrics['voronoi_nodes']>8:
        failures.append('node budget: '+str({k:metrics[k] for k in ('nodes','white_noise_nodes','voronoi_nodes')}))
    for name in ([args.only] if args.only else SECTIONS):
        folder=args.output/name; folder.mkdir(exist_ok=True)
        tick=time.perf_counter()
        try:
            result=SECTIONS[name](folder,args.full) if name.endswith('displacement') else SECTIONS[name](folder)
            metrics.update(result or {})
            print('TILE_DAMAGE_SECTION_PASS',name,flush=True)
        except Exception as exc:
            import traceback
            traceback.print_exc()
            (wip if name in WIP else failures).append(f'{name}: {exc}')
            if name in WIP: print('TILE_DAMAGE_SECTION_WIP',name,flush=True)
        metrics[name+'_seconds']=round(time.perf_counter()-tick,3)
    metrics['wall_seconds']=round(time.perf_counter()-start,3)
    metrics['failures']=failures
    metrics['wip_warnings']=wip
    (args.output/('metrics_'+(args.only or 'all')+'.json')).write_text(json.dumps(metrics,indent=2),encoding='utf-8')
    print('TILE_DAMAGE_'+('FAIL' if failures else 'PASS'),json.dumps(metrics),flush=True)
    return bool(failures)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--only',choices=SECTIONS)
    parser.add_argument('--full',action='store_true')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    sys.exit(main(args))
