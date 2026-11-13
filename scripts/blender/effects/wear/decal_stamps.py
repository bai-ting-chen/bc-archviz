"""Neighbour-aware, nonperiodic decal placement in metre-space surface coordinates."""
from effects.wear.layer_names import canonical_layer
import math
from dataclasses import dataclass, replace
from materials.shared.node_graph import active_socket
from effects.wear.wear_locations import face_z
from effects.wear.decal_atlas import StampAtlas


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


def stamps_field(graph, kind, layer, vector, extent, frame=None):
    """Select explicit decal deposits or scan-outline chips, never called by a hybrid source."""
    kind = canonical_layer(kind)
    settings = layer.stamps
    if kind == 'dried-marks':
        if settings.vertical_stamps is None or settings.floor_stamps is None:
            raise ValueError('Stamps deposits require vertical_stamps and floor_stamps')
        return deposit_stamps(graph, vector, settings, layer.extent, frame)
    if kind != 'chipping' or settings.worn_stamps is None:
        raise ValueError('Stamps supports deposits or chipping with worn_stamps')
    foot = replace(layer.extent, foot_height_m=max(layer.extent.foot_full_m, .5*layer.extent.foot_height_m))
    scan = scatter_stamps(graph, vector, settings.worn_stamps, settings.seed+109, True, foot, frame)
    bias = graph.math('MULTIPLY', extent, settings.worn_extent_bias, (-900, -26000), frame)
    score = graph.math('ADD', scan, bias, (-600, -26000), frame)
    return graph.map_range(score, settings.worn_threshold, settings.worn_threshold+.06,
                   (-300, -26000), frame=frame, smooth=True)


def _random(graph, cell, seed, frame):
    noise = graph.node('ShaderNodeTexWhiteNoise', (-2200, -20000), frame)
    noise.noise_dimensions = '4D'
    noise.inputs['W'].default_value = seed
    graph.link(cell, noise.inputs['Vector'])
    channels = graph.node('ShaderNodeSeparateColor', (-2000, -20000), frame)
    graph.link(noise.outputs['Color'], channels.inputs[0])
    return channels.outputs


def _size(graph, index, sizes, frame):
    dimensions = []
    for axis in (0, 1):
        value = 0
        for i, size in enumerate(sizes):
            pick = graph.math('COMPARE', index, i, (-1800, -20000), frame)
            pick.node.inputs[2].default_value = .1
            term = graph.math('MULTIPLY', pick, size[axis], (-1600, -20000), frame)
            value = graph.math('ADD', value, term, (-1400, -20000), frame)
        dimensions.append(value)
    return graph.combine_xyz(*dimensions, 1, (-1200, -20000), frame)


def _cell_phase(atlas, vertical, extent):
    return .5-(extent.floor_z_m+.56*extent.foot_height_m)/atlas.cell_m if vertical else 0.


