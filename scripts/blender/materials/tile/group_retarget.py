"""Group retarget; canonical implementation behind tile_nodes."""

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
