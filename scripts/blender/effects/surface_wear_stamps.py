"""Neighbour-aware, nonperiodic decal placement in metre-space surface coordinates."""
import math
from dataclasses import dataclass, replace
from materials.shared.nodes import sock
from effects.surface_wear_extent import face_z
from effects.surface_wear_atlas import StampAtlas


@dataclass
class StampSource:
    """Non-default decal pools and chip threshold retained independently from hybrid regions."""
    seed: int = 17
    vertical_stamps: StampAtlas | None = None
    wall_stamps: StampAtlas | None = None
    floor_stamps: StampAtlas | None = None
    worn_stamps: StampAtlas | None = None
    worn_extent_bias: float = .3
    worn_threshold: float = .55


def stamps_field(g, kind, layer, vector, extent, frame=None):
    """Select explicit decal deposits or scan-outline chips, never called by a hybrid source."""
    settings = layer.stamps
    if kind == 'dried-marks':
        if settings.vertical_stamps is None or settings.floor_stamps is None:
            raise ValueError('Stamps deposits require vertical_stamps and floor_stamps')
        return deposit_stamps(g, vector, settings, layer.extent, frame)
    if kind != 'worn-through' or settings.worn_stamps is None:
        raise ValueError('Stamps supports deposits or worn-through with worn_stamps')
    foot = replace(layer.extent, foot_height_m=max(layer.extent.foot_full_m, .5*layer.extent.foot_height_m))
    scan = scatter_stamps(g, vector, settings.worn_stamps, settings.seed+109, True, foot, frame)
    bias = g.math('MULTIPLY', extent, settings.worn_extent_bias, (-900, -26000), frame)
    score = g.math('ADD', scan, bias, (-600, -26000), frame)
    return g.range(score, settings.worn_threshold, settings.worn_threshold+.06,
                   (-300, -26000), frame=frame, smooth=True)


def _vector(g, operation, a, b, frame):
    node = g.node('ShaderNodeVectorMath', (-2400, -20000), frame)
    node.operation = operation
    g._in(node.inputs[0], a)
    g._in(node.inputs[1], b)
    return node.outputs[0]


def _random(g, cell, seed, frame):
    noise = g.node('ShaderNodeTexWhiteNoise', (-2200, -20000), frame)
    noise.noise_dimensions = '4D'
    noise.inputs['W'].default_value = seed
    g.link(cell, noise.inputs['Vector'])
    channels = g.node('ShaderNodeSeparateColor', (-2000, -20000), frame)
    g.link(noise.outputs['Color'], channels.inputs[0])
    return channels.outputs


def _size(g, index, sizes, frame):
    dimensions = []
    for axis in (0, 1):
        value = 0
        for i, size in enumerate(sizes):
            pick = g.math('COMPARE', index, i, (-1800, -20000), frame)
            pick.node.inputs[2].default_value = .1
            term = g.math('MULTIPLY', pick, size[axis], (-1600, -20000), frame)
            value = g.math('ADD', value, term, (-1400, -20000), frame)
        dimensions.append(value)
    return g.combine(*dimensions, 1, (-1200, -20000), frame)


def _cell_phase(atlas, vertical, extent):
    return .5-(extent.floor_z_m+.56*extent.foot_height_m)/atlas.cell_m if vertical else 0.


