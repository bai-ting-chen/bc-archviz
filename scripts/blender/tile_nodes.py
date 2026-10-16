"""Shared tile shader-node plumbing and safe versioned group retargeting."""
class _Graph:
    """Small composition helpers using the shared G node builder."""
    def __init__(self, tree):
        """Wrap the shared graph builder without clearing the tree."""
        from study_materials import G
        self.g = G(tree)
        self.count = 0

    def loc(self):
        """Allocate the next readable node position."""
        self.count += 1
        return ((self.count // 12) * 230, -(self.count % 12) * 180)

    def node(self, kind, **props):
        """Create a node using the shared public builder."""
        return self.g.n(kind, self.loc(), **props)

    def put(self, value, socket):
        """Assign literals (RGB becomes RGBA for colour sockets) or link sockets."""
        if isinstance(value, (int, float, tuple, list)):
            if isinstance(value, (tuple, list)) and len(value) == 3 and socket.type == 'RGBA':
                value = (*value, 1.0)
            socket.default_value = value
        else:
            self.g.link(value, socket)

    def m(self, op, a, b=0):
        """Create scalar math with the public shared helper."""
        return self.g.math(op, a, b, self.loc())

    def v(self, op, a, b):
        """Create vector math and select its vector or scalar output."""
        n = self.node('ShaderNodeVectorMath', operation=op)
        self.put(a, n.inputs[0]); self.put(b, n.inputs[1])
        return n.outputs['Value' if op == 'DOT_PRODUCT' else 'Vector']

    def xyz(self, x, y, z=0):
        """Combine three scalar values into a vector."""
        n = self.node('ShaderNodeCombineXYZ')
        for value, socket in zip((x, y, z), n.inputs):
            self.put(value, socket)
        return n.outputs[0]

    def split(self, vector):
        """Separate a vector into scalar components."""
        n = self.node('ShaderNodeSeparateXYZ')
        self.put(vector, n.inputs[0])
        return n.outputs

    def noise(self, vector, scale, detail=2):
        """Create native noise with a socket-driven scale."""
        result = self.g.noise(vector, 1., self.loc(), detail=detail)
        self.put(scale, result.node.inputs['Scale'])
        return result

    def amplitude(self, vector, scale, detail=2):
        """Normalize clustered noise to a clamped signed unit amplitude."""
        value = self.m('DIVIDE', self.m('SUBTRACT', self.noise(vector, scale, detail=detail), .5), .1)
        return self.m('MINIMUM', self.m('MAXIMUM', value, -1), 1)

    def rand(self, cell, offset, color=False):
        """Hash a cell with an independent seed."""
        n = self.node('ShaderNodeTexWhiteNoise', noise_dimensions='3D')
        self.put(self.v('ADD', cell, offset), n.inputs['Vector'])
        return n.outputs['Color' if color else 'Value']

    def smooth(self, value, lo, hi):
        """Clamp a smooth transition between physical bounds."""
        return self.g.range(value, lo, hi, self.loc(), smooth=True)

    def mix(self, factor, a, b):
        """Interpolate two scalar values."""
        return self.m('ADD', self.m('MULTIPLY', self.m('SUBTRACT', 1, factor), a),
                      self.m('MULTIPLY', factor, b))


def _socket(tree, name, direction='INPUT', kind='NodeSocketFloat', default=None):
    """Create an interface socket with an optional default."""
    s = tree.interface.new_socket(name, in_out=direction, socket_type=kind)
    if default is not None:
        s.default_value = default
    return s


def _replace_group_users(old, new):
    """Retarget shader group instances while preserving values and links by name."""
    import bpy

    trees = list(bpy.data.node_groups)
    for collection in (bpy.data.materials, bpy.data.worlds, bpy.data.lights):
        trees.extend(owner.node_tree for owner in collection if owner.node_tree is not None)
    seen = set()
    for tree in trees:
        if tree.as_pointer() in seen:
            continue
        seen.add(tree.as_pointer())
        users = [node for node in tree.nodes
                 if getattr(node, "node_tree", None) == old]
        if not users:
            continue
        # Snapshot the whole affected link set before changing any instance, so
        # links between two old-group instances also survive socket recreation.
        links = [(link.from_node,
                  link.from_socket.name if link.from_node in users else link.from_socket,
                  link.to_node,
                  link.to_socket.name if link.to_node in users else link.to_socket)
                 for link in tree.links
                 if link.from_node in users or link.to_node in users]
        for link in list(tree.links):
            if link.from_node in users or link.to_node in users:
                tree.links.remove(link)
        for node in users:
            values = {}
            for socket in node.inputs:
                if hasattr(socket, "default_value"):
                    value = socket.default_value
                    values[socket.name] = tuple(value) if hasattr(value, "__len__") else value
            node.node_tree = new
            for label, value in values.items():
                target = node.inputs.get(label)
                if target is not None and hasattr(target, "default_value"):
                    target.default_value = value
        for source, output, target, input_name in links:
            src = source.outputs.get(output) if source in users else output
            dst = target.inputs.get(input_name) if target in users else input_name
            if src is not None and dst is not None:
                tree.links.new(src, dst)


