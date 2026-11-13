"""Tile graph; canonical implementation behind tile_nodes."""

class _TileGraph:
    """Small composition helpers using the shared NodeGraph builder."""
    def __init__(self, tree):
        """Wrap the shared graph builder without clearing the tree."""
        from materials.shared.node_graph import NodeGraph
        self.g = NodeGraph(tree)
        self.count = 0

    def next_location(self):
        """Allocate the next readable node position."""
        self.count += 1
        return ((self.count // 12) * 230, -(self.count % 12) * 180)

    def node(self, kind, **props):
        """Create a node using the shared public builder."""
        return self.g.node_with_props(kind, self.next_location(), **props)

    def link_or_set(self, value, socket):
        """Assign literals (RGB becomes RGBA for colour sockets) or link sockets."""
        if isinstance(value, (int, float, tuple, list)):
            if isinstance(value, (tuple, list)) and len(value) == 3 and socket.type == 'RGBA':
                value = (*value, 1.0)
            socket.default_value = value
        else:
            self.g.link(value, socket)

    def math(self, op, a, b=0):
        """Create scalar math with the public shared helper."""
        return self.g.math(op, a, b, self.next_location())

    def vector_math(self, op, a, b):
        """Create vector math and select its vector or scalar output."""
        n = self.node('ShaderNodeVectorMath', operation=op)
        self.link_or_set(a, n.inputs[0]); self.link_or_set(b, n.inputs[1])
        return n.outputs['Value' if op == 'DOT_PRODUCT' else 'Vector']

    def combine_xyz(self, x, y, z=0):
        """Combine three scalar values into a vector."""
        n = self.node('ShaderNodeCombineXYZ')
        for value, socket in zip((x, y, z), n.inputs):
            self.link_or_set(value, socket)
        return n.outputs[0]

    def separate_xyz(self, vector):
        """Separate a vector into scalar components."""
        n = self.node('ShaderNodeSeparateXYZ')
        self.link_or_set(vector, n.inputs[0])
        return n.outputs

    def noise_texture(self, vector, scale, detail=2):
        """Create native noise with a socket-driven scale."""
        result = self.g.noise_texture(vector, 1., self.next_location(), detail=detail)
        self.link_or_set(scale, result.node.inputs['Scale'])
        return result

    def amplitude(self, vector, scale, detail=2):
        """Normalize clustered noise to a clamped signed unit amplitude."""
        value = self.math('DIVIDE', self.math('SUBTRACT', self.noise_texture(vector, scale, detail=detail), .5), .1)
        return self.math('MINIMUM', self.math('MAXIMUM', value, -1), 1)

    def hash_noise(self, cell, offset, color=False):
        """Hash a cell with an independent seed."""
        n = self.node('ShaderNodeTexWhiteNoise', noise_dimensions='3D')
        self.link_or_set(self.vector_math('ADD', cell, offset), n.inputs['Vector'])
        return n.outputs['Color' if color else 'Value']

    def smooth(self, value, lo, hi):
        """Clamp a smooth transition between physical bounds."""
        return self.g.map_range(value, lo, hi, self.next_location(), smooth=True)

    def mix(self, factor, a, b):
        """Interpolate two scalar values."""
        return self.math('ADD', self.math('MULTIPLY', self.math('SUBTRACT', 1, factor), a),
                      self.math('MULTIPLY', factor, b))

def _socket(tree, name, direction='INPUT', kind='NodeSocketFloat', default=None):
    """Create an interface socket with an optional default."""
    s = tree.interface.new_socket(name, in_out=direction, socket_type=kind)
    if default is not None:
        s.default_value = default
    return s
