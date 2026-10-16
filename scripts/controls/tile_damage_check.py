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
import tile_damage
import tile_surface

W, H, J, PX, NT = .025, .25, .003, .00025, 3
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
        signed = name in ('Piece Height', 'World Z', 'Normal X', 'Normal Y', 'Normal Z', 'Total Height')
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


def check_crack(folder):
    """Compare identical cells with and without C2, including its actual crack band."""
    sc, ob, mat = tile_rig(force_kind=1, branch_share=0, spall_density=0, crack_width=.0005)
    first = probe_rgb(mat, folder, 'c1', ('Crack','Piece','Dirt'))
    tile_surface.set_param(mat, 'branch_share', 1)
    second = probe_rgb(mat, folder, 'c2', ('Crack','Piece','Dirt'))
    c1, c2 = first[...,0]>.5, second[...,0]>.5
    for index, face, x0, X, Y in tiles(c1.shape):
        line = c1 & face
        assert line.any() and X[line].min()<x0+2*PX and X[line].max()>x0+W-2*PX, f'{index}: C1 endpoints'
        assert len(components(line)) == 1, f'{index}: C1 is disconnected'
        original_ids = np.rint(first[...,1]*4).astype(int)
        ids = np.rint(second[...,1]*4).astype(int)
        extra = c2 & ~c1 & face
        assert extra.any(), f'{index}: no additional C2 crack pixels'
        assert len(components(extra)) == 1, f'{index}: C2 is not one band'
        assert (dilate(extra)&line).any(), f'{index}: C2 misses C1'
        side_ids = original_ids[extra & ~dilate(line)]
        assert len(np.unique(side_ids)) == 1, f'{index}: C2 crosses C1'
        small = face & (ids>=2) & ~c2
        assert small.any(), f'{index}: missing small piece'
        left = X[small].min()<x0+2*PX; right = X[small].max()>x0+W-2*PX
        assert left != right, f'{index}: small piece long-edge contact'
        edge = (X<x0+2*PX) if left else (X>x0+W-2*PX)
        assert (extra & edge).any(), f'{index}: arc misses the same long edge'
        inner = boundary(small) & (X>x0+2*PX)&(X<x0+W-2*PX)&~dilate(line,2)
        assert inner.any() and np.mean(dilate(c2,2)[inner])>=.8, f'{index}: arc misses inner piece boundary'
        assert len(np.unique(ids[face&~dilate(c2)])) == 3, f'{index}: piece count'
    for data in (first,second):
        crack=data[...,0]>.5; dirt=data[...,2]
        assert not ((dirt>1e-6)&~disk_dilate(crack,round(.002/PX)+1)).any(), 'Dirt beyond Dirt Width + 1 px'
        assert (dirt[crack]<.1).any() and (dirt[crack]>.5).any(), 'Dirt must include clean and dark patches'
    tile_surface.set_param(mat,'crack_dirt',0)
    assert np.max(probe_rgb(mat,folder,'dirt_zero',('Dirt',None,None)))<1e-8


def check_pieces(folder):
    """Fit each rigid piece plane and enforce its reference, lift and tilt bounds."""
    sc, ob, mat = tile_rig(force_kind=1, branch_share=1, spall_density=0, crack_width=.0005)
    data = probe_rgb(mat, folder, 'piece_planes', ('Piece Height','Piece','Crack'), (.002,1,1))
    ph, ids, near = data[...,0], np.rint(data[...,1]*4).astype(int), dilate(data[...,2]>.5,3)
    moved = 0.
    for index, face, x0, X, Y in tiles(ph.shape):
        for value in np.unique(ids[face&~near]):
            mask = face & ~near & (ids==value)
            if mask.sum()<10: continue
            A = np.c_[X[mask],Y[mask],np.ones(mask.sum())]
            coef = np.linalg.lstsq(A,ph[mask],rcond=None)[0]
            assert np.max(np.abs(A@coef-ph[mask]))<1e-7, f'{index}/{value}: not planar'
            if value==0: assert np.max(np.abs(ph[mask]))<1e-9, 'reference piece moved'
            moved = max(moved,float(np.max(np.abs(ph[mask]))))
            assert np.max(np.abs(ph[mask]))<=.00006+math.tan(.0035)*.13+1e-7
    assert moved>.3*.00006
    face = np.logical_or.reduce([m for _,m,*_ in tiles(ph.shape)])
    assert np.max(np.abs(ph[~face]))<1e-9, 'height in grout'
    return {'piece_max_lift_m': moved}


