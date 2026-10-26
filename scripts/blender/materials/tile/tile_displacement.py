"""Tile geometric displacement: switch a tile material between bump shading and true displacement.

Full displacement moves the whole relief; damage-only displacement moves just the piece steps and
chip/crack cuts, and leaves profile and joints to bump. The chosen mode and its objects are stored
on the material so a structural rebuild applies exactly the same setting again.
"""
import json
import math


def use_displacement(mat, objects, pixel_size=1.0):
    """Opt into world-metre displacement using the shared adaptive subdivision helper."""
    from materials.displacement.displacement import enable_true_displacement
    if not math.isfinite(pixel_size) or pixel_size <= 0:
        raise ValueError('pixel_size must be positive and finite')
    tree = mat.node_tree
    disp = tree.nodes['TileDisplacement']
    out = next(n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output)
    tree.links.new(disp.outputs['Displacement'], out.inputs['Displacement'])
    mat.displacement_method = 'BOTH'
    for name in ('TileBump', 'DamageBump'):
        tree.nodes[name].inputs['Strength'].default_value = 0
    store_displacement(mat, True, objects, pixel_size)
    for obj in objects:
        enable_true_displacement(obj, pixel_size)
    return mat


def store_displacement(mat, mode, objects, pixel_size):
    """Record the displacement mode and its objects so a structural rebuild re-applies exactly that."""
    settings = json.loads(mat['tile_surface_settings'])
    settings.update(displacement=mode, pixel_size=pixel_size,
                    displaced_objects=None if mode is False else [o.name for o in objects])
    mat['tile_surface_settings'] = json.dumps(settings)


def use_damage_displacement(mat, objects, pixel_size=1.0):
    """Displace only damage (piece steps, chip/crack cuts); profile and joints stay bump (edges move only through damage)."""
    from materials.displacement.displacement import enable_true_displacement
    if not math.isfinite(pixel_size) or pixel_size <= 0:
        raise ValueError('pixel_size must be positive and finite')
    tree = mat.node_tree
    out = next(n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output)
    tree.links.new(tree.nodes['DamageDisplacement'].outputs['Displacement'], out.inputs['Displacement'])
    tree.nodes['DamageDisplacementOn'].outputs[0].default_value = 1.
    for name in ('TileBump', 'DamageBump'):
        tree.nodes[name].inputs['Strength'].default_value = 1
    mat.displacement_method = 'BOTH'
    store_displacement(mat, 'damage', objects, pixel_size)
    for obj in objects:
        enable_true_displacement(obj, pixel_size)
    return mat


def use_bump(mat):
    """Restore height bump shading and disconnect geometric displacement."""
    tree = mat.node_tree
    for node in tree.nodes:
        if node.type == 'OUTPUT_MATERIAL':
            for link in list(node.inputs['Displacement'].links):
                tree.links.remove(link)
    if 'DamageDisplacementOn' in tree.nodes:
        tree.nodes['DamageDisplacementOn'].outputs[0].default_value = 0.
    for name in ('TileBump', 'DamageBump'):
        tree.nodes[name].inputs['Strength'].default_value = 1
    mat.displacement_method = 'BUMP'
    store_displacement(mat, False, (), json.loads(mat['tile_surface_settings']).get('pixel_size', 1.0))
    return mat   # adaptive-subdivision modifiers stay on the objects: remove them to drop the dicing cost
