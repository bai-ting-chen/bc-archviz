"""Probe: upgrading a material built with an older damage group (v6) keeps its values, identity and links."""

import os as _os
import sys as _sys
_CONTROLS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in [_CONTROLS] + [_os.path.join(_CONTROLS, _t) for _t in ('archviz', 'tile', 'material', 'effects', 'water', 'lighting', 'environment', 'regression')]:
    if _d not in _sys.path:
        _sys.path.append(_d)
import json

import bpy

import materials.tile.tile_damage as tile_damage
import materials.tile.tile_surface as tile_surface
from tile_damage_rig import tile_rig


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
