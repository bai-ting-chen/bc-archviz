"""Build a tile material: layout, face maps, finish, colour, relief, shading and damage in one node tree.

Each part is built by its own module (tile_albedo, tile_specks, tile_relief, tile_bsdf, tile_damage);
this module only wires them together and stores the settings that a later rebuild reads back.
"""
import json
import math
import uuid

import bpy
import numpy as np

from materials.tile import tile_albedo
from materials.tile import tile_bsdf
from materials.tile import tile_config
from materials.tile import tile_damage
from materials.tile import tile_displacement
from materials.tile import tile_finish
from materials.tile import tile_layout
from materials.tile import tile_mapping
from materials.tile import tile_maps
from materials.tile import tile_relief
from materials.tile import tile_specks
from materials.shared.nodes import G
from materials.tile.tile_nodes import _Graph


def tile_material(name, uv="TileUV", tile_w=0.045, tile_h=0.145, joint=0.003, row_offset=0.0,
                  rotation=0.0, origin=(0.0, 0.0), face=None, map_size=None,
                  body_albedo=(0.65, 0.64, 0.61), coat_ior=1.5, coat_rough=0.25,
                  edge_radius=0.002, recess=0.0015, grout_albedo=(0.36, 0.36, 0.35),
                  grout_rough=0.9, dust=0.5, dust_width=0.004, tint_var=0.03, rough_var=0.05,
                  tilt_deg=0.4, wave_amp=0.0001, specks=0.3, macro=0.05, off=(),
                  corner_radius=0.003, speck_size=0.001, lippage=0.0003,
                  jitter_offset=0.0, jitter_rotation_deg=0.0, face_contrast=1.0, face_saturation=1.0,
                  damage=0.05, crack_share=0.45, chip_share=0.35,
                  step_height=0.00015, piece_tilt=0.0035, crack_width=0.00018, crack_depth=0.0008,
                  chip_size=0.004, chip_depth=0.0008,
                  spall_size=0.001, spall_density=0.25, glaze_thickness=0.0003,
                  engobe_thickness=0.0002, glaze_lip_width=0.0002, engobe_ring=0.0003,
                  force_kind=0, displacement=False, pixel_size=1.0,
                  shell_exponent=0.6, crack_dirt=0.85, dirt_width=0.004,
                  warp=0.004, warp_scale=0.02, crack_cell=0.03, crack_density=0.35, chip_density=0.5,
                  displaced_objects=None):
    """Build tiles in metres; rotation/piece_tilt radians, tilt/jitter_rotation_deg degrees; displacement False|True|'damage'."""
    values = locals().copy()
    if face is not None:
        values['face'] = face = str(face)
    settings = values.copy()
    if not math.isfinite(pixel_size) or pixel_size <= 0:
        raise ValueError('pixel_size must be positive and finite')
    unknown = set(off) - set(tile_config.FEATURES)
    if unknown:
        raise ValueError(f'Unknown features: {sorted(unknown)}')
    values['map_size'] = tile_maps.resolve_map_size(face, map_size)
    values['tilt_deg'] = math.radians(tilt_deg)
    values['jitter_rotation_deg'] = math.radians(jitter_rotation_deg)
    for key in ('body_albedo', 'grout_albedo'):
        values[key] = (*values[key][:3], 1)
    if tile_w <= 0 or tile_h <= 0 or joint < 0 or corner_radius < 0 or speck_size <= 0 or lippage < 0:
        raise ValueError('Tile dimensions must be positive and joint nonnegative')
    if not 0 <= face_contrast <= 1 or not 0 <= face_saturation <= 1:
        raise ValueError('face_contrast and face_saturation must lie in [0, 1]')
    for key in tile_damage.PARAMS:
        tile_config.validate_damage(key, values[key])
    maps = tile_maps.find_maps(face) if face else {}
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    old_group = None
    if mat.node_tree and mat.node_tree.nodes.get('TileFinish'):
        old_group = mat.node_tree.nodes['TileFinish'].node_tree
    owner = mat.get('tile_surface_id') or uuid.uuid4().hex
    mat['tile_surface_id'] = owner
    G(mat)
    if old_group and old_group.get('tile_surface_owner') == owner and old_group.users == 0:
        bpy.data.node_groups.remove(old_group)
    mat['tile_surface_settings'] = json.dumps(settings)

    a = _Graph(mat.node_tree)
    vector = tile_mapping.layout_vector(mat.node_tree, uv, (-600, 300))
    layout = tile_layout.add_layout(mat.node_tree, vector, (-350, 300),
                                    **{k: values[k] for k in tile_config.LAYOUT if k not in tile_config.OPTIONAL_LAYOUT})
    for key in tile_config.OPTIONAL_LAYOUT:
        socket = layout.inputs.get(tile_config.LAYOUT[key])
        if socket is not None:
            socket.default_value = values[key]
    layout.name = 'TileLayout'
    finish = a.node('ShaderNodeGroup'); finish.node_tree = tile_finish.finish_group(values, owner)
    finish.name = 'TileFinish'; finish.location = (350, 300)
    params = {socket.name: socket for socket in finish.outputs}
    params.update({key: layout.outputs[key] for key in ('Tile UV', 'Cell', 'Edge', 'Joint')})
    dimensions = a.split(layout.outputs['Tile Size'])
    params.update({'Tile W': dimensions[0], 'Tile H': dimensions[1],
                   'Joint Width': layout.outputs['Joint Width']})
    # Tile Size is (W,H,0); use a safe Z denominator while preserving map aspect.
    sizes = a.split(finish.outputs['Map Size'])
    map_scale = a.xyz(sizes[0], sizes[1], 1)
    patch = a.v('MULTIPLY', a.rand(layout.outputs['Cell'], (41, 73, 19), True), map_scale)
    coords = a.v('DIVIDE', a.v('ADD', a.v('MULTIPLY', layout.outputs['Tile UV'],
                                         layout.outputs['Tile Size']), patch), map_scale)
    coords.node.name = 'TileMapUV'
    geo = a.node('ShaderNodeNewGeometry')
    params.update({'World': geo.outputs['Position'], 'Face Color': (1, 1, 1),
                   'Face Mean': (1, 1, 1), 'Face Rough': 0., 'Rough Mean': 0.,
                   'Face Height': 0., 'Has Face': 0.})
    if face:
        for key, path in maps.items():
            if path is None:
                continue
            image = bpy.data.images.load(str(path), check_existing=True)
            if key != 'color':
                image.colorspace_settings.name = 'Non-Color'
            elif not image.is_float:
                image.colorspace_settings.name = 'sRGB'
            node = a.node('ShaderNodeTexImage'); node.image = image; node.extension = 'REPEAT'; node['tile_map_role'] = key
            a.put(coords, node.inputs['Vector'])
            if key == 'arm':
                separate = a.node('ShaderNodeSeparateColor', mode='RGB')
                separate.name = 'TileARMChannels'
                a.put(node.outputs['Color'], separate.inputs['Color'])
                params['Face Rough'] = separate.outputs['Green']
            else:
                params[{'color': 'Face Color', 'rough': 'Face Rough', 'height': 'Face Height'}[key]] = node.outputs['Color']
            if key == 'color':
                mean = tile_maps.mean_linear(image, True); mat['face_mean'] = mean
                tile_maps.warn_albedo(image, body_albedo, face_contrast, face_saturation)
                params['Face Mean'] = mean
            elif key in ('rough', 'arm'):
                params['Rough Mean'] = tile_maps.mean_linear(image)[1] if key == 'arm' else float(np.mean(tile_maps.mean_linear(image)))
        params['Has Face'] = 1.
    else:
        mat['face_mean'] = (1., 1., 1.)
    dust_mask = tile_albedo.dust(a, params)
    pits, pinholes = tile_specks.specks(a, params)
    color, grout_color, macro_delta = tile_albedo.albedo(a, params, dust_mask, pits, pinholes)
    height, joint_mix, face_height = tile_relief.height(a, params, pits, pinholes)
    damage_node = a.node('ShaderNodeGroup'); damage_node.node_tree = tile_damage.damage_group()
    damage_node.name = 'TileDamage'; damage_node.location = (0, -500)
    for label in ('Tile ID', 'Cell', 'Tile UV', 'Edge', 'Tile Size'):
        a.put(layout.outputs[label], damage_node.inputs[label])
    for key, label in tile_damage.PARAMS.items():
        damage_node.inputs[label].default_value = values[key]
    a.put(finish.outputs['damage On'], damage_node.inputs['On'])
    d = damage_node.outputs
    piece_height = a.m('MULTIPLY', d['Piece Height'], a.m('GREATER_THAN', params['Edge'], 0))
    undamaged = height
    height = a.m('ADD', height, piece_height)
    face_height = a.m('ADD', face_height, piece_height)
    missing = a.m('ADD', d['Chip Depth Out'], d['Crack Depth Out'])
    cut = a.m('MINIMUM', height, a.m('SUBTRACT', face_height, missing))
    cut = a.m('MAXIMUM', cut, a.m('MULTIPLY', params['Recess'], -1))
    height = a.mix(a.m('GREATER_THAN', missing, 0), height, cut)
    marker = a.node('ShaderNodeMath', operation='ADD'); marker.name = 'TileTotalHeight'
    a.put(height, marker.inputs[0]); marker.inputs[1].default_value = 0
    height = marker.outputs[0]
    # Damage-only relief (piece steps + chip/crack cuts): what use_damage_displacement turns into geometry.
    # Bump then shades the rest (profile, joints, waviness), so the displaced part is not counted twice.
    damage_height = a.node('ShaderNodeMath', operation='SUBTRACT'); damage_height.name = 'TileDamageHeight'
    a.put(height, damage_height.inputs[0]); a.put(undamaged, damage_height.inputs[1])
    displaced_share = a.node('ShaderNodeValue'); displaced_share.name = 'DamageDisplacementOn'
    displaced_share.outputs[0].default_value = 0.
    bump_height = a.m('SUBTRACT', height, a.m('MULTIPLY', damage_height.outputs[0], displaced_share.outputs[0]))
    shader = tile_bsdf.bsdfs(a, params, color, grout_color, dust_mask, macro_delta, bump_height, joint_mix)
    shader = tile_damage.damage_bsdfs(a, params, shader, color, bump_height, d)
    out = a.node('ShaderNodeOutputMaterial'); out.location = (900, 300)
    a.put(shader, out.inputs['Surface'])
    disp = a.node('ShaderNodeDisplacement'); disp.label = 'Metres; optional displacement'; disp.space = 'WORLD'
    disp.inputs['Midlevel'].default_value = 0; disp.inputs['Scale'].default_value = 1
    a.put(height, disp.inputs['Height'])
    disp.name = 'TileDisplacement'
    ddisp = a.node('ShaderNodeDisplacement'); ddisp.label = 'Metres; damage-only displacement'; ddisp.space = 'WORLD'
    ddisp.inputs['Midlevel'].default_value = 0; ddisp.inputs['Scale'].default_value = 1
    a.put(damage_height.outputs[0], ddisp.inputs['Height'])
    ddisp.name = 'DamageDisplacement'
    mat.displacement_method = 'BUMP'
    for feature in off:
        tile_finish.toggle(mat, feature, False)
    if displacement:
        # Re-apply only to the objects it was set on (a macro may displace one wall); legacy: every user.
        if displaced_objects is not None:
            objects = [bpy.data.objects[n] for n in displaced_objects if n in bpy.data.objects]
        else:
            objects = [o for o in bpy.data.objects if o.type == 'MESH' and
                       any(slot.material == mat for slot in o.material_slots)]
        (tile_displacement.use_damage_displacement if displacement == 'damage'
         else tile_displacement.use_displacement)(mat, objects, pixel_size)
    return mat