def chip_data(folder, depth=.0008, label='chips'):
    """Read chip depths and both coating masks in one topology probe."""
    sc, ob, mat = tile_rig(force_kind=2, chip_size=.004, chip_depth=depth)
    return mat, probe_rgb(mat, folder, label, ('Chip Depth Out','Glaze Lip','Body'), (.001,1,1))


def check_chips(folder):
    """Verify shell location, positive lip coverage, layer order and a 10-micron edge scan."""
    mat, data = chip_data(folder)
    depth, lip = data[...,0], data[...,1]>.5
    selected = None
    for index, face, x0, X, Y in tiles(depth.shape):
        shell = face & (depth>1e-6)
        assert shell.any(), f'{index}: no chip'
        cx = x0 if X[shell].mean()<x0+W/2 else x0+W
        cy = J/2 if Y[shell].mean()<J/2+H/2 else J/2+H
        edge = np.minimum(np.abs(X-cx),np.abs(Y-cy))
        assert np.hypot(X[shell]-cx,Y[shell]-cy).max()<.004*1.15+.0005
        deepest=np.unravel_index(np.argmax(np.where(shell,depth,-1)),depth.shape)
        assert edge[deepest]<=.0005, f'{index}: deepest band is away from arris'
        assert not (shell&(data[...,2]>.5)&(depth<GLAZE+ENGOBE-1e-8)).any(), 'Body above its depth threshold'
        outline = boundary(shell)&(edge>2*PX)
        assert outline.any() and np.mean(dilate(lip)[outline])>=.6, f'{index}: missing lip coverage'
        assert not (lip & shell & ~dilate(boundary(shell),2)).any(), f'{index}: lip inside bowl'
        if selected is None: selected = (cx,cy,x0)
    cx,cy,x0 = selected
    origin = (cx if cx==x0 else cx-.008, cy if cy==J/2 else cy-.008)
    sc,ob,mat = setup(.008,.008,160,160,origin=origin,force_kind=2,chip_depth=.0008)
    layers = probe_rgb(mat,folder,'chip_layers',('Glaze Lip','Engobe','Body'))>.5
    codes = layers[...,0].astype(int)+2*layers[...,1]+3*layers[...,2]
    if cx!=x0: codes = codes[:,::-1]
    if cy!=J/2: codes = codes[::-1]
    scans = 0
    for row in codes[10:50]:
        seq = row[::-1]; seq = seq[np.r_[True,seq[1:]!=seq[:-1]]]
        if np.any(seq):
            assert seq[0]==0 and seq[1]==1, f'Glaze -> Lip skipped: {seq}'
            assert not np.any(seq[2:]==1), f'Lip follows deeper strata: {seq}'
            if 3 in seq: assert 2 in seq and np.flatnonzero(seq==2)[0]<np.flatnonzero(seq==3)[0], f'Engobe skipped: {seq}'
            scans += 1
    assert scans>0
    rim = boundary(np.any(layers,axis=-1))
    yy,xx = np.nonzero(rim & (np.indices(rim.shape)[0]>10)&(np.indices(rim.shape)[1]>10))
    assert len(xx)>0
    k=len(xx)//2
    centre=(origin[0]+(xx[k]+.5)*.00005,origin[1]+(yy[k]+.5)*.00005)
    sc,ob,mat = setup(.002,.002,200,200,origin=(centre[0]-.001,centre[1]-.001),force_kind=2)
    fine=probe_rgb(mat,folder,'chip_edge_10um',('Chip Depth Out',None,None),(.001,1,1))[...,0]
    widths=[]
    for line in list(fine)+list(fine.T):
        for values in (line,line[::-1]):
            hits=np.flatnonzero((values[:-1]<.1*GLAZE)&(values[1:]>=.1*GLAZE))
            for start in hits:
                stop=np.flatnonzero(values[start+1:]>=.9*GLAZE)
                if len(stop): widths.append((stop[0]+1)*.00001)
    assert widths and max(widths)<=.00003+1e-12, f'edge transition: {widths}'
    mat, shallow=chip_data(folder,.0004,'shallow_chips')
    shell=shallow[...,0]>1e-6
    assert np.mean(shallow[...,2][shell]>.5)<.05, 'shallow shell exposes body'
    tile_surface.set_param(mat,'chip_depth',0)
    zero=probe_rgb(mat,folder,'zero_depth_chip',('Body','Chip Depth Out',None),(1,.001,1))
    assert np.max(zero[...,0])<1e-6 and np.max(zero[...,1])<=GLAZE+1e-8
    return {'edge_transition_max_m': max(widths),**check_chip_look(folder)}