def _stamp(g, vector, cell, atlas, seed, vertical, extent, frame):
    random = _random(g, cell, seed, frame)
    jitter = _random(g, cell, seed + 113, frame)
    index = g.math('MULTIPLY', random[0], len(atlas.sizes_m), (-1800, -20000), frame)
    index = g.math('FLOOR', index, 0, (-1600, -20000), frame)
    scale = g.range(random[1], 0, 1, (-1800, -20300), tmin=atlas.scale_min, tmax=atlas.scale_max, frame=frame)
    size = _size(g,index,atlas.sizes_m,frame)
    size = _vector(g,'MULTIPLY',size,g.combine(scale,scale,1,(-1200,-21300),frame),frame)
    angle = g.range(random[2], 0, 1, (-1800, -20600),
                    tmin=-math.radians(atlas.tilt_deg) if vertical else -math.pi,
                    tmax=math.radians(atlas.tilt_deg) if vertical else math.pi, frame=frame)
    phase = _cell_phase(atlas,vertical,extent)
    centre = _vector(g, 'ADD', cell, (.5, .5-phase, 0), frame)
    centre = _vector(g, 'MULTIPLY', centre, (atlas.cell_m,)*2+(0,), frame)
    dx = g.range(jitter[0], 0, 1, (-1800, -20900), tmin=-atlas.centre_jitter*atlas.cell_m,
                 tmax=atlas.centre_jitter*atlas.cell_m, frame=frame)
    y_jitter = (0 if atlas.anchor=='top' else min(atlas.centre_jitter,.06)) if vertical else atlas.centre_jitter
    dy = g.range(jitter[1], 0, 1, (-1800, -21200), tmin=-y_jitter*atlas.cell_m,
                 tmax=y_jitter*atlas.cell_m, frame=frame)
    centre = _vector(g, 'ADD', centre, g.combine(dx, dy, 0, (-1600,-21200), frame), frame)
    if vertical and atlas.anchor=='top':
        dimensions=g.node('ShaderNodeSeparateXYZ',(-1400,-21400),frame)
        g.link(size,dimensions.inputs[0])
        half=g.math('MULTIPLY',dimensions.outputs['Y'],.5,(-1200,-21400),frame)
        shift=g.math('SUBTRACT',.44*extent.foot_height_m,half,(-1000,-21400),frame)
        centre=_vector(g,'ADD',centre,g.combine(0,shift,0,(-800,-21400),frame),frame)
    local = _vector(g, 'SUBTRACT', vector, centre, frame)
    rotation = g.node('ShaderNodeVectorRotate', (-1400, -21000), frame)
    rotation.rotation_type = 'AXIS_ANGLE'
    rotation.inputs['Axis'].default_value = (0,0,1)
    g.link(angle, rotation.inputs['Angle'])
    g.link(local, rotation.inputs['Vector'])
    uv = _vector(g, 'DIVIDE', rotation.outputs[0], size, frame)
    uv = _vector(g, 'ADD', uv, (.5,.5,0), frame)
    xy = g.node('ShaderNodeSeparateXYZ', (-1000,-21000), frame)
    g.link(uv, xy.inputs[0])
    inside = 1
    for axis in ('X','Y'):
        for operation, limit in (('GREATER_THAN',0),('LESS_THAN',1)):
            test = g.math(operation, xy.outputs[axis], limit, (-800,-21000), frame)
            inside = g.math('MULTIPLY', inside, test, (-600,-21000), frame)
    column = g.math('MODULO', index, atlas.columns, (-1000,-21500), frame)
    row = g.math('DIVIDE', index, atlas.columns, (-1000,-21800), frame)
    row = g.math('FLOOR', row, 0, (-800,-21800), frame)
    row = g.math('SUBTRACT', atlas.rows-1, row, (-600,-21800), frame)
    atlas_uv = _vector(g, 'ADD', uv, g.combine(column,row,0,(-400,-21800),frame), frame)
    atlas_uv = _vector(g, 'MULTIPLY', atlas_uv, (1/atlas.columns,1/atlas.rows,1), frame)
    texture = g.img(atlas.path, 'Non-Color' if atlas.profile!='tone' else 'sRGB',
                    (-200,-21000), frame, atlas_uv, 'surface-wear stamp colour-opacity')
    if atlas.profile!='tone':
        texture.image.alpha_mode='CHANNEL_PACKED'
    texture.extension = 'EXTEND'
    luminance = g.node('ShaderNodeRGBToBW', (100,-21300), frame)
    g.link(texture.outputs['Color'], luminance.inputs[0])
    tone = g.range(luminance.outputs[0], 0, 1, (300,-21300), tmin=1, tmax=.25, frame=frame)
    if atlas.profile=='deposit':
        from effects.surface_wear_deposits import deposit_profile
        channels=g.node('ShaderNodeSeparateColor',(100,-21700),frame)
        g.link(texture.outputs['Color'],channels.inputs[0])
        shape=deposit_profile(g,texture.outputs['Alpha'],channels.outputs[1],channels.outputs[0],frame)
    elif atlas.profile=='opacity':
        shape=texture.outputs['Alpha']
    else:
        shape = g.math('MULTIPLY', texture.outputs['Alpha'], tone, (500,-21000), frame)
    shape = g.math('MULTIPLY', shape, inside, (700,-21000), frame)
    # Density selects occupied cells. The final point extent owns patchy placement;
    # sampling it again at cell centres can reject every stamp in a small surface.
    density = atlas.density
    if vertical:
        z = g.node('ShaderNodeSeparateXYZ', (0,-22000), frame)
        g.link(centre,z.inputs[0])
        foot = g.math('LESS_THAN',z.outputs['Y'],extent.floor_z_m+extent.foot_height_m,(300,-22300),frame)
        above = g.math('GREATER_THAN',z.outputs['Y'],extent.floor_z_m,(100,-22300),frame)
        foot = g.math('MULTIPLY',foot,above,(500,-22300),frame)
        density = g.math('MULTIPLY',density,foot,(500,-22000),frame)
    active = g.math('LESS_THAN', jitter[2], density, (700,-22000), frame)
    return g.math('MULTIPLY',shape,active,(900,-21000),frame)


