"""Warped, tile-local Voronoi fracture cells, coating loss and rigid piece planes.

Cracks (network, pieces, spalls, dirt band) are look-approved; chips and edge flakes are WORK IN
PROGRESS (shape still under look-dev, controls report them as WIP) — see references/materials/tiles.md
"""
import math
import bpy
from .tile_nodes import _Graph
from .tile_nodes import _socket
from .tile_nodes import _replace_group_users

_VERSION = 7
_REVISION = 1
PIECE_BINS = 65536
PARAMS = dict(damage='Fraction',crack_share='Crack Share',chip_share='Chip Share',
              step_height='Step Height',piece_tilt='Piece Tilt',crack_width='Crack Width',
              crack_depth='Crack Depth',chip_size='Chip Size',chip_depth='Chip Depth',
              spall_size='Spall Size',spall_density='Spall Density',glaze_thickness='Glaze Thickness',
              engobe_thickness='Engobe Thickness',glaze_lip_width='Glaze Lip Width',engobe_ring='Engobe Ring',
              force_kind='Force Kind',shell_exponent='Shell Exponent',crack_dirt='Crack Dirt',
              dirt_width='Dirt Width',warp='Warp',warp_scale='Warp Scale',crack_cell='Crack Cell',
              crack_density='Crack Density',chip_density='Chip Density')
DEFAULTS=(.05,.45,.35,.00015,.0035,.00018,.0008,.004,.0008,.001,.25,.0003,.0002,
          .0002,.0003,0,.6,.85,.004,.004,.02,.03,.35,.5)
_LAYOUT_INPUTS=('Tile ID','Cell','Tile UV','Edge','Tile Size')
_OUTPUTS=('Chip Depth Out','Piece Height','Piece','Crack','Crack Depth Out','Glaze Lip','Engobe',
          'Body','Damaged','Kind','Dirt','Chip','Picked','Crack Distance','Chip Cell','Chip Site Edge')


def _is_current(tree):
    """Require the full v7 contract, not only the version stamp."""
    if tree is None or tree.get('tile_damage_version')!=_VERSION or tree.get('tile_damage_revision')!=_REVISION:
        return False
    sockets={(s.in_out,s.name) for s in tree.interface.items_tree if s.item_type=='SOCKET'}
    return (all(('INPUT',label) in sockets for label in (*_LAYOUT_INPUTS,*PARAMS.values(),'On')) and
            all(('OUTPUT',label) in sockets for label in _OUTPUTS))


