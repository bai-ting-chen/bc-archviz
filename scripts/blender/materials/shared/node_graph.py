"""NodeGraph: the builder for shader and Geometry Nodes trees, and the wear-layer frame and switch."""
import bpy


def active_socket(sockets, name):
    """Active socket by name (Mix nodes keep hidden same-named sockets per data type)."""
    return next(s for s in sockets if s.name == name and s.enabled)


class NodeGraph:
    """Builds a shader or Geometry Nodes tree: frames, nodes (inputs by keyword, or properties with
    node_with_props), image textures on a named UV map, links, and shorthands for math, map range,
    mix, vector math, colour ramp, noise and named attributes. NodeGraph(material) starts the
    material's tree empty; NodeGraph(node_tree) adds to an existing tree (a GN group)."""

    def __init__(self, target, clear=None):
        if isinstance(target, bpy.types.Material):
            target.use_nodes = True
            tree = target.node_tree
            clear = True if clear is None else clear
        else:
            tree = target
        if clear:
            tree.nodes.clear()
        self.tree = tree
        self.frames = {}

    def frame(self, label, color=None):
        """Labelled frame node, remembered by label for node(..., frame=label)."""
        frame = self.tree.nodes.new("NodeFrame")
        frame.label, frame.label_size = label, 14
        if color:
            frame.use_custom_color, frame.color = True, color
        self.frames[label] = frame
        return frame

    def node(self, kind, loc, frame=None, label=None, **inputs):
        """Node of type kind at loc, inside a frame, with input default values by keyword."""
        node = self.tree.nodes.new(kind)
        node.location = loc
        if label:
            node.label = label
        if frame:
            node.parent = self.frames[frame]
        for name, value in inputs.items():
            node.inputs[name].default_value = value
        return node

    def node_with_props(self, kind, loc, **props):
        """Node with properties (operation, data_type, domain...) set by keyword."""
        node = self.tree.nodes.new(kind)
        node.location = loc
        for name, value in props.items():
            setattr(node, name, value)
        return node

    def image_texture(self, path, colorspace, loc, frame, vector, label=None):
        """Image Texture node loading path, repeated, driven by the vector socket."""
        node = self.node("ShaderNodeTexImage", loc, frame, label)
        node.image = bpy.data.images.load(path, check_existing=True)
        node.image.colorspace_settings.name = colorspace
        node.extension = "REPEAT"
        self.link(vector, node.inputs["Vector"])
        return node

    def uv_map(self, name, loc, frame):
        """UV Map node for the named UV layer; returns its UV socket."""
        node = self.node("ShaderNodeUVMap", loc, frame, label="UV: " + name)
        node.uv_map = name
        return node.outputs["UV"]

    def link(self, from_socket, to_socket):
        """Link two sockets; returns the link."""
        return self.tree.links.new(from_socket, to_socket)

    def link_or_set(self, socket, value):
        """Link value into socket when it is a socket; otherwise set the socket's default value."""
        if isinstance(value, (int, float, tuple, list)):
            socket.default_value = value
        else:
            self.link(value, socket)

    def math(self, op, a, b, loc, frame=None, clamp=False):
        """Math node (op on a and b, sockets or values); returns its Value."""
        node = self.node("ShaderNodeMath", loc, frame)
        node.operation, node.use_clamp = op, clamp
        for i, value in enumerate((a, b)):
            self.link_or_set(node.inputs[i], value)
        return node.outputs[0]

    def map_range(self, value, fmin, fmax, loc, tmin=0.0, tmax=1.0, frame=None, label=None, smooth=False):
        """Map Range from [fmin, fmax] to [tmin, tmax], smoothstep when smooth; returns Result."""
        node = self.node("ShaderNodeMapRange", loc, frame, label)
        if smooth:
            node.interpolation_type = "SMOOTHSTEP"
        for name, bound in (("From Min", fmin), ("From Max", fmax), ("To Min", tmin), ("To Max", tmax)):
            self.link_or_set(node.inputs[name], bound)
        self.link(value, node.inputs["Value"])
        return node.outputs["Result"]

    def noise_texture(self, vector, scale, loc, frame=None, detail=6.0, rough=0.6, label=None):
        """Noise Texture on a vector socket; returns its Fac."""
        node = self.node("ShaderNodeTexNoise", loc, frame, label, Scale=scale, Detail=detail, Roughness=rough)
        self.link(vector, node.inputs["Vector"])
        return node.outputs[0]

    def mix(self, a, b, factor, loc, frame=None, data_type="RGBA", blend="MIX", label=None):
        """Mix node (data_type RGBA, FLOAT or VECTOR) from sockets or values; returns Result."""
        node = self.node("ShaderNodeMix", loc, frame, label)
        node.data_type, node.blend_type = data_type, blend
        self.link_or_set(node.inputs["Factor"], factor)
        self.link_or_set(active_socket(node.inputs, "A"), a)
        self.link_or_set(active_socket(node.inputs, "B"), b)
        return active_socket(node.outputs, "Result")

    def vector_math(self, op, a, b, loc, frame=None, label=None):
        """Vector Math from sockets or values (b None: unary); returns the Value output for
        DOT_PRODUCT / LENGTH / DISTANCE, otherwise the Vector."""
        node = self.node("ShaderNodeVectorMath", loc, frame, label)
        node.operation = op
        self.link_or_set(node.inputs[0], a)
        if b is not None:
            self.link_or_set(node.inputs["Scale"] if op == "SCALE" else node.inputs[1], b)
        return node.outputs["Value" if op in ("DOT_PRODUCT", "LENGTH", "DISTANCE") else "Vector"]

    def color_ramp(self, loc, frame, stops, label=None, interp="LINEAR"):
        """Color Ramp with stops [(position, (r, g, b)), ...]; returns the node."""
        node = self.node("ShaderNodeValToRGB", loc, frame, label)
        ramp = node.color_ramp
        ramp.interpolation = interp
        while len(ramp.elements) > 1:
            ramp.elements.remove(ramp.elements[-1])
        ramp.elements[0].position, ramp.elements[0].color = stops[0][0], (*stops[0][1], 1)
        for position, color in stops[1:]:
            ramp.elements.new(position).color = (*color, 1)
        return node

    def combine_xyz(self, x, y, z, loc, frame=None):
        """Combine XYZ from sockets or numbers; returns the vector socket."""
        node = self.node("ShaderNodeCombineXYZ", loc, frame)
        for i, value in enumerate((x, y, z)):
            self.link_or_set(node.inputs[i], value)
        return node.outputs[0]

    def attribute(self, name, loc, frame=None, out="Fac"):
        """Shader Attribute node reading a named attribute; returns the out socket."""
        node = self.node("ShaderNodeAttribute", loc, frame, label="attr: " + name)
        node.attribute_name = name
        return node.outputs[out]

    def store_attribute(self, geometry, name, dtype, value, loc):
        """Geometry Nodes Store Named Attribute on points; returns the geometry socket."""
        node = self.node_with_props("GeometryNodeStoreNamedAttribute", loc, data_type=dtype, domain="POINT")
        node.inputs["Name"].default_value = name
        self.link(geometry, node.inputs["Geometry"])
        self.link(value, active_socket(node.inputs, "Value"))
        return node.outputs["Geometry"]

    def named_attribute(self, name, dtype, loc):
        """Geometry Nodes Named Attribute input; returns its value socket."""
        node = self.node_with_props("GeometryNodeInputNamedAttribute", loc, data_type=dtype)
        node.inputs["Name"].default_value = name
        return node.outputs[0]