def _stamp(graph, vector, cell, atlas, seed, vertical, extent, frame):
    random = _random(graph, cell, seed, frame)
    jitter = _random(graph, cell, seed + 113, frame)
    index = graph.math('MULTIPLY', random[0], len(atlas.sizes_m), (-1800, -20000), frame)
    index = graph.math('FLOOR', index, 0, (-1600, -20000), frame)
    scale = graph.map_range(random[1], 0, 1, (-1800, -20300), target_min=atlas.scale_min, target_max=atlas.scale_max, frame=frame)
    size = _size(graph,index,atlas.sizes_m,frame)
    size = graph.vector_math('MULTIPLY',size,graph.combine_xyz(scale,scale,1,(-1200,-21300),frame), (-2400, -20000),frame)
    angle = graph.map_range(random[2], 0, 1, (-1800, -20600),
                    target_min=-math.radians(atlas.tilt_deg) if vertical else -math.pi,
                    target_max=math.radians(atlas.tilt_deg) if vertical else math.pi, frame=frame)
    phase = _cell_phase(atlas,vertical,extent)
    centre = graph.vector_math('ADD', cell, (.5, .5-phase, 0), (-2400, -20000), frame)
    centre = graph.vector_math('MULTIPLY', centre, (atlas.cell_m,)*2+(0,), (-2400, -20000), frame)
    dx = graph.map_range(jitter[0], 0, 1, (-1800, -20900), target_min=-atlas.centre_jitter*atlas.cell_m,
                 target_max=atlas.centre_jitter*atlas.cell_m, frame=frame)
    y_jitter = (0 if atlas.anchor=='top' else min(atlas.centre_jitter,.06)) if vertical else atlas.centre_jitter
    dy = graph.map_range(jitter[1], 0, 1, (-1800, -21200), target_min=-y_jitter*atlas.cell_m,
                 target_max=y_jitter*atlas.cell_m, frame=frame)
    centre = graph.vector_math('ADD', centre, graph.combine_xyz(dx, dy, 0, (-1600,-21200), frame), (-2400, -20000), frame)
    if vertical and atlas.anchor=='top':
        dimensions=graph.node('ShaderNodeSeparateXYZ',(-1400,-21400),frame)
        graph.link(size,dimensions.inputs[0])
        half=graph.math('MULTIPLY',dimensions.outputs['Y'],.5,(-1200,-21400),frame)
        shift=graph.math('SUBTRACT',.44*extent.foot_height_m,half,(-1000,-21400),frame)
        centre=graph.vector_math('ADD',centre,graph.combine_xyz(0,shift,0,(-800,-21400),frame), (-2400, -20000),frame)
    local = graph.vector_math('SUBTRACT', vector, centre, (-2400, -20000), frame)
    rotation = graph.node('ShaderNodeVectorRotate', (-1400, -21000), frame)
    rotation.rotation_type = 'AXIS_ANGLE'
    rotation.inputs['Axis'].default_value = (0,0,1)
    graph.link(angle, rotation.inputs['Angle'])
    graph.link(local, rotation.inputs['Vector'])
    uv = graph.vector_math('DIVIDE', rotation.outputs[0], size, (-2400, -20000), frame)
    uv = graph.vector_math('ADD', uv, (.5,.5,0), (-2400, -20000), frame)
    xy = graph.node('ShaderNodeSeparateXYZ', (-1000,-21000), frame)
    graph.link(uv, xy.inputs[0])
    inside = 1
    for axis in ('X','Y'):
        for operation, limit in (('GREATER_THAN',0),('LESS_THAN',1)):
            test = graph.math(operation, xy.outputs[axis], limit, (-800,-21000), frame)
            inside = graph.math('MULTIPLY', inside, test, (-600,-21000), frame)
    column = graph.math('MODULO', index, atlas.columns, (-1000,-21500), frame)
    row = graph.math('DIVIDE', index, atlas.columns, (-1000,-21800), frame)
    row = graph.math('FLOOR', row, 0, (-800,-21800), frame)
    row = graph.math('SUBTRACT', atlas.rows-1, row, (-600,-21800), frame)
    atlas_uv = graph.vector_math('ADD', uv, graph.combine_xyz(column,row,0,(-400,-21800),frame), (-2400, -20000), frame)
    atlas_uv = graph.vector_math('MULTIPLY', atlas_uv, (1/atlas.columns,1/atlas.rows,1), (-2400, -20000), frame)
    texture = graph.image_texture(atlas.path, 'Non-Color' if atlas.profile!='tone' else 'sRGB',
                    (-200,-21000), frame, atlas_uv, 'surface-wear stamp colour-opacity')
    if atlas.profile!='tone':
        texture.image.alpha_mode='CHANNEL_PACKED'
    texture.extension = 'EXTEND'
    luminance = graph.node('ShaderNodeRGBToBW', (100,-21300), frame)
    graph.link(texture.outputs['Color'], luminance.inputs[0])
    tone = graph.map_range(luminance.outputs[0], 0, 1, (300,-21300), target_min=1, target_max=.25, frame=frame)
    if atlas.profile=='deposit':
        from effects.wear.water_marks import deposit_profile
        channels=graph.node('ShaderNodeSeparateColor',(100,-21700),frame)
        graph.link(texture.outputs['Color'],channels.inputs[0])
        shape=deposit_profile(graph,texture.outputs['Alpha'],channels.outputs[1],channels.outputs[0],frame)
    elif atlas.profile=='opacity':
        shape=texture.outputs['Alpha']
    else:
        shape = graph.math('MULTIPLY', texture.outputs['Alpha'], tone, (500,-21000), frame)
    shape = graph.math('MULTIPLY', shape, inside, (700,-21000), frame)
    # Density selects occupied cells. The final point extent owns patchy placement;
    # sampling it again at cell centres can reject every stamp in a small surface.
    density = atlas.density
    if vertical:
        z = graph.node('ShaderNodeSeparateXYZ', (0,-22000), frame)
        graph.link(centre,z.inputs[0])
        foot = graph.math('LESS_THAN',z.outputs['Y'],extent.floor_z_m+extent.foot_height_m,(300,-22300),frame)
        above = graph.math('GREATER_THAN',z.outputs['Y'],extent.floor_z_m,(100,-22300),frame)
        foot = graph.math('MULTIPLY',foot,above,(500,-22300),frame)
        density = graph.math('MULTIPLY',density,foot,(500,-22000),frame)
    active = graph.math('LESS_THAN', jitter[2], density, (700,-22000), frame)
    return graph.math('MULTIPLY',shape,active,(900,-21000),frame)


