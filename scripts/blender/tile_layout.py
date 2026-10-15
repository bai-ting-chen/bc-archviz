"""Metre-based tile layout shader maths; see references/materials.md > Tiles."""
import numpy as np

_VERSION = 3
_INPUTS = {
    "tile_w": "Tile W", "tile_h": "Tile H", "joint": "Joint", "corner_radius": "Corner Radius",
    "row_offset": "Row Offset", "rotation": "Rotation", "origin": "Origin",
}


def reference(u, v, tile_w, tile_h, joint, row_offset=0.0, rotation=0.0,
              origin=(0.0, 0.0), corner_radius=0.0):
    """Return layout truth in metres; row_offset accepts any real value and wraps."""
    u, v = np.broadcast_arrays(np.asarray(u, dtype=float), np.asarray(v, dtype=float))
    x, y = u - origin[0], v - origin[1]
    c, s = np.cos(rotation), np.sin(rotation)
    qx, qy = c * x + s * y, -s * x + c * y
    pw, ph = tile_w + joint, tile_h + joint
    row = np.floor(qy / ph)
    offset = row * row_offset
    xp = qx - (offset - np.floor(offset)) * pw
    col = np.floor(xp / pw)
    tx, ty = xp - col * pw - joint / 2, qy - row * ph - joint / 2
    rc = np.clip(corner_radius, 0, min(tile_w, tile_h) / 2)
    dx = np.abs(tx - tile_w / 2) - (tile_w / 2 - rc)
    dy = np.abs(ty - tile_h / 2) - (tile_h / 2 - rc)
    edge = -(np.hypot(np.maximum(dx, 0), np.maximum(dy, 0))
             + np.minimum(np.maximum(dx, dy), 0) - rc)
    return dict(tile_uv_x=np.clip(tx / tile_w, 0, 1),
                tile_uv_y=np.clip(ty / tile_h, 0, 1), edge=edge,
                joint=(edge < -1e-7).astype(float), col=col, row=row)


def _interface_signature(group):
    """Read ordered socket names, directions and types without instance identifiers."""
    return [(item.name, item.in_out, item.socket_type)
            for item in group.interface.items_tree if item.item_type == "SOCKET"]


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


