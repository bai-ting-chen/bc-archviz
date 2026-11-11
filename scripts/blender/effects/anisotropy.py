"""Directional microfacet roughness shared by reflective and transmissive materials."""


TANGENT_NODE = 'anisotropy tangent'


def anisotropy(bsdf, amount=0.0, rotation=None, tangent=None):
    """Set directional roughness; rotation in turns, tangent a world vector or UV-map name; None keeps either as it is."""
    # BSDF socket names differ between Glass and Principled.
    amount_input = bsdf.inputs.get('Anisotropic') or bsdf.inputs.get('Anisotropy')
    rotation_input = bsdf.inputs.get('Anisotropic Rotation') or bsdf.inputs.get('Rotation')
    amount_input.default_value = amount
    if rotation is not None:
        rotation_input.default_value = rotation
    tangent_input = bsdf.inputs['Tangent']
    if tangent is None:
        if tangent_input.is_linked:
            return
        tangent = (1.0, 0.0, 0.0)
    tree = bsdf.id_data
    for link in list(tangent_input.links):
        source = link.from_node
        tree.links.remove(link)
        # Only the node this helper made before is replaced; a user's tangent node stays in the tree.
        if source.label == TANGENT_NODE and not any(o.links for o in source.outputs):
            tree.nodes.remove(source)
    if isinstance(tangent, str):
        node = tree.nodes.new('ShaderNodeTangent')
        node.direction_type = 'UV_MAP'
        node.uv_map = tangent
    else:
        # Cycles uses a fallback tangent for an unlinked input, even with a vector default.
        node = tree.nodes.new('ShaderNodeCombineXYZ')
        for socket, value in zip(node.inputs, tangent):
            socket.default_value = value
    node.label = TANGENT_NODE
    node.location = (bsdf.location.x - 220, bsdf.location.y - 240)
    tree.links.new(node.outputs[0], tangent_input)
