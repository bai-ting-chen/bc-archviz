"""Metre-valued brittle ceramic fracture fields in each tile's rotated frame."""
import math

import bpy
from tile_nodes import _Graph, _socket, _replace_group_users

_VERSION = 6
PARAMS = dict(damage='Fraction', crack_share='Crack Share', chip_share='Chip Share',
              branch_share='Branch Share', step_height='Step Height', piece_tilt='Piece Tilt',
              crack_width='Crack Width', crack_depth='Crack Depth', kink_size='Kink Size',
              kink_amp='Kink Amp', chip_size='Chip Size', chip_depth='Chip Depth',
              spall_size='Spall Size', spall_density='Spall Density', glaze_thickness='Glaze Thickness',
              engobe_thickness='Engobe Thickness', glaze_lip_width='Glaze Lip Width',
              engobe_ring='Engobe Ring', force_kind='Force Kind', shell_exponent='Shell Exponent',
              crack_dirt='Crack Dirt', dirt_width='Dirt Width')
DEFAULTS = (.05, .45, .35, .35, .00006, .0035, .00018, .0008, .0015, .0002, .004, .0008,
            .001, .25, .0003, .0002, .0002, .0003, 0, .6, .6, .002)
_LAYOUT_INPUTS = ('Tile ID','Cell','Tile UV','Edge','Tile Size')
_OUTPUTS = ('Chip Depth Out','Piece Height','Piece','Crack','Crack Depth Out',
            'Glaze Lip','Engobe','Body','Damaged','Kind','Dirt')


def _is_current(tree):
    """Require the complete v6 interface as well as the implementation stamp."""
    if tree is None or tree.get('tile_damage_version') != _VERSION or tree.get('tile_damage_revision') != 2:
        return False
    sockets = {(item.in_out,item.name) for item in tree.interface.items_tree if item.item_type=='SOCKET'}
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


def _signed(a, value):
    """Map a uniform unit draw onto a signed unit interval."""
    return a.mad(value,2,-1)


def _kink(a, t, size, amp, seed):
    """Linearly interpolate independent knots at two physical arc-length scales."""
    m, draws = a.m, []
    frequency = m('DIVIDE',1,m('MAXIMUM',size,1e-9))
    base = a.mad(t,frequency,seed)
    for octave in (1, 3):
        q = base if octave==1 else a.mad(base,3,37)
        knot = m('FLOOR',q); next_knot=m('ADD',knot,1)
        first, second = a.knot(knot), a.knot(next_knot)
        draws.append(_signed(a,a.interval(q,knot,next_knot,first,second)))
    return m('MULTIPLY',amp,a.mad(draws[1],1/3,draws[0]))


def _jagged_distance(a, p, p0, d, n, length, bow, kink_size, kink_amp, seed):
    """Return signed distance to a bowed chord with piecewise-linear arc-length kinks."""
    m = a.m
    delta = a.v('SUBTRACT', p, p0)
    t = a.v('DOT_PRODUCT', delta, d)
    # Hold the bow at its chord endpoints outside the finite line length; extrapolating
    # the quadratic would create a second shell far beyond a corner chip.
    u = a.clamp(m('DIVIDE',t,m('MAXIMUM',length,1e-9)),-.5,.5)
    shape = m('SUBTRACT', 1/3, m('MULTIPLY', 4, m('MULTIPLY',u,u)))
    curve = m('MULTIPLY', m('MULTIPLY', bow, length), shape)
    return m('SUBTRACT', a.v('DOT_PRODUCT', delta, n),
             m('ADD', curve, _kink(a, t, kink_size, kink_amp, seed)))


def _radial_distance(a, tangent, normal, radius, i, seed, arc=math.pi):
    """Use the same jagged primitive in unwrapped radial and arc-length coordinates."""
    m = a.m
    theta = m('ARCTAN2', normal, tangent)
    t = m('MULTIPLY', radius, theta)
    rho = a.length(a.xyz(tangent,normal))
    distance = m('SUBTRACT',m('SUBTRACT',rho,radius),_kink(a,t,i['Kink Size'],i['Kink Amp'],seed))
    return distance, t