class _DamageGraph(_Graph):
    """Intern repeated expressions and use native one-node scalar interpolation."""
    def __init__(self, tree):
        """Keep expression/hash caches local to this group build."""
        super().__init__(tree)
        self.cache = {}
        self.hashes = {}

    def cached(self, key, build):
        """Reuse an identical expression within the current graph."""
        if key not in self.cache:
            self.cache[key] = build()
        return self.cache[key]

    def m(self, op, x, y=0):
        """Fold identities and share repeated scalar expressions."""
        if isinstance(x,(int,float)) and isinstance(y,(int,float)):
            folded = {'MULTIPLY':lambda:x*y,'ADD':lambda:x+y,'SUBTRACT':lambda:x-y,
                      'DIVIDE':lambda:x/y if y else 0.,'MINIMUM':lambda:min(x,y),'MAXIMUM':lambda:max(x,y)}
            if op in folded: return folded[op]()
        if op == 'MULTIPLY':
            if isinstance(x,(int,float)) and x == 0 or isinstance(y,(int,float)) and y == 0: return 0.
            if isinstance(x,(int,float)) and x == 1: return y
            if isinstance(y,(int,float)) and y == 1: return x
        if op in ('ADD','SUBTRACT') and isinstance(y,(int,float)) and y == 0: return x
        if op == 'ADD' and isinstance(x,(int,float)) and x == 0: return y
        if op == 'DIVIDE' and isinstance(y,(int,float)) and y == 1: return x
        if op == 'ADD':
            for term,other in ((x,y),(y,x)):
                node = getattr(term,'node',None)
                if node is not None and node.bl_idname=='ShaderNodeMath' and node.operation=='MULTIPLY':
                    inputs = [s.links[0].from_socket if s.is_linked else s.default_value for s in node.inputs[:2]]
                    return self.mad(*inputs,other)
        return self.cached(('m',op,x,y),lambda: super(_DamageGraph,self).m(op,x,y))

    def v(self, op, x, y):
        """Share vector expressions, including repeated hash coordinates."""
        return self.cached(('v',op,x,y),lambda: super(_DamageGraph,self).v(op,x,y))

    def xyz(self, x, y, z=0):
        """Share scalar-to-vector combinations."""
        return self.cached(('xyz',x,y,z),lambda: super(_DamageGraph,self).xyz(x,y,z))

    def split(self, vector):
        """Separate each vector only once."""
        return self.cached(('split',vector),lambda: super(_DamageGraph,self).split(vector))

    def mix(self, factor, x, y):
        """Interpolate floats with one native Mix node, without clamping values."""
        if x == y: return x
        if isinstance(factor,(int,float)) and factor in (0,1): return y if factor else x
        def build():
            """Use the float sockets of Blender's multi-type Mix node."""
            n = self.node('ShaderNodeMix',data_type='FLOAT',clamp_factor=False)
            for value,socket in zip((factor,x,y),(n.inputs[0],n.inputs[2],n.inputs[3])):
                self.put(value,socket)
            return n.outputs[0]
        return self.cached(('mix',factor,x,y),build)

    def hash_vector(self, cell):
        """One three-component hash per tile/piece/spall cell, reused for draws."""
        if cell not in self.hashes:
            self.hashes[cell] = self.split(self.rand(cell,(101.5,303.5,707.5),True))
        return self.hashes[cell]

    def mad(self, x, y, z):
        """Fuse a scalar multiply and add without introducing a nested group."""
        def build():
            """Wire the native three-input operation."""
            n = self.node('ShaderNodeMath',operation='MULTIPLY_ADD')
            for value,socket in zip((x,y,z),n.inputs): self.put(value,socket)
            return n.outputs[0]
        return self.cached(('mad',x,y,z),build)

    def knot(self, coordinate):
        """Hash one 1D knot directly, sharing both adjacent evaluations."""
        def build():
            """Use W rather than constructing a redundant 3D vector."""
            n = self.node('ShaderNodeTexWhiteNoise',noise_dimensions='1D')
            self.put(coordinate,n.inputs['W'])
            return n.outputs['Value']
        return self.cached(('knot',coordinate),build)

    def clamp(self, value, lo, hi):
        """Clamp with one native node instead of two scalar comparisons."""
        def build():
            """Wire physical min/max bounds explicitly."""
            n = self.node('ShaderNodeClamp')
            for value_,socket in zip((value,lo,hi),n.inputs): self.put(value_,socket)
            return n.outputs[0]
        return self.cached(('clamp',value,lo,hi),build)

    def length(self, vector):
        """Read the scalar output of native vector Length."""
        def build():
            """Avoid repeated square/add/square-root scalar nodes."""
            n = self.node('ShaderNodeVectorMath',operation='LENGTH')
            self.put(vector,n.inputs[0])
            return n.outputs['Value']
        return self.cached(('length',vector),build)

    def interval(self,value,lo,hi,first,second):
        """Interpolate adjacent knots directly over their integer interval."""
        def build():
            """Fuse fraction extraction and linear interpolation in one Map Range."""
            n=self.node('ShaderNodeMapRange',interpolation_type='LINEAR',clamp=False)
            for value_,socket in zip((value,lo,hi,first,second),n.inputs[:5]): self.put(value_,socket)
            return n.outputs[0]
        return self.cached(('interval',value,lo,hi,first,second),build)


def _rand(a, cell, seed):
    """Derive reproducible draws from shared hash components with scale-and-fract."""
    value = a.hash_vector(cell)[seed % 3]
    if seed == 101: return value
    return a.m('FRACT', a.mad(value,1+(seed%29)*1.61803398875,seed*.037))