def chip_cells(data,width=.0375):
    """Locate each of three corner chips and return its folded metre coordinates."""
    Y,X=np.meshgrid((np.arange(data.shape[0])+.5)*PX,(np.arange(data.shape[1])+.5)*PX,indexing='ij')
    for index in range(NT):
        x0=index*(width+J)+J/2
        face=(X>x0)&(X<x0+width)&(Y>J/2)&(Y<J/2+H)
        shell=face&(data[...,0]>1e-6)
        assert shell.any(), f'{index}: empty chip'
        cx=x0 if X[shell].mean()<x0+width/2 else x0+width
        cy=J/2 if Y[shell].mean()<J/2+H/2 else J/2+H
        yield index,face,shell,np.abs(X-cx),np.abs(Y-cy),(cx,cy,x0)


def scallop_measure(x,y,outline,size):
    """Measure line deviation or two curvature sign changes after smoothing kink scale."""
    points=np.c_[x[outline],y[outline]]
    assert len(points)>=8, 'Too few outline samples'
    centre=points.mean(axis=0)
    _,_,axes=np.linalg.svd(points-centre,full_matrices=False)
    deviation=float(np.max(np.abs((points-centre)@axes[1])))
    points=points[np.argsort(np.arctan2(points[:,1],points[:,0]))]
    # A 1.75 mm average suppresses the 1.5 mm kink knots, retaining the scar arcs.
    smooth=np.stack([np.convolve(np.pad(points[:,k],3,mode='edge'),np.ones(7)/7,mode='valid') for k in (0,1)],axis=1)
    left=smooth[3:-3]-smooth[:-6]; right=smooth[6:]-smooth[3:-3]
    cross=left[:,0]*right[:,1]-left[:,1]*right[:,0]
    signs=np.sign(cross[np.abs(cross)>(.1*PX)**2])
    changes=int(np.count_nonzero(signs[1:]!=signs[:-1]))
    assert deviation>=.15*size or changes>=2, f'No scalloped arcs: deviation {deviation:.6g} m, changes {changes}'
    return deviation,changes


def check_chip_look(folder):
    """Measure slip width, clay coverage, scallops and the room-distance size clamp."""
    width=.0375
    def rig(size,label):
        """Pack the full three-chip look rig at the topology pixel scale."""
        sc,ob,mat=setup(NT*(width+J),H+J,round(NT*(width+J)/PX),round((H+J)/PX),
                        tile_w=width,force_kind=2,chip_size=size,chip_depth=.0015)
        return probe_rgb(mat,folder,label,('Chip Depth Out','Body','Engobe'),(.002,1,1))
    data=rig(.01,'scalloped_10mm')
    coverage=[]; deviations=[]; changes=[]; selected=None
    for index,face,shell,x,y,corner in chip_cells(data):
        fraction=float(np.mean(data[...,1][shell]>.5))
        assert fraction>=.4, f'{index}: Body covers only {fraction:.3f} of shell'
        coverage.append(fraction)
        outline=boundary(shell)&(np.minimum(x,y)>2*PX)
        deviation,count=scallop_measure(x,y,outline,.01)
        deviations.append(deviation); changes.append(count)
        if selected is None: selected=corner
    cx,cy,x0=selected
    origin=(cx if cx==x0 else cx-.008,cy if cy==J/2 else cy-.008)
    sc,ob,mat=setup(.008,.008,160,160,origin=origin,tile_w=width,force_kind=2,chip_size=.01,chip_depth=.0015)
    layers=probe_rgb(mat,folder,'slip_width_50um',('Glaze Lip','Engobe','Body'))>.5
    outer=layers[...,1]&dilate(layers[...,0])
    outer[:3]=outer[-3:]=False; outer[:,:3]=outer[:,-3:]=False
    outer_points=np.argwhere(outer); body_points=np.argwhere(layers[...,2])
    assert len(outer_points) and len(body_points), 'Missing slip/body band'
    widths=[]
    for points in np.array_split(outer_points,max(1,math.ceil(len(outer_points)/128))):
        distances=np.sqrt(np.min(np.sum((points[:,None,:]-body_points[None,:,:])**2,axis=-1),axis=1))
        widths.extend((distances+1)*.00005)
    median=float(np.median(widths))
    assert median<=.0006, f'Slip band median {median:.6g} m > 0.6 mm'
    large=rig(.03,'room_distance_30mm')
    reaches=[]; faces=[]
    for index,face,shell,x,y,_ in chip_cells(large):
        reach=float(np.hypot(x[shell],y[shell]).max())
        assert reach<=.03*1.15+.0005, f'{index}: chip exceeds corner clamp ({reach} m)'
        reaches.append(reach); faces.append(face)
    assert max(reaches)>=.02, f'30 mm chips only reach {max(reaches):.6g} m'
    assert not ((large[...,0]>1e-6)&~np.logical_or.reduce(faces)).any(), 'Large chip leaves tile faces'
    return dict(slip_median_width_m=median,body_shell_fraction_min=min(coverage),
                scallop_deviation_m=deviations,scallop_curvature_changes=changes,large_chip_reaches_m=reaches)


