"""Layout instance; canonical implementation behind tile_layout."""

from materials.tile.layout_build import layout_group

from materials.tile.layout_config import _INPUTS

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
