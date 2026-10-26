"""Damage graph; canonical implementation behind tile_damage."""

from materials.tile.tile_graph import _Graph

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