def _cracks(a, i, p, w, h):
    """Anchor C1 on both long edges, with a closed-form endpoint-centred C2."""
    m = a.m
    x, y, _ = a.split(p)
    rand = lambda seed: _rand(a, i['Cell'], seed)
    # Endpoints reserve eight percent of the long edge at either end, including
    # squares. The field is a graph over x, so endpoint anchoring needs no solver.
    limit = m('MINIMUM', math.radians(25), m('ARCTANGENT',m('DIVIDE',m('MULTIPLY',.24,h),w)))
    angle = m('MULTIPLY',_signed(a,rand(201)),limit)
    co, slope = m('COSINE',angle), m('TANGENT',angle)
    py = m('MULTIPLY',h,m('ADD',.2,m('MULTIPLY',.6,rand(203))))
    half_w = m('MULTIPLY',w,.5)
    length = m('DIVIDE',w,co)
    bow = m('MULTIPLY',.05,_signed(a,rand(205)))
    phase = m('MULTIPLY',97,rand(207))

    def line_at(xx):
        """Evaluate the anchored bow and piecewise-linear, endpoint-bounded kinks."""
        u = a.clamp(m('DIVIDE',xx,w),0,1)
        mid = m('SUBTRACT',u,.5)
        t = m('MULTIPLY',mid,length)
        # The raw midpoint-coordinate bow is symmetric and zero-mean. Subtract
        # its equal endpoint value to place that chord ON the chosen endpoints.
        shape = m('SUBTRACT',1/3,m('MULTIPLY',4,m('MULTIPLY',mid,mid)))
        curve = m('MULTIPLY',m('MULTIPLY',bow,length),m('ADD',shape,2/3))
        knots = _kink(a,t,i['Kink Size'],i['Kink Amp'],phase)
        envelope = m('MULTIPLY',m('MULTIPLY',4,i['Kink Amp']),m('MINIMUM',u,m('SUBTRACT',1,u)))
        knots = a.clamp(knots,m('MULTIPLY',-1,envelope),envelope)
        base = a.mad(m('SUBTRACT',xx,half_w),slope,py)
        yy = m('ADD',base,m('DIVIDE',m('ADD',curve,knots),co))
        return a.clamp(yy,m('MULTIPLY',.08,h),m('MULTIPLY',.92,h))

    s1 = m('MULTIPLY',co,m('SUBTRACT',y,line_at(x)))
    t1 = m('DIVIDE',m('SUBTRACT',x,half_w),co)

    def point1(t):
        """Place spall centres directly on the actual anchored C1 graph."""
        xx = m('ADD',half_w,m('MULTIPLY',t,co))
        return a.xyz(xx,line_at(xx))

    right = m('GREATER_THAN',rand(211),.5)
    cx = m('MULTIPLY',right,w)
    cy = m('ADD',py,m('MULTIPLY',m('SUBTRACT',cx,half_w),slope))
    direction = a.mix(right,1.,-1.)
    side = a.mix(m('GREATER_THAN',rand(213),.5),-1.,1.)
    inward = m('MULTIPLY',m('SUBTRACT',x,cx),direction)
    dy = m('MULTIPLY',side,m('SUBTRACT',y,cy))
    radius = m('MULTIPLY',w,m('ADD',.3,m('MULTIPLY',.5,rand(217))))
    phase2 = m('MULTIPLY',97,rand(219))
    s2,t2 = _radial_distance(a,inward,dy,radius,i,phase2,math.pi/2)

    def point2(t):
        """Place the C2 spall centre on the kinked circle in tile coordinates."""
        theta = m('DIVIDE',t,m('MAXIMUM',radius,1e-9))
        r = m('ADD',radius,_kink(a,t,i['Kink Size'],i['Kink Amp'],phase2))
        xx = m('ADD',cx,m('MULTIPLY',direction,m('MULTIPLY',r,m('COSINE',theta))))
        yy = m('ADD',cy,m('MULTIPLY',side,m('MULTIPLY',r,m('SINE',theta))))
        return a.xyz(xx,yy)

    active2 = m('MULTIPLY',m('LESS_THAN',rand(223),i['Branch Share']),
                m('MULTIPLY',m('GREATER_THAN',inward,-1e-8),m('GREATER_THAN',m('MULTIPLY',side,s1),0)))
    piece = m('ADD',m('GREATER_THAN',s1,0),m('MULTIPLY',2,m('MULTIPLY',active2,m('LESS_THAN',s2,0))))
    half = m('MULTIPLY',i['Crack Width'],.5)
    gap = m('MAXIMUM',m('LESS_THAN',m('ABSOLUTE',s1),half),
            m('MULTIPLY',active2,m('LESS_THAN',m('ABSOLUTE',s2),half)))
    return gap,piece,((s1,t1,1.,point1),(s2,t2,active2,point2))


