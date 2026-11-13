"""Damage fields; canonical implementation behind tile_damage."""

import math

from materials.tile.damage_contract import PIECE_BINS

def _rand(graph, cell, seed):
    """Derive reproducible draws from shared hash components with scale-and-fract."""
    value = graph.hash_vector(cell)[seed % 3]
    if seed == 101: return value
    return graph.math('FRACT', graph.multiply_add(value,1+(seed%29)*1.61803398875,seed*.037))

def _voronoi(graph,q,cell,phase):
    """Share one 2D edge/F1 pair; return metre distance, cell colour and metre site."""
    vector=graph.vector_math('ADD',graph.vector_math('DIVIDE',q,graph.combine_xyz(cell,cell,1)),phase)
    edge=graph.node('ShaderNodeTexVoronoi',voronoi_dimensions='2D',feature='DISTANCE_TO_EDGE')
    first=graph.node('ShaderNodeTexVoronoi',voronoi_dimensions='2D',feature='F1',distance='EUCLIDEAN')
    for node in (edge,first):
        graph.link_or_set(vector,node.inputs['Vector'])
        node.inputs['Scale'].default_value=1
        node.inputs['Randomness'].default_value=1
    site=graph.vector_math('MULTIPLY',graph.vector_math('SUBTRACT',first.outputs['Position'],phase),graph.combine_xyz(cell,cell,0))
    return graph.math('MULTIPLY',edge.outputs['Distance'],cell),graph.separate_xyz(first.outputs['Color']),site

def _warp(graph,inputs,p):
    """Warp metres by one RGB noise field and share the per-tile hash offset."""
    offset=graph.vector_math('MULTIPLY',graph.combine_xyz(*graph.hash_vector(inputs['Cell'])),(100,100,0))
    scale=graph.math('MAXIMUM',inputs['Warp Scale'],1e-9)
    vector=graph.vector_math('ADD',graph.vector_math('DIVIDE',p,graph.combine_xyz(scale,scale,1)),offset)
    noise=graph.noise_texture(vector,1,detail=2).node.outputs['Color']
    q=graph.vector_math('ADD',p,graph.vector_math('MULTIPLY',graph.vector_math('SUBTRACT',noise,(.5,.5,.5)),graph.combine_xyz(inputs['Warp'],inputs['Warp'],0)))
    return q,offset

def _piece_fields(graph,inputs,p,site,colours,picked):
    """Give each picked F1 cell one rigid plane about its constant metre site."""
    m=graph.math
    red,green,blue=colours
    lift=m('MULTIPLY',inputs['Step Height'],m('MULTIPLY',graph.multiply_add(green,2,-1),graph.multiply_add(blue,.7,.3)))
    slope=m('TANGENT',m('MULTIPLY',inputs['Piece Tilt'],graph.multiply_add(blue,2,-1)))
    angle=m('MULTIPLY',math.tau,green)
    delta=graph.vector_math('SUBTRACT',p,site)
    tilt=m('MULTIPLY',slope,graph.vector_math('DOT_PRODUCT',delta,graph.combine_xyz(m('COSINE',angle),m('SINE',angle))))
    height=m('MULTIPLY',picked,m('ADD',lift,tilt))
    identity=m('DIVIDE',m('ADD',1,m('FLOOR',m('MULTIPLY',red,PIECE_BINS-1))),PIECE_BINS)
    return height,m('MULTIPLY',picked,identity)