def scatter_stamps(graph, vector, atlas, seed=17, vertical=False, extent=None, frame=None):
    """Sum 3x3 neighbour stamps with seeded choice, rotation, scale, offsets and cell density."""
    from effects.wear.wear_locations import WearExtent
    extent = extent or WearExtent()
    radius = max(math.hypot(*size) for size in atlas.sizes_m)*atlas.scale_max/2
    anchor_shift=(max(abs(.44*extent.foot_height_m-.5*size[1]*scale)
                      for size in atlas.sizes_m for scale in (atlas.scale_min,atlas.scale_max))
                  if vertical and atlas.anchor=='top' else 0)
    if radius+atlas.centre_jitter*atlas.cell_m+anchor_shift > atlas.cell_m:
        raise ValueError('Stamp support exceeds the 3x3 neighbour footprint; increase cell_m')
    import bpy
    from materials.shared.node_graph import NodeGraph
    # One cell sampler graph, reused by all nine neighbours. Keep its parameters local
    # to this scatter call, rather than caching mutable shader state globally.
    group=bpy.data.node_groups.new('surface-wear-stamp-cell','ShaderNodeTree')
    for name in ('Vector','Cell'):
        group.interface.new_socket(name=name,in_out='INPUT',socket_type='NodeSocketVector')
    group.interface.new_socket(name='Value',in_out='OUTPUT',socket_type='NodeSocketFloat')
    cell_graph=NodeGraph(group)
    inputs=cell_graph.node('NodeGroupInput',(-3000,-20000))
    output=cell_graph.node('NodeGroupOutput',(1500,-21000))
    value=_stamp(cell_graph,inputs.outputs['Vector'],inputs.outputs['Cell'],atlas,seed,vertical,extent,None)
    cell_graph.link(value,output.inputs['Value'])
    scaled = graph.vector_math('MULTIPLY',vector,(1/atlas.cell_m,1/atlas.cell_m,1), (-2400, -20000),frame)
    phase = _cell_phase(atlas,vertical,extent)
    scaled = graph.vector_math('ADD',scaled,(0,phase,0), (-2400, -20000),frame)
    node = graph.node('ShaderNodeVectorMath',(-2600,-20000),frame)
    node.operation = 'FLOOR'
    graph.link(scaled,node.inputs[0])
    result = 0
    for y in (-1,0,1):
        for x in (-1,0,1):
            cell = graph.vector_math('ADD',node.outputs[0],(x,y,0), (-2400, -20000),frame)
            sample=graph.node('ShaderNodeGroup',(-1800+x*400,-20000+y*400),frame)
            sample.node_tree=group
            graph.link(vector,sample.inputs['Vector'])
            graph.link(cell,sample.inputs['Cell'])
            result = graph.math('MAXIMUM',result,sample.outputs['Value'],(1200,-21000),frame)
    return result


def deposit_stamps(graph, vector, settings, extent, frame=None):
    """Select down-aligned wall decals or freely rotated floor stains; undersides are gated later."""
    wall_extent=(replace(extent,foot_height_m=max(extent.foot_full_m,.5*extent.foot_height_m))
                 if settings.wall_stamps else extent)
    vertical = scatter_stamps(graph,vector,settings.wall_stamps or settings.vertical_stamps,
                              settings.seed,True,wall_extent,frame)
    if extent.drip_top_m is not None:
        drip_extent = replace(extent, floor_z_m=extent.drip_top_m-extent.drip_length_m,
                              foot_height_m=extent.drip_length_m)
        drips = scatter_stamps(graph,vector,settings.vertical_stamps,settings.seed+73,True,drip_extent,frame)
        vertical = graph.math('MAXIMUM',vertical,drips,(-500,-24500),frame)
    floor = scatter_stamps(graph,vector,settings.floor_stamps,settings.seed+37,False,extent,frame)
    up = graph.map_range(face_z(graph,frame),.25,.75,(-500,-24000),frame=frame,smooth=True)
    mix = graph.node('ShaderNodeMix',(-200,-24000),frame)
    mix.data_type = 'FLOAT'
    graph.link(up,mix.inputs[0])
    graph.link(vertical,active_socket(mix.inputs,'A'))
    graph.link(floor,active_socket(mix.inputs,'B'))
    return active_socket(mix.outputs,'Result')
