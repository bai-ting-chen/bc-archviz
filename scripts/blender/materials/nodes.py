"""Nodes material helpers; canonical implementations."""
import bpy


def sock(sockets, name):
    """Active socket by name (Mix nodes keep hidden same-named sockets per data type)."""
    return next(s for s in sockets if s.name == name and s.enabled)


class G:
    """The node-graph builder for shader and Geometry Nodes trees: frames, nodes (inputs by
    keyword, or properties with n()), images on a named UV map, links, and the math / map range /
    noise / named-attribute shorthands. G(material) starts the material's tree empty; G(node_tree)
    adds to an existing tree (a GN group). materials.edge_wear._GN and the materials.edge_wear._math/_range/_noise/_attr
    functions are thin aliases of this class."""

    def __init__(self, target, clear=None):
        if isinstance(target, bpy.types.Material):
            target.use_nodes = True
            nt = target.node_tree
            clear = True if clear is None else clear
        else:
            nt = target
        if clear:
            nt.nodes.clear()
        self.nt = nt
        self.L = nt.links.new
        self.frames = {}

    def frame(self, label, color=None):
        f = self.nt.nodes.new("NodeFrame")
        f.label, f.label_size = label, 14
        if color:
            f.use_custom_color, f.color = True, color
        self.frames[label] = f
        return f

    def node(self, kind, loc, frame=None, label=None, **inputs):
        n = self.nt.nodes.new(kind)
        n.location = loc
        if label:
            n.label = label
        if frame:
            n.parent = self.frames[frame]
        for k, v in inputs.items():
            n.inputs[k].default_value = v
        return n

    def img(self, path, colorspace, loc, frame, vector, label=None):
        n = self.node("ShaderNodeTexImage", loc, frame, label)
        n.image = bpy.data.images.load(path, check_existing=True)
        n.image.colorspace_settings.name = colorspace
        n.extension = "REPEAT"
        self.link(vector, n.inputs["Vector"])
        return n

    def uv(self, name, loc, frame):
        n = self.node("ShaderNodeUVMap", loc, frame, label="UV: " + name)
        n.uv_map = name
        return n.outputs["UV"]

    def link(self, a, b):
        self.nt.links.new(a, b)

    def n(self, kind, loc, **props):
        """Node with properties (operation, data_type, domain...) set by keyword."""
        node = self.nt.nodes.new(kind)
        node.location = loc
        for k, v in props.items():
            setattr(node, k, v)
        return node

    def _in(self, sockt, v):
        if isinstance(v, (int, float, tuple, list)):
            sockt.default_value = v
        else:
            self.L(v, sockt)

    def math(self, op, a, b, loc, frame=None, clamp=False):
        node = self.node("ShaderNodeMath", loc, frame)
        node.operation, node.use_clamp = op, clamp
        for i, v in enumerate((a, b)):
            self._in(node.inputs[i], v)
        return node.outputs[0]

    def range(self, v, fmin, fmax, loc, tmin=0.0, tmax=1.0, frame=None, label=None, smooth=False):
        node = self.node("ShaderNodeMapRange", loc, frame, label)
        if smooth:
            node.interpolation_type = "SMOOTHSTEP"
        for k, x in (("From Min", fmin), ("From Max", fmax), ("To Min", tmin), ("To Max", tmax)):
            self._in(node.inputs[k], x)
        self.L(v, node.inputs["Value"])
        return node.outputs["Result"]

    def noise(self, vec, scale, loc, frame=None, detail=6.0, rough=0.6, label=None):
        node = self.node("ShaderNodeTexNoise", loc, frame, label, Scale=scale, Detail=detail, Roughness=rough)
        self.L(vec, node.inputs["Vector"])
        return node.outputs[0]

    def attr(self, name, loc, frame=None, out="Fac"):
        node = self.node("ShaderNodeAttribute", loc, frame, label="attr: " + name)
        node.attribute_name = name
        return node.outputs[out]

    def store(self, geo, name, dtype, val, loc):
        st = self.n("GeometryNodeStoreNamedAttribute", loc, data_type=dtype, domain="POINT")
        st.inputs["Name"].default_value = name
        self.L(geo, st.inputs["Geometry"])
        self.L(val, sock(st.inputs, "Value"))
        return st.outputs["Geometry"]

    def named(self, name, dtype, loc):
        node = self.n("GeometryNodeInputNamedAttribute", loc, data_type=dtype)
        node.inputs["Name"].default_value = name
        return node.outputs[0]