def check_flakes(folder):
    """Coating flakes stay at an edge and within the coating stack."""
    sc,ob,mat=tile_rig(force_kind=3)
    data=probe_rgb(mat,folder,'flakes',('Chip Depth Out','Glaze Lip','Engobe'),(.001,1,1))
    for index,face,x0,X,Y in tiles(data.shape[:2]):
        shell=face&(data[...,0]>1e-6)
        assert shell.any(), f'{index}: no flake'
        edge=np.minimum.reduce([X-x0,x0+W-X,Y-J/2,J/2+H-Y])
        assert edge[shell].max()<.001*1.5*1.1+.0004
        assert data[...,0][shell].max()<=GLAZE+ENGOBE+1e-8


def check_spalls(folder):
    """Spall coating shells hug the actual crack and cannot exceed the stack."""
    sc,ob,mat=tile_rig(force_kind=1,branch_share=0,spall_density=1,crack_width=.0005)
    data=probe_rgb(mat,folder,'spalls',('Crack','Chip Depth Out','Engobe'),(1,.001,1))
    crack=data[...,0]>.5; shell=data[...,1]>1e-6
    assert shell.any()
    assert not (shell&~dilate(crack,7)).any(), 'spall away from crack'
    assert data[...,1][shell&~crack].max()<=GLAZE+ENGOBE+1e-8


def check_square(folder):
    """Twenty square cells touch both long edges; mosaics retain the 0.8-side clamp."""
    pitch=.102
    sc,ob,mat=setup(4*pitch,5*pitch,round(4*pitch/PX),round(5*pitch/PX),tile_w=.1,tile_h=.1,
                    joint=.002,force_kind=1,branch_share=0,spall_density=0,crack_width=.001)
    crack=probe_rgb(mat,folder,'square_20',('Crack',None,None))[...,0]>.5
    Y,X=np.meshgrid((np.arange(crack.shape[0])+.5)*PX,(np.arange(crack.shape[1])+.5)*PX,indexing='ij')
    for row in range(5):
        for col in range(4):
            x0,y0=col*pitch+.001,row*pitch+.001
            face=(X>x0)&(X<x0+.1)&(Y>y0)&(Y<y0+.1)
            line=face&crack
            assert line.any() and X[line].min()<x0+2*PX and X[line].max()>x0+.1-2*PX, f'square {col},{row}: C1 endpoints'
    sc,ob,mat=setup(.033,.033,132,132,tile_w=.01,tile_h=.01,joint=.001,force_kind=2,chip_size=.008)
    data=probe_rgb(mat,folder,'mosaic',('Chip Depth Out','UV X','UV Y'),(.001,1,1))
    lx,ly=data[...,1]*.01,data[...,2]*.01
    r=np.hypot(np.minimum(lx,.01-lx),np.minimum(ly,.01-ly))
    assert r[data[...,0]>1e-6].max()<.8*.01*1.15+.0005