def frame_for(mat, label):
    """The material's node builder with one labelled frame for a wear layer; returns (builder, label)."""
    graph = NodeGraph(mat.node_tree)
    graph.frame(label, (0.18, 0.26, 0.30))
    return graph, label


def layer_frame(g, label):
    """Create a stacked layer frame and return its label for the graph builder."""
    node = g.frame(label)
    node.location.y = -12000 * (sum(n.type == 'FRAME' for n in g.tree.nodes)-1)
    return label


def layer_switch(g, layer, value, amount, neutral=1.0, frame=None):
    """Switch a scalar or vector layer and export its AOV."""
    x, y = value.node.location
    # Keep each control beside its own input chain, followed by Mix and AOV.
    used = {(tuple(node.location)) for node in g.tree.nodes
            if node.parent == (g.frames[frame] if frame else None)}
    while any((x+dx, y+dy) in used for dx, dy in ((300, 200), (600, 0), (900, 0))):
        y -= 700
    if isinstance(amount, (int, float)):
        node = g.node('ShaderNodeValue', (x + 300, y + 200), frame, label=layer + ' amount')
        node.outputs[0].default_value = amount
        amount = node.outputs[0]
    mix = g.node('ShaderNodeMix', (x + 600, y), frame, label=layer)
    mix.data_type = 'VECTOR' if value.type == 'VECTOR' else 'FLOAT'
    g.link(amount, mix.inputs[0])
    g.link_or_set(active_socket(mix.inputs, 'A'), neutral)
    g.link(value, active_socket(mix.inputs, 'B'))
    result = active_socket(mix.outputs, 'Result')
    aov = g.node('ShaderNodeOutputAOV', (x + 900, y), frame)
    aov.aov_name = aov.name = 'var_' + layer
    g.link(result, aov.inputs['Color' if value.type == 'VECTOR' else 'Value'])
    return result