def layout_group(name="TileLayout"):
    """Create the metre-based shader layout group or reuse its matching version."""
    import bpy
    from study_materials import G

    old = bpy.data.node_groups.get(name)
    if old is not None:
        if "tile_layout_version" not in old:
            raise ValueError(f"{name!r} has no tile_layout_version; refusing to overwrite it")
        if old.bl_idname != "ShaderNodeTree":
            raise TypeError(f"{name!r} is not a shader node tree")
        if old.get("tile_layout_version") == _VERSION:
            return old
    ng = bpy.data.node_groups.new(name, "ShaderNodeTree")

    def socket(label, direction, kind="NodeSocketFloat", default=None,
               minimum=None, maximum=None):
        item = ng.interface.new_socket(label, in_out=direction, socket_type=kind)
        if default is not None:
            item.default_value = default
        if minimum is not None:
            item.min_value = minimum
        if maximum is not None:
            item.max_value = maximum
        return item

    socket("Vector", "INPUT", "NodeSocketVector", (0, 0, 0))
    socket("Tile W", "INPUT", default=0.1, minimum=1e-6)
    socket("Tile H", "INPUT", default=0.1, minimum=1e-6)
    socket("Joint", "INPUT", default=0.003, minimum=0)
    socket("Corner Radius", "INPUT", default=0, minimum=0)
    offset_socket = socket("Row Offset", "INPUT", default=0)
    offset_socket.description = "Any real value wraps; usual range 0 to 1"
    # Bundled 5.2 RNA documents no soft bounds on interface float sockets.
    if hasattr(offset_socket, "soft_min") and hasattr(offset_socket, "soft_max"):
        offset_socket.soft_min, offset_socket.soft_max = 0, 1
    socket("Rotation", "INPUT", default=0).subtype = "ANGLE"
    socket("Origin", "INPUT", "NodeSocketVector", (0, 0, 0))
    socket("Tile ID", "OUTPUT", minimum=0, maximum=1)
    socket("Tile UV", "OUTPUT", "NodeSocketVector")
    socket("Edge", "OUTPUT")
    socket("Joint", "OUTPUT", minimum=0, maximum=1)
    socket("Cell", "OUTPUT", "NodeSocketVector")
    socket("Tile Size", "OUTPUT", "NodeSocketVector")
    socket("Joint Width", "OUTPUT")

    if old is not None and _interface_signature(old) == _interface_signature(ng):
        bpy.data.node_groups.remove(ng)
        ng = old
        ng.nodes.clear()  # Preserve socket identifiers, instance values and links.
        for item in ng.interface.items_tree:
            if item.item_type == "SOCKET" and item.in_out == "INPUT" and item.name == "Row Offset":
                item.min_value, item.max_value = -3.402823466e38, 3.402823466e38
                item.description = "Any real value wraps; usual range 0 to 1"
                if hasattr(item, "soft_min") and hasattr(item, "soft_max"):
                    item.soft_min, item.soft_max = 0, 1

    g = G(ng)
    ins = g.node("NodeGroupInput", (-1600, 300)).outputs
    out = g.node("NodeGroupOutput", (1800, 300))
    out.is_active_output = True
    index = 0

    def math(op, a, b=0.0, clamp=False):
        nonlocal index
        index += 1
        return g.math(op, a, b, (-1100 + (index // 7) * 220,
                               700 - (index % 7) * 180), clamp=clamp)

    def separate(vector, loc):
        node = g.node("ShaderNodeSeparateXYZ", loc)
        g.link(vector, node.inputs[0])
        return node.outputs

    def combine(x, y, loc):
        node = g.node("ShaderNodeCombineXYZ", loc)
        g.link(x, node.inputs["X"])
        g.link(y, node.inputs["Y"])
        node.inputs["Z"].default_value = 0
        return node.outputs[0]

    p = separate(ins["Vector"], (-1450, 500))
    origin = separate(ins["Origin"], (-1450, -200))
    x, y = math("SUBTRACT", p[0], origin[0]), math("SUBTRACT", p[1], origin[1])
    c, s = math("COSINE", ins["Rotation"]), math("SINE", ins["Rotation"])
    qx = math("ADD", math("MULTIPLY", c, x), math("MULTIPLY", s, y))
    qy = math("SUBTRACT", math("MULTIPLY", c, y), math("MULTIPLY", s, x))
    pw = math("ADD", ins["Tile W"], ins["Joint"])
    ph = math("ADD", ins["Tile H"], ins["Joint"])
    row = math("FLOOR", math("DIVIDE", qy, ph))
    # FRACT = x-floor(x), including for negative rows.
    shift = math("FRACT", math("MULTIPLY", row, ins["Row Offset"]))
    xp = math("SUBTRACT", qx, math("MULTIPLY", shift, pw))
    col = math("FLOOR", math("DIVIDE", xp, pw))
    half_joint = math("MULTIPLY", ins["Joint"], 0.5)
    tx = math("SUBTRACT", math("SUBTRACT", xp, math("MULTIPLY", col, pw)), half_joint)
    ty = math("SUBTRACT", math("SUBTRACT", qy, math("MULTIPLY", row, ph)), half_joint)
    hx, hy = math("MULTIPLY", ins["Tile W"], 0.5), math("MULTIPLY", ins["Tile H"], 0.5)
    rc = math("MINIMUM", math("MAXIMUM", ins["Corner Radius"], 0), math("MINIMUM", hx, hy))
    dx = math("SUBTRACT", math("ABSOLUTE", math("SUBTRACT", tx, hx)), math("SUBTRACT", hx, rc))
    dy = math("SUBTRACT", math("ABSOLUTE", math("SUBTRACT", ty, hy)), math("SUBTRACT", hy, rc))
    positive = combine(math("MAXIMUM", dx, 0), math("MAXIMUM", dy, 0), (900, -800))
    length = g.n("ShaderNodeVectorMath", (1100, -800), operation="LENGTH")
    g.link(positive, length.inputs[0])
    inside = math("MINIMUM", math("MAXIMUM", dx, dy), 0)
    edge = math("SUBTRACT", rc, math("ADD", length.outputs["Value"], inside))
    joint = math("LESS_THAN", edge, -1e-7)
    uv = combine(math("DIVIDE", tx, ins["Tile W"], clamp=True),
                 math("DIVIDE", ty, ins["Tile H"], clamp=True), (1400, 500))
    cell = combine(col, row, (1050, -500))
    tile_size = combine(ins["Tile W"], ins["Tile H"], (1400, 800))
    seed = g.n("ShaderNodeVectorMath", (1250, -500), operation="ADD")
    g.link(cell, seed.inputs[0])
    seed.inputs[1].default_value = (0.5, 0.5, 0.5)
    noise = g.n("ShaderNodeTexWhiteNoise", (1450, -500), noise_dimensions="3D")
    g.link(seed.outputs["Vector"], noise.inputs["Vector"])
    for label, value in (("Tile ID", noise.outputs["Value"]), ("Tile UV", uv),
                         ("Edge", edge), ("Joint", joint), ("Cell", cell),
                         ("Tile Size", tile_size), ("Joint Width", ins["Joint"])):
        g.link(value, out.inputs[label])
    ng["tile_layout_version"] = _VERSION
    if old is not None and old != ng:
        _replace_group_users(old, ng)
        old.user_remap(ng)
        bpy.data.node_groups.remove(old)
        ng.name = name
    return ng


def add_layout(node_tree, vector_socket, loc=(0, 0), **inputs):
    """Add a metre/radian layout group; row_offset accepts any real value and wraps."""
    unknown = inputs.keys() - _INPUTS.keys()
    if unknown:
        raise TypeError(f"Unknown tile layout inputs: {', '.join(sorted(unknown))}")
    node = node_tree.nodes.new("ShaderNodeGroup")
    node.node_tree = layout_group()
    node.location = loc
    for key, value in inputs.items():
        if key == "origin":
            value = tuple(value)
            if len(value) == 2:
                value = (*value, 0.0)
        node.inputs[_INPUTS[key]].default_value = value
    node_tree.links.new(vector_socket, node.inputs["Vector"])
    return node
