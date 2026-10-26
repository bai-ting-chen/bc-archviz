"""Damage build; canonical implementation behind tile_damage."""

import bpy

from materials.tile.tile_graph import _socket

from materials.tile.group_retarget import _replace_group_users

from materials.tile.damage_contract import DEFAULTS, PARAMS, _LAYOUT_INPUTS, _OUTPUTS, _REVISION, _VERSION

from materials.tile.damage_fields import _fine_fields, _piece_fields, _rand, _voronoi, _warp

from materials.tile.damage_graph import _DamageGraph

from materials.tile.damage_layers import _layers

def _is_current(tree):
    """Require the full v7 contract, not only the version stamp."""
    if tree is None or tree.get('tile_damage_version')!=_VERSION or tree.get('tile_damage_revision')!=_REVISION:
        return False
    sockets={(s.in_out,s.name) for s in tree.interface.items_tree if s.item_type=='SOCKET'}
    return (all(('INPUT',label) in sockets for label in (*_LAYOUT_INPUTS,*PARAMS.values(),'On')) and
            all(('OUTPUT',label) in sockets for label in _OUTPUTS))

def damage_group(name='TileDamage'):
    """Build four shared Voronoi evaluations, preserving matching links on v6 upgrade."""
    old=bpy.data.node_groups.get(name)
    if old is not None:
        if old.bl_idname!='ShaderNodeTree' or 'tile_damage_version' not in old:
            raise ValueError(f'Refusing to replace unrelated group {name!r}')
        if _is_current(old): return old
    tree=bpy.data.node_groups.new(name,'ShaderNodeTree')
    for label in _LAYOUT_INPUTS:
        _socket(tree,label,kind='NodeSocketVector' if label in ('Cell','Tile UV','Tile Size') else 'NodeSocketFloat')
    for (key,label),default in zip(PARAMS.items(),DEFAULTS):
        socket=_socket(tree,label,default=default); socket.min_value=0
        if key in ('damage','crack_share','chip_share','spall_density','crack_dirt','crack_density','chip_density'):
            socket.max_value=1
        elif key=='force_kind': socket.max_value=3
        elif key=='shell_exponent': socket.min_value,socket.max_value=.2,2
        elif key in ('warp_scale','crack_cell'): socket.min_value=1e-8
        elif key=='piece_tilt': socket.subtype='ANGLE'
    _socket(tree,'On',default=1.)
    for label in _OUTPUTS: _socket(tree,label,'OUTPUT')
    a=_DamageGraph(tree); m=a.m
    i=a.node('NodeGroupInput').outputs
    out=a.node('NodeGroupOutput'); out.is_active_output=True
    damaged=m('MULTIPLY',i['On'],m('LESS_THAN',_rand(a,i['Cell'],101),i['Fraction']))
    draw=_rand(a,i['Cell'],103)
    kind=m('SUBTRACT',3,m('ADD',m('LESS_THAN',draw,i['Crack Share']),m('LESS_THAN',draw,m('ADD',i['Crack Share'],i['Chip Share']))))
    kind=a.mix(m('GREATER_THAN',i['Force Kind'],0),kind,i['Force Kind'])
    inside=m('MULTIPLY',damaged,m('GREATER_THAN',i['Edge'],0))
    crack_tile=m('MULTIPLY',inside,m('COMPARE',kind,1))
    chip_tile=m('MULTIPLY',inside,m('MAXIMUM',m('COMPARE',kind,2),m('MULTIPLY',m('COMPARE',kind,1),
                          m('LESS_THAN',_rand(a,i['Cell'],901),m('MULTIPLY',i['Chip Share'],.5)))))
    chip_tile=m('MULTIPLY',chip_tile,m('GREATER_THAN',i['Chip Size'],0))
    flake_tile=m('MULTIPLY',inside,m('COMPARE',kind,3))
    flake_tile=m('MULTIPLY',flake_tile,m('GREATER_THAN',i['Chip Size'],0))
    p=a.v('MULTIPLY',i['Tile UV'],i['Tile Size'])
    w,h,_=a.split(i['Tile Size'])
    q,phase=_warp(a,i,p)
    crack_cell=m('MAXIMUM',m('MULTIPLY',i['Crack Cell'],a.mad(_rand(a,i['Cell'],903),1.,.6)),1e-8)
    # SPEC v7 calls for a per-tile network origin as well as a warp offset. Phase
    # is subtracted from Position so sites/tilt pivots remain in tile-frame metres.
    distance,colours,site=_voronoi(a,q,crack_cell,phase)
    picked=m('LESS_THAN',colours[0],i['Crack Density'])
    patch=a.smooth(a.noise(p,m('DIVIDE',1,m('MULTIPLY',2,crack_cell)),detail=2),.35,.55)
    keep=m('MULTIPLY',picked,patch)
    width_noise=a.noise(a.v('ADD',q,a.v('MULTIPLY',phase,a.xyz(crack_cell,crack_cell,0))),
                       m('DIVIDE',1,crack_cell),detail=2)
    half=m('MULTIPLY',m('MULTIPLY',.5,i['Crack Width']),a.mad(width_noise,1.5,.5))
    crack=m('MULTIPLY',crack_tile,m('MULTIPLY',keep,m('LESS_THAN',distance,half)))
    ph,piece=_piece_fields(a,i,p,site,colours,m('MULTIPLY',crack_tile,picked))
    # Where the patch mask fades the crack out, its piece must not step either: scale lift and tilt by the
    # mask at the cell site (one value per cell, so each piece stays a plane).
    ph=m('MULTIPLY',ph,a.smooth(a.noise(site,m('DIVIDE',1,m('MULTIPLY',2,crack_cell)),detail=2),.35,.55))
    r=_rand(a,i['Cell'],907)
    chip_cell=m('MAXIMUM',m('MULTIPLY',i['Chip Size'],a.mad(m('MULTIPLY',r,r),.65,.35)),1e-8)
    fine,fine_colours,fine_site=_voronoi(a,q,chip_cell,a.v('ADD',phase,(31,47,0)))
    selected,chip_depth,chip_identity,site_edge,e_shell=_fine_fields(a,i,p,fine,fine_colours,fine_site,chip_cell,w,h)
    chip=m('MULTIPLY',selected,m('MAXIMUM',chip_tile,flake_tile))
    e_chip=a.mix(chip,-1e10,e_shell)
    depth=m('MULTIPLY',selected,m('ADD',m('MULTIPLY',chip_tile,chip_depth),m('MULTIPLY',flake_tile,i['Glaze Thickness'])))
    spall=m('MULTIPLY',crack_tile,m('MULTIPLY',m('GREATER_THAN',i['Spall Size'],0),
            m('MULTIPLY',m('GREATER_THAN',keep,0),m('LESS_THAN',fine_colours[0],i['Spall Density']))))
    spall_e=m('MINIMUM',fine,m('SUBTRACT',i['Spall Size'],distance))
    e=m('MAXIMUM',e_chip,a.mix(spall,-1e10,spall_e))
    # Crack spalls flake glaze, at most into the slip; glaze+slip exactly would count as clay.
    spall_depth=a.mad(m('MULTIPLY',.5,i['Engobe Thickness']),m('LESS_THAN',fine_colours[1],.25),i['Glaze Thickness'])
    depth=m('MAXIMUM',depth,m('MULTIPLY',m('MULTIPLY',spall,m('GREATER_THAN',spall_e,0)),spall_depth))
    depth,lip,engobe,body=_layers(a,i,e,depth,chip_tile,p)
    stack=m('ADD',i['Glaze Thickness'],i['Engobe Thickness'])
    crack_depth=m('MULTIPLY',crack,m('ADD',stack,i['Crack Depth']))
    dirt=m('MULTIPLY',crack_tile,m('MULTIPLY',i['Crack Dirt'],m('MULTIPLY',keep,
           m('MULTIPLY',m('GREATER_THAN',i['Dirt Width'],0),m('SUBTRACT',1,a.smooth(distance,0,m('MAXIMUM',i['Dirt Width'],1e-9)))))))
    values=(depth,ph,piece,crack,crack_depth,lip,engobe,body,damaged,m('MULTIPLY',damaged,m('DIVIDE',kind,3)),dirt,
            m('MULTIPLY',chip,chip_identity),m('MULTIPLY',crack_tile,picked),m('MULTIPLY',crack_tile,distance),
            m('MULTIPLY',inside,chip_cell),m('MULTIPLY',chip,site_edge))
    for label,value in zip(_OUTPUTS,values): a.put(value,out.inputs[label])
    live=set()
    def visit(node):
        """Prune only unreachable expressions in this newly built group."""
        if node in live: return
        live.add(node)
        for socket in node.inputs:
            for link in socket.links: visit(link.from_node)
    visit(out)
    for node in list(tree.nodes):
        if node not in live: tree.nodes.remove(node)
    tree['tile_damage_version']=_VERSION; tree['tile_damage_revision']=_REVISION
    if old is not None:
        _replace_group_users(old,tree)
        old.user_remap(tree); bpy.data.node_groups.remove(old); tree.name=name
    return tree