def _piece_height(a, i, p, w, h, piece):
    """Give each nonzero piece a rigid plane through the tile centre plus a signed lift."""
    m = a.m
    cell = a.v('ADD', i['Cell'], a.xyz(0, 0, m('MULTIPLY', piece, 17)))
    lift = m('MULTIPLY', i['Step Height'], _signed(a, _rand(a, cell, 301)))
    slope = m('TANGENT', m('MULTIPLY', i['Piece Tilt'], _signed(a, _rand(a, cell, 307))))
    axis = m('MULTIPLY', math.tau, _rand(a, cell, 311))
    offset = a.v('SUBTRACT', p, a.xyz(m('MULTIPLY', w, .5), m('MULTIPLY', h, .5)))
    tilt = m('MULTIPLY', slope, a.v('DOT_PRODUCT', offset, a.xyz(m('COSINE', axis), m('SINE', axis))))
    return m('MULTIPLY', m('GREATER_THAN', piece, 0), m('ADD', lift, tilt))


def _corner_frame(a, i, p, w, h):
    """Fold the selected corner to the origin without changing physical units."""
    m = a.m
    x,y,_ = a.split(p)
    corner = m('FLOOR',m('MULTIPLY',4,_rand(a,i['Cell'],401)))
    return (a.mix(m('MODULO',corner,2),x,m('SUBTRACT',w,x)),
            a.mix(m('GREATER_THAN',corner,1.5),y,m('SUBTRACT',h,y)))


def _flake_frame(a, i, p, w, h, rand):
    """Express an edge flake in tangent/normal coordinates about its edge centre."""
    m = a.m
    x,y,_ = a.split(p)
    edge = m('FLOOR',m('MULTIPLY',4,rand(0)))
    vertical,second = m('LESS_THAN',edge,2),m('MODULO',edge,2)
    normal = a.mix(vertical,a.mix(second,y,m('SUBTRACT',h,y)),a.mix(second,x,m('SUBTRACT',w,x)))
    tangent = m('SUBTRACT',a.mix(vertical,x,y),m('MULTIPLY',rand(2),a.mix(vertical,w,h)))
    return tangent,normal


def _shells(a, i, p, w, h, size, spall_size, corner_kind):
    """Union 2-4 corner scars or 1-3 edge flakes, sharing the four radial primitives."""
    m = a.m
    x,y = _corner_frame(a,i,p,w,h)
    flip = m('GREATER_THAN',_rand(a,i['Cell'],419),.5)
    count = a.mix(corner_kind,
                  m('ADD',1,m('FLOOR',m('MULTIPLY',3,_rand(a,i['Cell'],501)))),
                  m('ADD',2,m('FLOOR',m('MULTIPLY',3,_rand(a,i['Cell'],405)))))
    inward,flake_depth,rings = -1e10,0.,0.
    # A shared uniform tile radius keeps neighbouring scars visible instead of
    # letting one large disc swallow the small one; every radius stays U(.25,.45).
    chip_radius=m('MULTIPLY',size,a.mad(_rand(a,i['Cell'],515),.2,.25))
    flake_bias=m('MULTIPLY',spall_size,.5)
    ripple_frequency=m('DIVIDE',math.tau*6,m('MAXIMUM',size,1e-9))
    # Centres run along a chord just outside either edge at its ends. The middle
    # scar contains the corner; adjacent scars overlap, making small cusp joins.
    for index,position in enumerate((.5,0.,1.,.25)):
        rand = lambda offset: _rand(a,i['Cell'],511+index*40+offset)
        f = a.mix(flip,position,1-position)
        cx = m('MULTIPLY',size,a.mad(f,-.5,.37))
        cy = m('MULTIPLY',size,a.mad(f,.5,-.13))
        xx,yy = m('SUBTRACT',x,cx),m('SUBTRACT',y,cy)
        radius=chip_radius
        if index<3:
            tangent,normal = _flake_frame(a,i,p,w,h,rand)
            xx,yy = a.mix(corner_kind,tangent,xx),a.mix(corner_kind,normal,yy)
            radius=a.mix(corner_kind,a.mad(rand(4),spall_size,flake_bias),chip_radius)
        radial,arc = _radial_distance(a,xx,yy,radius,i,m('MULTIPLY',97,rand(6)))
        e = a.mix(m('LESS_THAN',index,count),-1e10,m('MULTIPLY',-1,radial))
        # Each scar has concentric ripples about its own disc centre. Pick the
        # exposed scar at each point, rather than summing unrelated ripple sets.
        rho = a.length(a.xyz(xx,yy))
        wave = m('SINE',m('MULTIPLY',ripple_frequency,rho))
        rings = a.mix(m('GREATER_THAN',e,inward),rings,wave)
        inward = m('MAXIMUM',inward,e)
        if index<3:
            stack = a.mad(i['Engobe Thickness'],m('LESS_THAN',rand(8),.3),i['Glaze Thickness'])
            flake_depth = m('MAXIMUM',flake_depth,m('MULTIPLY',m('GREATER_THAN',e,0),stack))
    # Normalise between the nearest free arris and the union outline: ratio=1
    # on the arris, 0 on the outline. No depth floor beyond the glaze is added.
    arris = m('MAXIMUM',m('MINIMUM',x,y),0)
    ratio = a.clamp(m('DIVIDE',m('MAXIMUM',inward,0),m('MAXIMUM',m('ADD',inward,arris),1e-9)),0,1)
    profile = m('MULTIPLY',i['Chip Depth'],m('POWER',ratio,i['Shell Exponent']))
    ripple = m('MULTIPLY',m('MULTIPLY',.05,i['Chip Depth']),m('MULTIPLY',m('SUBTRACT',1,ratio),rings))
    depth = m('MAXIMUM',i['Glaze Thickness'],m('ADD',profile,ripple))
    return inward,a.mix(corner_kind,flake_depth,depth)


