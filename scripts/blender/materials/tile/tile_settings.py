"""Tile settings: read a tile material's settings back from its node tree and change one parameter.

A tile material stores its keyword settings as JSON. `read_settings` returns them with live socket
edits applied (so a UI change is kept), and `set_param` changes one keyword and rebuilds the
material when the change is structural.
"""
import inspect
import json
import math

import bpy

from materials.tile import tile_config
from materials.tile import tile_damage
from materials.tile import tile_finish
from materials.tile import tile_maps
from materials.tile.tile_build import tile_material


def read_settings(mat):
    """Read rebuild settings including live UI socket edits and feature switches."""
    saved = json.loads(mat['tile_surface_settings'])
    defaults = {key:p.default for key,p in inspect.signature(tile_material).parameters.items()
                if p.default is not inspect.Parameter.empty}
    unknown = set(saved)-set(defaults)-{'name'}-set(tile_config.REMOVED_DAMAGE)
    if unknown:
        raise ValueError(f'Cannot map legacy tile settings: {", ".join(sorted(unknown))}')
    values = {**defaults,**saved}
    for key in tile_config.REMOVED_DAMAGE:
        values.pop(key, None)
    values['name'] = mat.name
    for key, label in {**tile_config.LAYOUT, **tile_config.FINISH, **tile_damage.PARAMS}.items():
        node = mat.node_tree.nodes['TileDamage' if key in tile_damage.PARAMS else 'TileLayout' if key in tile_config.LAYOUT else 'TileFinish']
        socket = node.inputs.get(label)
        if socket is None:
            continue
        value = socket.default_value
        if key in ('tilt_deg', 'jitter_rotation_deg'):
            value = math.degrees(value)
        elif key in ('body_albedo', 'grout_albedo'):
            value = list(value[:3])
        elif key in ('origin', 'map_size'):
            value = list(value[:2])
        values[key] = value
    values['off'] = [f for f in tile_config.FEATURES if not mat.node_tree.nodes['TileFinish'].inputs[f + ' On'].default_value]
    damage = mat.node_tree.nodes.get('TileDamage')
    piece = damage.outputs.get('Piece Height') if damage else None
    dirt = damage.outputs.get('Dirt') if damage else None
    needs_upgrade = (damage is None or not tile_damage._is_current(damage.node_tree) or
                     piece is None or not piece.is_linked or dirt is None or not dirt.is_linked)
    if needs_upgrade:
        try:
            tile_material(**values)
        except (TypeError,ValueError) as exc:
            raise ValueError(f'Cannot map legacy tile material {mat.name!r}: {exc}') from exc
    return values


def set_param(mat, name, value):
    """Set any tile_material keyword, rebuilding structural options in the same material."""
    if name in tile_config.REMOVED_DAMAGE:
        raise ValueError(f'{name} was removed; v7 parameters: {", ".join(tile_damage.PARAMS)}')
    settings = read_settings(mat)
    if name not in settings:
        raise KeyError(name)
    if name == 'name':
        existing = bpy.data.materials.get(value)
        if existing is not None and existing != mat:
            raise ValueError(f'Material {value!r} already exists')
        mat.name = value
        settings['name'] = mat.name
    elif name in ('displacement', 'pixel_size', 'displaced_objects'):
        if name == 'pixel_size' and (not math.isfinite(value) or value <= 0):
            raise ValueError('pixel_size must be positive and finite')
        settings[name] = value
        return tile_material(**settings)
    elif name in ('face', 'uv'):
        settings[name] = str(value) if name == 'face' and value is not None else value
        return tile_material(**settings)
    elif name == 'off':
        unknown = set(value) - set(tile_config.FEATURES)
        if unknown:
            raise ValueError(f'Unknown tile features: {sorted(unknown)}')
        for feature in tile_config.FEATURES:
            tile_finish.toggle(mat, feature, feature not in value)
        settings['off'] = list(value)
    else:
        node = mat.node_tree.nodes['TileDamage' if name in tile_damage.PARAMS else 'TileLayout' if name in tile_config.LAYOUT else 'TileFinish']
        label = ({**tile_config.LAYOUT, **tile_config.FINISH, **tile_damage.PARAMS})[name]
        if name in tile_damage.PARAMS:
            tile_config.validate_damage(name, value)
        settings[name] = value
        if name in ('tilt_deg', 'jitter_rotation_deg'):
            value = math.radians(value)
        elif name == 'map_size':
            value = tile_maps.resolve_map_size(settings['face'], value)
        elif name in ('origin',) and len(value) == 2:
            value = (*value, 0.)
        elif name.endswith('albedo') and len(value) == 3:
            value = (*value, 1.)
        if name in ('face_contrast', 'face_saturation') and not 0 <= value <= 1:
            raise ValueError(f'{name} must lie in [0, 1]')
        if name in ('tile_w', 'tile_h', 'speck_size') and value <= 0:
            raise ValueError(f'{name} must be positive')
        if name in ('joint', 'corner_radius', 'lippage') and value < 0:
            raise ValueError(f'{name} must be nonnegative')
        socket = node.inputs.get(label)
        if socket is not None:
            socket.default_value = value
        elif name not in tile_config.OPTIONAL_LAYOUT:
            raise KeyError(label)
        if name in ('body_albedo', 'face_contrast', 'face_saturation'):
            image_node = next((n for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE' and n.get('tile_map_role') == 'color'), None)
            if image_node:
                finish_inputs = mat.node_tree.nodes['TileFinish'].inputs
                tile_maps.warn_albedo(image_node.image, finish_inputs['Body Albedo'].default_value[:3],
                                      finish_inputs['Face Contrast'].default_value, finish_inputs['Face Saturation'].default_value)
    mat['tile_surface_settings'] = json.dumps(settings)
    mat.node_tree.update_tag(); mat.update_tag()
    return mat