def check_rotated(folder):
    """Per-tile chip coordinates survive rotation, jitter and swapped tile axes."""
    sc,ob,mat=setup(.3,.3,1200,1200,tile_w=.25,tile_h=.0375,rotation=.43,
                    jitter_rotation_deg=.6,jitter_offset=.0003,force_kind=2)
    data=probe_rgb(mat,folder,'rotated',('Chip Depth Out','UV X','UV Y'),(.001,1,1))
    lx,ly=data[...,1]*.25,data[...,2]*.0375
    r=np.hypot(np.minimum(lx,.25-lx),np.minimum(ly,.0375-ly))
    assert data[...,0].max()>.0005
    assert r[data[...,0]>1e-6].max()<.004*1.15+.0005


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
    sc,ob,mat=setup(.3,.3,400,400,tile_w=.0375,tile_h=.25,joint=0,damage=.5,force_kind=2)
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
    """Create a legacy interface/settings contract, then call the public setter."""
    sc,ob,mat=tile_rig(damage=.37,chip_depth=.00073)
    group=tile_damage.damage_group()
    legacy=bpy.data.node_groups.new('LegacyTileDamage','ShaderNodeTree')
    legacy['tile_damage_version']=5
    missing={'Branch Share','Step Height','Piece Tilt','Kink Size','Kink Amp','Chip Size','Spall Density','Force Kind',
             'Shell Exponent','Crack Dirt','Dirt Width'}
    for item in group.interface.items_tree:
        if item.item_type=='SOCKET' and item.name not in missing|{'Piece Height','Piece','Dirt'}:
            sock=legacy.interface.new_socket(name=item.name,in_out=item.in_out,socket_type=item.socket_type)
            if hasattr(item,'default_value'): sock.default_value=item.default_value
    node=mat.node_tree.nodes['TileDamage']; node.node_tree=legacy
    node.inputs['Fraction'].default_value=.37; node.inputs['Chip Depth'].default_value=.00073
    settings=json.loads(mat['tile_surface_settings'])
    for key,label in tile_damage.PARAMS.items():
        if label in missing: settings.pop(key,None)
    settings['chip_reach']=.01
    mat['tile_surface_settings']=json.dumps(settings)
    assert node.outputs.get('Piece Height') is None
    tile_surface.set_param(mat,'damage',.42)
    node=mat.node_tree.nodes['TileDamage']
    assert node.node_tree['tile_damage_version']==6 and node.outputs['Piece Height'].is_linked
    assert abs(node.inputs['Fraction'].default_value-.42)<1e-6
    assert abs(node.inputs['Chip Depth'].default_value-.00073)<1e-8
    for link in list(node.outputs['Piece Height'].links): mat.node_tree.links.remove(link)
    tile_surface.set_param(mat,'uv','TileUV')
    assert mat.node_tree.nodes['TileDamage'].outputs['Piece Height'].is_linked
    try: tile_surface.set_param(mat,'chip_reach',.01)
    except ValueError as exc: assert 'chip_size' in str(exc)
    else: raise AssertionError('obsolete name accepted')
    first=tile_damage.damage_group()
    tile_surface.tile_material('DamageControl'); tile_surface.tile_material('DamageControl')
    assert tile_damage.damage_group()==first
    check_shared_upgrade()


def check_shared_upgrade():
    """A sibling remapped to the new group still needs its material shader rebuilt."""
    first=tile_surface.tile_material('OldFirst',damage=.31)
    second=tile_surface.tile_material('OldSibling',damage=.47)
    old=first.node_tree.nodes['TileDamage'].node_tree
    old['tile_damage_revision']=1
    for item in list(old.interface.items_tree):
        if item.item_type=='SOCKET' and item.name in {'Shell Exponent','Crack Dirt','Dirt Width','Dirt'}:
            old.interface.remove(item)
    tile_surface.set_param(first,'crack_dirt',.55)
    remapped=second.node_tree.nodes['TileDamage']
    assert tile_damage._is_current(remapped.node_tree)
    assert not remapped.outputs['Dirt'].is_linked, 'Fixture did not reproduce missing sibling wiring'
    tile_surface.set_param(second,'crack_dirt',.5)
    node=second.node_tree.nodes['TileDamage']
    assert node.outputs['Dirt'].is_linked and node.outputs['Piece Height'].is_linked
    assert abs(node.inputs['Fraction'].default_value-.47)<1e-6
    assert abs(node.inputs['Crack Dirt'].default_value-.5)<1e-6