def _crack_dirt(a, i, paths):
    """Patchy, coating-only darkening along both actual fracture paths."""
    m = a.m
    value = 0.
    phase = m('MULTIPLY',37,_rand(a,i['Cell'],809))
    for distance,t,active,_ in paths:
        band = m('SUBTRACT',1,a.smooth(m('ABSOLUTE',distance),0,m('MAXIMUM',i['Dirt Width'],1e-9)))
        patches = a.smooth(a.noise(a.xyz(t,phase),1/.008,detail=0),.4,.6)
        value = m('MAXIMUM',value,m('MULTIPLY',active,m('MULTIPLY',band,patches)))
    return m('MULTIPLY',i['Crack Dirt'],m('MULTIPLY',m('GREATER_THAN',i['Dirt Width'],0),value))


def _spalls(a, i, s, t, active, size, seed, p, point_on_crack):
    """Place tile-space half-discs centred on the actual fracture in physical arc-length cells."""
    m = a.m
    pitch = m('MAXIMUM', m('MULTIPLY', 3, size), 1e-9)
    cell = m('FLOOR', m('DIVIDE', t, pitch))
    hash_cell = a.v('ADD', i['Cell'], a.xyz(0, 0, cell))
    rand = lambda offset: _rand(a, hash_cell, seed + offset)
    # Mid-cell centres keep a radius <= Spall Size inside its 3*Spall Size cell.
    center = m('MULTIPLY', m('ADD', cell, .5), pitch)
    delta = a.v('SUBTRACT', p, point_on_crack(center))
    radius = m('MULTIPLY', size, m('ADD', .3, m('MULTIPLY', .7, rand(3))))
    e = m('SUBTRACT',radius,a.length(delta))
    active = m('MULTIPLY', active, m('MULTIPLY', m('LESS_THAN', rand(5), i['Spall Density']),
               m('GREATER_THAN', m('MULTIPLY', s, a.mix(m('LESS_THAN', rand(7), .5), -1., 1.)), 0)))
    # The diameter borders the crack, not intact glaze; the coating lip follows the arc.
    e = a.mix(active, -1e10, e)
    depth = m('ADD', i['Glaze Thickness'], m('MULTIPLY', i['Engobe Thickness'], m('LESS_THAN', rand(9), .25)))
    return e, m('MULTIPLY', m('GREATER_THAN', e, 0), depth)


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
    """Build versioned fracture-network fields while preserving material users on upgrade."""
    old = bpy.data.node_groups.get(name)
    if old is not None:
        if old.bl_idname != 'ShaderNodeTree' or 'tile_damage_version' not in old:
            raise ValueError(f'Refusing to replace unrelated group {name!r}')
        if _is_current(old):
            return old
    tree = bpy.data.node_groups.new(name, 'ShaderNodeTree')
    for label in _LAYOUT_INPUTS:
        _socket(tree, label, kind='NodeSocketVector' if label in ('Cell', 'Tile UV', 'Tile Size') else 'NodeSocketFloat')
    for (key, label), default in zip(PARAMS.items(), DEFAULTS):
        socket = _socket(tree, label, default=default)
        socket.min_value = 0
        if key in ('damage', 'chip_share', 'crack_share', 'branch_share', 'spall_density', 'crack_dirt'):
            socket.max_value = 1
        elif key == 'shell_exponent':
            socket.min_value, socket.max_value = .2, 2
        elif key == 'force_kind':
            socket.max_value = 3
        elif key == 'piece_tilt':
            socket.subtype = 'ANGLE'
    _socket(tree, 'On', default=1.)
    labels = _OUTPUTS
    for label in labels:
        _socket(tree, label, 'OUTPUT')
    a = _DamageGraph(tree); m = a.m
    i = a.node('NodeGroupInput').outputs
    out = a.node('NodeGroupOutput'); out.is_active_output = True
    damaged = m('MULTIPLY', i['On'], m('LESS_THAN', _rand(a, i['Cell'], 101), i['Fraction']))
    draw = _rand(a, i['Cell'], 103)
    kind = m('SUBTRACT', 3, m('ADD', m('LESS_THAN', draw, i['Crack Share']),
                       m('LESS_THAN', draw, m('ADD', i['Crack Share'], i['Chip Share']))))
    kind = a.mix(m('GREATER_THAN', i['Force Kind'], 0), kind, i['Force Kind'])
    inside = m('MULTIPLY', damaged, m('GREATER_THAN', i['Edge'], 0))
    crack_tile = m('MULTIPLY', inside, m('COMPARE', kind, 1))
    chip_tile = m('MULTIPLY', m('MULTIPLY', inside, m('COMPARE', kind, 2)),
                  m('GREATER_THAN', i['Chip Size'], 0))
    flake_tile = m('MULTIPLY', m('MULTIPLY', inside, m('COMPARE', kind, 3)),
                   m('GREATER_THAN', i['Spall Size'], 0))
    x, y, _ = a.split(a.v('MULTIPLY', i['Tile UV'], i['Tile Size']))
    w0, h0, _ = a.split(i['Tile Size'])
    swap = m('GREATER_THAN', w0, h0)
    w, h = a.mix(swap, w0, h0), a.mix(swap, h0, w0)
    p = a.xyz(a.mix(swap, x, y), a.mix(swap, y, x))
    chip_size = m('MINIMUM', i['Chip Size'], m('MULTIPLY', .8, w))
    spall_size = m('MINIMUM', i['Spall Size'], m('MULTIPLY', .4/1.5, w))
    gap, piece, paths = _cracks(a, i, p, w, h)
    piece_height = m('MULTIPLY', crack_tile, _piece_height(a, i, p, w, h, piece))
    crack = m('MULTIPLY', crack_tile, gap)
    e_shell,d_shell = _shells(a,i,p,w,h,chip_size,spall_size,chip_tile)
    shell_tile = m('MAXIMUM',chip_tile,flake_tile)
    e_spall, d_spall = -1e10, 0.
    for index, (s, t, active, point_on_crack) in enumerate(paths):
        e, depth = _spalls(a, i, s, t, active, spall_size, 701 + index * 40, p, point_on_crack)
        e_spall = m('MAXIMUM', e_spall, e)
        d_spall = m('MAXIMUM', d_spall, depth)
    e = m('MAXIMUM',a.mix(shell_tile,-1e10,e_shell),a.mix(crack_tile,-1e10,e_spall))
    depth = m('ADD',m('MULTIPLY',shell_tile,d_shell),m('MULTIPLY',crack_tile,d_spall))
    depth, lip, engobe, body = _layers(a, i, e, depth, chip_tile, p)
    stack = m('ADD', i['Glaze Thickness'], i['Engobe Thickness'])
    crack_depth = m('MULTIPLY', crack, m('ADD', stack, i['Crack Depth']))
    values = (depth, piece_height, m('MULTIPLY', crack_tile, m('DIVIDE', piece, 4)), crack,
              crack_depth, lip, engobe, body, damaged, m('MULTIPLY', damaged, m('DIVIDE', kind, 3)),m('MULTIPLY',crack_tile,_crack_dirt(a,i,paths)))
    for label, value in zip(labels, values):
        a.put(value, out.inputs[label])
    # Fused multiply-add and common expressions may leave temporary build nodes.
    # Remove only unreachable nodes of this newly-created group.
    live = set()
    def visit(node):
        """Trace the generated output graph backwards."""
        if node in live: return
        live.add(node)
        for socket in node.inputs:
            for link in socket.links: visit(link.from_node)
    visit(out)
    for node in list(tree.nodes):
        if node not in live: tree.nodes.remove(node)
    tree['tile_damage_version'] = _VERSION
    tree['tile_damage_revision'] = 2
    if old is not None:
        _replace_group_users(old, tree)
        old.user_remap(tree); bpy.data.node_groups.remove(old); tree.name = name
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
    # Linear terracotta, 25 % toward its own luminance: measured red body read too saturated (user).
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