def _voronoi(a,q,cell,phase):
    """Share one 2D edge/F1 pair; return metre distance, cell colour and metre site."""
    vector=a.v('ADD',a.v('DIVIDE',q,a.xyz(cell,cell,1)),phase)
    edge=a.node('ShaderNodeTexVoronoi',voronoi_dimensions='2D',feature='DISTANCE_TO_EDGE')
    first=a.node('ShaderNodeTexVoronoi',voronoi_dimensions='2D',feature='F1',distance='EUCLIDEAN')
    for node in (edge,first):
        a.put(vector,node.inputs['Vector'])
        node.inputs['Scale'].default_value=1
        node.inputs['Randomness'].default_value=1
    site=a.v('MULTIPLY',a.v('SUBTRACT',first.outputs['Position'],phase),a.xyz(cell,cell,0))
    return a.m('MULTIPLY',edge.outputs['Distance'],cell),a.split(first.outputs['Color']),site


def _warp(a,i,p):
    """Warp metres by one RGB noise field and share the per-tile hash offset."""
    offset=a.v('MULTIPLY',a.xyz(*a.hash_vector(i['Cell'])),(100,100,0))
    scale=a.m('MAXIMUM',i['Warp Scale'],1e-9)
    vector=a.v('ADD',a.v('DIVIDE',p,a.xyz(scale,scale,1)),offset)
    noise=a.noise(vector,1,detail=2).node.outputs['Color']
    q=a.v('ADD',p,a.v('MULTIPLY',a.v('SUBTRACT',noise,(.5,.5,.5)),a.xyz(i['Warp'],i['Warp'],0)))
    return q,offset


def _piece_fields(a,i,p,site,colours,picked):
    """Give each picked F1 cell one rigid plane about its constant metre site."""
    m=a.m
    red,green,blue=colours
    lift=m('MULTIPLY',i['Step Height'],m('MULTIPLY',a.mad(green,2,-1),a.mad(blue,.7,.3)))
    slope=m('TANGENT',m('MULTIPLY',i['Piece Tilt'],a.mad(blue,2,-1)))
    angle=m('MULTIPLY',math.tau,green)
    delta=a.v('SUBTRACT',p,site)
    tilt=m('MULTIPLY',slope,a.v('DOT_PRODUCT',delta,a.xyz(m('COSINE',angle),m('SINE',angle))))
    height=m('MULTIPLY',picked,m('ADD',lift,tilt))
    identity=m('DIVIDE',m('ADD',1,m('FLOOR',m('MULTIPLY',red,PIECE_BINS-1))),PIECE_BINS)
    return height,m('MULTIPLY',picked,identity)


