"""Tile uv node; canonical implementation behind tile_mapping."""

def layout_vector(node_tree, name="TileUV", loc=(0, 0), obj=None):
    """Add a named UV Map node and return its layout vector output socket."""
    if obj is not None and (obj.type != 'MESH' or obj.data.uv_layers.get(name) is None):
        raise ValueError(f"Object {obj.name!r} has no UV layer {name!r}")
    node = node_tree.nodes.new("ShaderNodeUVMap")
    node.uv_map = name
    node.location = loc
    return node.outputs["UV"]