def _fine_fields(graph,inputs,p,distance,colours,site,cell,w,h):
    """Pick outline-adjacent chip cells and assign coating-only or conchoidal depth."""
    m=graph.math
    x,y,_=graph.separate_xyz(site)
    edge=m('MINIMUM',m('MINIMUM',m('ABSOLUTE',x),m('ABSOLUTE',m('SUBTRACT',w,x))),
           m('MINIMUM',m('ABSOLUTE',y),m('ABSOLUTE',m('SUBTRACT',h,y))))
    red,green,blue=colours
    rnd=lambda k: m('FRACT',m('MULTIPLY',red,k))              # further per-cell draws from the same hash
    # Arris chips: the tile outline must cut the cell (site within 0.35 cell of it), never an island.
    at_edge=m('LESS_THAN',edge,m('MULTIPLY',.35,cell))
    edge_pick=m('MULTIPLY',at_edge,m('LESS_THAN',red,inputs['Chip Density']))
    # Face pop-outs: a few interior cells become small glaze spalls (impact chips are rarely all on edges).
    face_pick=m('MULTIPLY',m('SUBTRACT',1,at_edge),m('LESS_THAN',rnd(29.3),m('MULTIPLY',.1,inputs['Chip Density'])))
    # Size per chip, heavy-tailed (most small, few big): shrinks the chip inward from the arris and along it.
    size=graph.multiply_add(m('MULTIPLY',rnd(13.7),rnd(13.7)),.75,.25)
    # Half-disc proportions (~2:1 along the arris : inward): size trims the length along the edge (inset from the
    # cell sides) more than the depth into the tile, so small chips do not become slivers.
    # Rounded inner edge: a disc about the cell site, reaching past the arris (radius = site's distance to the
    # outline + the chip's depth), clipped by the cell's own irregular sides -> a curved shell bite, not a strip.
    # Kept inside the cell (a pixel only sees its own cell, so a larger disc would be clipped to straight sides).
    radius=m('ADD',edge,m('MULTIPLY',m('MULTIPLY',.35,cell),graph.multiply_add(size,.6,.4)))
    band=m('SUBTRACT',radius,graph.length(graph.vector_math('SUBTRACT',p,site)))
    e_edge=m('MINIMUM',m('SUBTRACT',distance,m('MULTIPLY',m('MULTIPLY',.35,cell),m('SUBTRACT',1,size))),band)
    face_size=graph.multiply_add(rnd(41.1),.25,.1)
    e_face=m('SUBTRACT',distance,m('MULTIPLY',m('MULTIPLY',.25,cell),m('SUBTRACT',1,face_size)))
    e_shell=graph.mix(face_pick,e_edge,e_face)
    selected=m('MAXIMUM',edge_pick,face_pick)
    # Conchoidal shell: deepest at the arris (layout Edge = metres to the tile outline), shallowing inward,
    # with a short ramp up from the chip's own outline.
    # Glaze breaks with a steep wall: the depth ramps up over 5 % of the chip, so the wall casts a shadow.
    rim=graph.clamp(m('DIVIDE',e_shell,m('MULTIPLY',m('MULTIPLY',.05,cell),size)),0,1)
    inward=graph.clamp(m('DIVIDE',inputs['Edge'],m('MULTIPLY',1.2,radius)),0,1)   # falloff over the chip's own reach
    deep=m('MULTIPLY',inputs['Chip Depth'],m('MULTIPLY',graph.multiply_add(blue,.6,.4),graph.multiply_add(size,.5,.5)))
    wave=m('SINE',m('DIVIDE',m('MULTIPLY',math.tau*6,graph.length(graph.vector_math('SUBTRACT',p,site))),cell))
    ripple=m('MULTIPLY',m('MULTIPLY',.05,deep),m('MULTIPLY',rim,wave))
    shape=m('MULTIPLY',m('POWER',rim,inputs['Shell Exponent']),m('POWER',m('SUBTRACT',1,inward),.4))
    profile=m('MAXIMUM',inputs['Glaze Thickness'],graph.multiply_add(deep,shape,ripple))
    edge_depth=graph.mix(m('LESS_THAN',green,.25),profile,inputs['Glaze Thickness'])   # 25 % glaze-only arris flakes
    # Pop-outs never reach the clay: glaze only, or into (not through) the slip.
    face_depth=graph.multiply_add(m('MULTIPLY',.5,inputs['Engobe Thickness']),m('LESS_THAN',green,.35),inputs['Glaze Thickness'])
    depth=graph.mix(face_pick,edge_depth,face_depth)
    identity=m('DIVIDE',m('ADD',1,m('FLOOR',m('MULTIPLY',red,PIECE_BINS-1))),PIECE_BINS)
    return selected,depth,identity,edge,e_shell