def _fine_fields(a,i,p,distance,colours,site,cell,w,h):
    """Pick outline-adjacent chip cells and assign coating-only or conchoidal depth."""
    m=a.m
    x,y,_=a.split(site)
    edge=m('MINIMUM',m('MINIMUM',m('ABSOLUTE',x),m('ABSOLUTE',m('SUBTRACT',w,x))),
           m('MINIMUM',m('ABSOLUTE',y),m('ABSOLUTE',m('SUBTRACT',h,y))))
    red,green,blue=colours
    rnd=lambda k: m('FRACT',m('MULTIPLY',red,k))              # further per-cell draws from the same hash
    # Arris chips: the tile outline must cut the cell (site within 0.35 cell of it), never an island.
    at_edge=m('LESS_THAN',edge,m('MULTIPLY',.35,cell))
    edge_pick=m('MULTIPLY',at_edge,m('LESS_THAN',red,i['Chip Density']))
    # Face pop-outs: a few interior cells become small glaze spalls (impact chips are rarely all on edges).
    face_pick=m('MULTIPLY',m('SUBTRACT',1,at_edge),m('LESS_THAN',rnd(29.3),m('MULTIPLY',.1,i['Chip Density'])))
    # Size per chip, heavy-tailed (most small, few big): shrinks the chip inward from the arris and along it.
    size=a.mad(m('MULTIPLY',rnd(13.7),rnd(13.7)),.75,.25)
    # Half-disc proportions (~2:1 along the arris : inward): size trims the length along the edge (inset from the
    # cell sides) more than the depth into the tile, so small chips do not become slivers.
    # Rounded inner edge: a disc about the cell site, reaching past the arris (radius = site's distance to the
    # outline + the chip's depth), clipped by the cell's own irregular sides -> a curved shell bite, not a strip.
    # Kept inside the cell (a pixel only sees its own cell, so a larger disc would be clipped to straight sides).
    radius=m('ADD',edge,m('MULTIPLY',m('MULTIPLY',.35,cell),a.mad(size,.6,.4)))
    band=m('SUBTRACT',radius,a.length(a.v('SUBTRACT',p,site)))
    e_edge=m('MINIMUM',m('SUBTRACT',distance,m('MULTIPLY',m('MULTIPLY',.35,cell),m('SUBTRACT',1,size))),band)
    face_size=a.mad(rnd(41.1),.25,.1)
    e_face=m('SUBTRACT',distance,m('MULTIPLY',m('MULTIPLY',.25,cell),m('SUBTRACT',1,face_size)))
    e_shell=a.mix(face_pick,e_edge,e_face)
    selected=m('MAXIMUM',edge_pick,face_pick)
    # Conchoidal shell: deepest at the arris (layout Edge = metres to the tile outline), shallowing inward,
    # with a short ramp up from the chip's own outline.
    # Glaze breaks with a steep wall: the depth ramps up over 5 % of the chip, so the wall casts a shadow.
    rim=a.clamp(m('DIVIDE',e_shell,m('MULTIPLY',m('MULTIPLY',.05,cell),size)),0,1)
    inward=a.clamp(m('DIVIDE',i['Edge'],m('MULTIPLY',1.2,radius)),0,1)   # falloff over the chip's own reach
    deep=m('MULTIPLY',i['Chip Depth'],m('MULTIPLY',a.mad(blue,.6,.4),a.mad(size,.5,.5)))
    wave=m('SINE',m('DIVIDE',m('MULTIPLY',math.tau*6,a.length(a.v('SUBTRACT',p,site))),cell))
    ripple=m('MULTIPLY',m('MULTIPLY',.05,deep),m('MULTIPLY',rim,wave))
    shape=m('MULTIPLY',m('POWER',rim,i['Shell Exponent']),m('POWER',m('SUBTRACT',1,inward),.4))
    profile=m('MAXIMUM',i['Glaze Thickness'],a.mad(deep,shape,ripple))
    edge_depth=a.mix(m('LESS_THAN',green,.25),profile,i['Glaze Thickness'])   # 25 % glaze-only arris flakes
    # Pop-outs never reach the clay: glaze only, or into (not through) the slip.
    face_depth=a.mad(m('MULTIPLY',.5,i['Engobe Thickness']),m('LESS_THAN',green,.35),i['Glaze Thickness'])
    depth=a.mix(face_pick,edge_depth,face_depth)
    identity=m('DIVIDE',m('ADD',1,m('FLOOR',m('MULTIPLY',red,PIECE_BINS-1))),PIECE_BINS)
    return selected,depth,identity,edge,e_shell


def _layers(a, i, e, depth, deep, p):
    """Apply hard coating strata and include clay relief in the physical removal field."""
    m = a.m
    shell = m('GREATER_THAN', e, 0)
    lip = m('MULTIPLY', shell, m('LESS_THAN', e, i['Glaze Lip Width']))
    ring = m('LESS_THAN', e, m('ADD', i['Glaze Lip Width'], i['Engobe Ring']))
    layers = m('ADD', i['Glaze Thickness'], i['Engobe Thickness'])
    reaches_body = m('GREATER_THAN', depth, m('SUBTRACT', layers, 1e-8))
    body = m('MULTIPLY', m('MULTIPLY', shell, m('SUBTRACT', 1, ring)), reaches_body)
    grain_uv = a.v('ADD', p, a.xyz(*a.hash_vector(i['Cell'])))
    relief = m('MULTIPLY', .00015, a.amplitude(grain_uv, 1/.00045))
    # Relief belongs only to exposed body. Its amplitude fades at the actual
    # depth threshold, so it cannot manufacture clay in a shallow shell.
    relief = m('MULTIPLY',relief,m('MINIMUM',1,m('DIVIDE',m('MAXIMUM',m('SUBTRACT',depth,layers),0),.00015)))
    removed = m('MULTIPLY',shell,m('MAXIMUM',i['Glaze Thickness'],
                m('SUBTRACT',depth,m('MULTIPLY',body,relief))))
    # Depth thresholds and the inward rings both apply; nothing forces Body.
    body = m('MULTIPLY',body,m('GREATER_THAN',removed,m('SUBTRACT',layers,1e-8)))
    engobe = m('MULTIPLY',shell,m('SUBTRACT',1,m('ADD',lip,body)))
    return removed, lip, engobe, body


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