def displacement_case(folder,kind,whole=False):
    """Compare positions and world normals in an 8 mm, <=20 um-edge diced window."""
    kw=dict(force_kind=kind,chip_depth=.0008,branch_share=1,spall_density=0,joint=0,recess=.006)
    sc,ob,mat=setup(W,H,round(W/PX),round(H/PX),**kw)
    data=probe_rgb(mat,folder,f'locate_{kind}',('Chip Depth Out','Crack','Piece Height'),(.001,1,.002))
    if kind==2:
        yy,xx=np.unravel_index(np.argmax(data[...,0]),data[...,0].shape)
        centre=((xx+.5)*PX,(yy+.5)*PX)
    else:
        yy=np.flatnonzero(data[:,data.shape[1]//2,1]>.5)
        assert len(yy), 'no crack at window centre'
        centre=(W/2,(yy[len(yy)//2]+.5)*PX)
    origin=(min(max(centre[0]-.004,0),W-.008),min(max(centre[1]-.004,0),H-.008))
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
    mask=(after[...,1]>.0006) if kind==2 else ~dilate(before[...,2]>.5,3)
    mask[:3]=mask[-3:]=False; mask[:,:3]=mask[:,-3:]=False
    assert mask.any(), prefix+': no interior samples'
    error=np.abs(after[...,0][mask]-before[...,0][mask])
    metrics={prefix+'_position_mean_m':float(error.mean()),prefix+'_position_max_m':float(error.max()),
             prefix+'_interior_pixels':int(mask.sum()),prefix+'_dicing_edge_m':max(width/nx,height/ny)*(.125 if whole else .5)}
    if not whole: assert error.mean()<5e-6 and error.max()<1e-4, metrics
    if kind==1:
        yy,xx=np.meshgrid(origin[1]+(np.arange(ny)+.5)*height/ny,origin[0]+(np.arange(nx)+.5)*width/nx,indexing='ij')
        ids=np.rint(after[...,2]*4).astype(int); errors=[]
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
    """Keep strict window cases; optional whole-tile comparisons are evidence only."""
    metrics={}
    for kind in (2,1): metrics.update(displacement_case(folder,kind))
    if full:
        for kind in (2,1): metrics.update(displacement_case(folder,kind,whole=True))
    return metrics


SECTIONS=dict(rate=check_rate,crack=check_crack,pieces=check_pieces,chips=check_chips,
              flakes=check_flakes,spalls=check_spalls,square=check_square,rotated=check_rotated,
              onoff=check_onoff,displacement=check_displacement,upgrade=check_upgrade)


def main(args):
    """Run each selected section once, retaining failures and timings in one report."""
    args.output.mkdir(parents=True,exist_ok=True)
    start=time.perf_counter(); metrics={}; failures=[]
    group=tile_damage.damage_group()
    metrics['nodes']=len(group.nodes)
    metrics['white_noise_nodes']=sum(n.bl_idname=='ShaderNodeTexWhiteNoise' for n in group.nodes)
    if metrics['nodes']>=700 or metrics['white_noise_nodes']>40:
        failures.append('node budget: '+str({k:metrics[k] for k in ('nodes','white_noise_nodes')}))
    for name in ([args.only] if args.only else SECTIONS):
        folder=args.output/name; folder.mkdir(exist_ok=True)
        tick=time.perf_counter()
        try:
            result=SECTIONS[name](folder,args.full) if name=='displacement' else SECTIONS[name](folder)
            metrics.update(result or {})
            print('TILE_DAMAGE_SECTION_PASS',name,flush=True)
        except Exception as exc:
            import traceback
            traceback.print_exc(); failures.append(f'{name}: {exc}')
        metrics[name+'_seconds']=round(time.perf_counter()-tick,3)
    metrics['wall_seconds']=round(time.perf_counter()-start,3)
    metrics['failures']=failures
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