def scatter_stamps(g, vector, atlas, seed=17, vertical=False, extent=None, frame=None):
    """Sum 3x3 neighbour stamps with seeded choice, rotation, scale, offsets and cell density."""
    from effects.surface_wear_extent import WearExtent
    extent = extent or WearExtent()
    radius = max(math.hypot(*size) for size in atlas.sizes_m)*atlas.scale_max/2
    anchor_shift=(max(abs(.44*extent.foot_height_m-.5*size[1]*scale)
                      for size in atlas.sizes_m for scale in (atlas.scale_min,atlas.scale_max))
                  if vertical and atlas.anchor=='top' else 0)
    if radius+atlas.centre_jitter*atlas.cell_m+anchor_shift > atlas.cell_m:
        raise ValueError('Stamp support exceeds the 3x3 neighbour footprint; increase cell_m')
    import bpy
    from materials.shared.nodes import G
    # One cell sampler graph, reused by all nine neighbours. Keep its parameters local
    # to this scatter call, rather than caching mutable shader state globally.
    group=bpy.data.node_groups.new('surface-wear-stamp-cell','ShaderNodeTree')
    for name in ('Vector','Cell'):
        group.interface.new_socket(name=name,in_out='INPUT',socket_type='NodeSocketVector')
    group.interface.new_socket(name='Value',in_out='OUTPUT',socket_type='NodeSocketFloat')
    cell_graph=G(group)
    inputs=cell_graph.node('NodeGroupInput',(-3000,-20000))
    output=cell_graph.node('NodeGroupOutput',(1500,-21000))
    value=_stamp(cell_graph,inputs.outputs['Vector'],inputs.outputs['Cell'],atlas,seed,vertical,extent,None)
    cell_graph.link(value,output.inputs['Value'])
    scaled = _vector(g,'MULTIPLY',vector,(1/atlas.cell_m,1/atlas.cell_m,1),frame)
    phase = _cell_phase(atlas,vertical,extent)
    scaled = _vector(g,'ADD',scaled,(0,phase,0),frame)
    node = g.node('ShaderNodeVectorMath',(-2600,-20000),frame)
    node.operation = 'FLOOR'
    g.link(scaled,node.inputs[0])
    result = 0
    for y in (-1,0,1):
        for x in (-1,0,1):
            cell = _vector(g,'ADD',node.outputs[0],(x,y,0),frame)
            sample=g.node('ShaderNodeGroup',(-1800+x*400,-20000+y*400),frame)
            sample.node_tree=group
            g.link(vector,sample.inputs['Vector'])
            g.link(cell,sample.inputs['Cell'])
            result = g.math('MAXIMUM',result,sample.outputs['Value'],(1200,-21000),frame)
    return result


def deposit_stamps(g, vector, settings, extent, frame=None):
    """Select down-aligned wall decals or freely rotated floor stains; undersides are gated later."""
    wall_extent=(replace(extent,foot_height_m=max(extent.foot_full_m,.5*extent.foot_height_m))
                 if settings.wall_stamps else extent)
    vertical = scatter_stamps(g,vector,settings.wall_stamps or settings.vertical_stamps,
                              settings.seed,True,wall_extent,frame)
    if extent.drip_top_m is not None:
        drip_extent = replace(extent, floor_z_m=extent.drip_top_m-extent.drip_length_m,
                              foot_height_m=extent.drip_length_m)
        drips = scatter_stamps(g,vector,settings.vertical_stamps,settings.seed+73,True,drip_extent,frame)
        vertical = g.math('MAXIMUM',vertical,drips,(-500,-24500),frame)
    floor = scatter_stamps(g,vector,settings.floor_stamps,settings.seed+37,False,extent,frame)
    up = g.range(face_z(g,frame),.25,.75,(-500,-24000),frame=frame,smooth=True)
    mix = g.node('ShaderNodeMix',(-200,-24000),frame)
    mix.data_type = 'FLOAT'
    g.link(up,mix.inputs[0])
    g.link(vertical,sock(mix.inputs,'A'))
    g.link(floor,sock(mix.inputs,'B'))
    return sock(mix.outputs,'Result')