def damage_bsdfs(a, i, intact, color, height, d):
    """Shade exposed clay, engobe and dirt independently of the coated glaze."""
    m, v = a.m, a.v
    # The face Principled is the first input of tile_surface's face/grout mix.
    # Change only its pigment: all coat inputs and the grout shader stay intact.
    face = intact.node.inputs[1].links[0].from_node
    attenuation = m('SUBTRACT',1,d['Dirt'])
    a.put(v('MULTIPLY',color,a.xyz(attenuation,attenuation,attenuation)),face.inputs['Base Color'])
    grain = a.amplitude(a.v('ADD', i['World'], a.rand(i['Cell'], (563, 569, 571), True)), 1/.00045)
    grog = m('GREATER_THAN', a.noise(i['World'], 1/.0005), .7)
    iron = m('LESS_THAN', a.noise(a.v('ADD', i['World'], (17, 23, 31)), 1/.0004), .28)
    tone = m('MULTIPLY', m('ADD', .85, m('MULTIPLY', .3, a.rand(i['Cell'], (521, 541, 557)))),
             m('ADD', 1, m('MULTIPLY', .2, grain)))
    # Red-firing body, linear; slip and body colours become knobs with the chip work (chips are WIP).
    clay_color = v('MULTIPLY', (.30, .17, .10), a.xyz(tone, tone, tone))
    specks = m('MULTIPLY', m('ADD', 1, m('MULTIPLY', .4, grog)), m('SUBTRACT', 1, m('MULTIPLY', .35, iron)))
    clay_color = v('MULTIPLY', clay_color, a.xyz(specks, specks, specks))
    # The existing dust colour is the same physical deposit inside the deepest bowls.
    deposit = m('MULTIPLY', m('MULTIPLY', i['Dust'], i['dust On']),
                m('MULTIPLY', .2, a.smooth(d['Chip Depth Out'], .0015, .0025)))
    clay_color = v('ADD', v('MULTIPLY', clay_color, a.xyz(m('SUBTRACT', 1, deposit), m('SUBTRACT', 1, deposit), m('SUBTRACT', 1, deposit))),
                   v('MULTIPLY', i['Grout Albedo'], a.xyz(deposit, deposit, deposit)))
    bump = a.node('ShaderNodeBump'); bump.name = 'DamageBump'
    bump.inputs['Distance'].default_value = 1
    a.put(height, bump.inputs['Height'])
    fine = a.node('ShaderNodeBump'); fine.inputs['Distance'].default_value = .00003
    fine.name = 'ClayGrainBump'
    a.put(a.noise(i['World'], 1/.0001), fine.inputs['Height']); a.put(bump.outputs['Normal'], fine.inputs['Normal'])
    def material(base, rough, normal):
        bsdf = a.node('ShaderNodeBsdfPrincipled')
        a.put(base, bsdf.inputs['Base Color']); bsdf.inputs['Roughness'].default_value = rough
        bsdf.inputs['Coat Weight'].default_value = 0
        a.put(normal, bsdf.inputs['Normal'])
        return bsdf.outputs['BSDF']
    def mix(mask, first, second):
        node = a.node('ShaderNodeMixShader')
        for value, socket in zip((mask, first, second), node.inputs):
            a.put(value, socket)
        return node.outputs[0]
    shader = mix(d['Engobe'], intact, material((.70, .70, .70), .9, bump.outputs['Normal']))
    shader = mix(d['Body'], shader, material(clay_color, .9, fine.outputs['Normal']))
    dark = v('MULTIPLY', color, (.25, .25, .25))
    return mix(d['Crack'], shader, material(dark, .9, bump.outputs['Normal']))
