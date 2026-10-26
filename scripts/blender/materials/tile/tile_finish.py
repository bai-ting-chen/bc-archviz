"""Tile finish group: the owned node group that exposes every editable finish parameter, plus the
feature switch helpers. A feature's switch removes its whole contribution when it is zero.
"""
import bpy

from materials.tile.tile_config import FEATURES, FINISH
from materials.tile.tile_nodes import _Graph
from materials.tile.tile_nodes import _socket


def finish_group(defaults, owner):
    """Create an owned group exposing all editable finish parameters."""
    tree = bpy.data.node_groups.new(defaults['name'] + '.TileFinish', 'ShaderNodeTree')
    tree['tile_surface_owner'] = owner
    for key, label in FINISH.items():
        kind = ('NodeSocketColor' if key.endswith('albedo') else
                'NodeSocketVector' if key == 'map_size' else 'NodeSocketFloat')
        socket = _socket(tree, label, kind=kind, default=defaults[key])
        if key == 'tilt_deg':
            socket.subtype = 'ANGLE'
        elif key in ('face_contrast', 'face_saturation'):
            socket.min_value, socket.max_value = 0., 1.
    for f in FEATURES:
        _socket(tree, f + ' On', default=1.0)
    # A parameter-only group keeps every dependency flowing outwards to the shader.
    # Images can stay outside groups without feeding any output back into TileFinish.
    inputs = [item for item in tree.interface.items_tree if item.in_out == 'INPUT']
    for item in inputs:
        _socket(tree, item.name, 'OUTPUT', item.socket_type)
    a = _Graph(tree)
    source = a.node('NodeGroupInput')
    target = a.node('NodeGroupOutput')
    target.is_active_output = True
    for item in inputs:
        a.put(source.outputs[item.name], target.inputs[item.name])
    return tree


def gate(a, i, feature, value):
    """Remove a feature's whole contribution when its switch is zero."""
    return a.m('MULTIPLY', i[feature + ' On'], value)


def toggle(mat, feature, on):
    """Enable or remove a finish feature, preserving its parameter values."""
    if feature not in FEATURES:
        raise ValueError(f'Unknown tile feature: {feature}')
    mat.node_tree.nodes['TileFinish'].inputs[feature + ' On'].default_value = float(bool(on))
    mat.node_tree.update_tag(); mat.update_tag()
